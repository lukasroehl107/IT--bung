import requests
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")
st.title("SMARD Lastprofil Explorer")

FILTER = "410"
REGION = "DE"

WEEKDAY_LABELS = {
    1: "Montag",
    2: "Dienstag",
    3: "Mittwoch",
    4: "Donnerstag",
    5: "Freitag",
    6: "Samstag",
    7: "Sonntag",
}

WEEKDAY_ORDER = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

# SMARD liefert die stündlichen Daten in Wochen-Paketen ("Chunks").
# Hier werden die letzten N Wochen geladen – das reicht für alle Ansichten
# und hält die Ladezeit kurz. Bei Bedarf erhöhen (mehr Historie, langsamer).
ANZAHL_WOCHEN = 20


@st.cache_data
def load_smard_hourly_data():
    index_url = (
        f"https://www.smard.de/app/chart_data/"
        f"{FILTER}/{REGION}/index_hour.json"
    )

    response = requests.get(index_url, timeout=10)
    response.raise_for_status()
    timestamps = response.json().get("timestamps", [])

    all_data = []
    for ts in timestamps[-ANZAHL_WOCHEN:]:
        data_url = (
            f"https://www.smard.de/app/chart_data/"
            f"{FILTER}/{REGION}/"
            f"{FILTER}_{REGION}_hour_{ts}.json"
        )
        chunk = requests.get(data_url, timeout=10)
        chunk.raise_for_status()
        series = chunk.json().get("series", [])
        for row in series:
            if row[1] is not None:
                all_data.append(row)

    df = pd.DataFrame(all_data, columns=["timestamp", "load"])
    if df.empty:
        return df

    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_convert("Europe/Berlin")
    df["date"] = df["datetime"].dt.date
    df["hour"] = df["datetime"].dt.hour
    df["weekday"] = df["datetime"].dt.isocalendar().day  # 1 = Montag ... 7 = Sonntag (passt zu WEEKDAY_LABELS)
    df["weekday_label"] = df["weekday"].map(WEEKDAY_LABELS)
    df["iso_year"] = df["datetime"].dt.isocalendar().year
    df["iso_week"] = df["datetime"].dt.isocalendar().week
    df["week_label"] = df.apply(lambda row: f"{row.iso_year}-KW{row.iso_week:02d}", axis=1)
    return df


def available_weeks(df: pd.DataFrame) -> list[str]:
    unique_weeks = df["week_label"].unique().tolist()
    return sorted(unique_weeks, key=lambda label: (int(label.split("-KW")[0]), int(label.split("-KW")[1])))


def available_dates(df: pd.DataFrame) -> list[str]:
    unique_dates = df["date"].astype(str).unique().tolist()
    return sorted(unique_dates)


def render_time_series(df: pd.DataFrame, start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    title = "Lastprofil: Netzlast"
    if start_date is not None and end_date is not None:
        title = f"Lastprofil: {start_date} bis {end_date}"

    st.header(title)
    if df.empty:
        st.warning("Keine Daten verfügbar.")
        return

    fig = px.line(
        df,
        x="datetime",
        y="load",
        title=title,
        labels={"datetime": "Zeit", "load": "Netzlast (MWh)"},
    )
    fig.update_layout(xaxis_title="Datum", yaxis_title="Last (MWh)")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Max Last", f"{df['load'].max():,.0f} MWh")
    col2.metric("Min Last", f"{df['load'].min():,.0f} MWh")
    col3.metric("Durchschnitt", f"{df['load'].mean():,.0f} MWh")


def render_weekly_overlay(df: pd.DataFrame, selected_weeks: list[str]):
    st.header("Wochenvergleich: überlagerte Wochentage")
    if df.empty or not selected_weeks:
        st.warning("Bitte wählen Sie mindestens eine Kalenderwoche aus.")
        return

    filtered = df[df["week_label"].isin(selected_weeks)].copy()
    if filtered.empty:
        st.warning("Für die ausgewählten Kalenderwochen gibt es keine Daten.")
        return

    summary = (
        filtered
        .groupby(["week_label", "weekday", "weekday_label", "hour"], as_index=False)["load"]
        .mean()
        .sort_values(["week_label", "weekday", "hour"])
    )

    summary["weekday_label"] = pd.Categorical(
        summary["weekday_label"],
        categories=WEEKDAY_ORDER,
        ordered=True,
    )

    fig = px.line(
        summary,
        x="hour",
        y="load",
        color="weekday_label",
        line_dash="week_label",
        title="Stündliche Lastprofile pro Wochentag und Kalenderwoche",
        labels={
            "hour": "Stunde des Tages",
            "load": "Netzlast (MWh)",
            "weekday_label": "Wochentag",
            "week_label": "Kalenderwoche",
        },
        hover_data={"week_label": True, "weekday_label": True, "hour": True, "load": ":.1f"},
    )

    fig.update_layout(
        xaxis=dict(tickmode="array", tickvals=list(range(0, 24)), ticktext=[str(h) for h in range(0, 24)]),
        yaxis=dict(title="Netzlast (MWh)", rangemode="tozero"),
        legend_title_text="Wochentag / Woche",
        margin=dict(l=50, r=280, t=90, b=50),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_day_compare(df: pd.DataFrame, selected_dates: list[str]):
    st.header("Tagesvergleich: bis zu 7 Tage")
    if df.empty or not selected_dates:
        st.warning("Bitte wählen Sie mindestens einen Tag aus.")
        return

    if len(selected_dates) > 7:
        st.warning("Bitte wählen Sie maximal 7 Tage aus.")
        return

    selected = df[df["date"].astype(str).isin(selected_dates)].copy()
    if selected.empty:
        st.warning("Für die ausgewählten Tage gibt es keine Daten.")
        return

    summary = (
        selected
        .groupby(["date", "hour"], as_index=False)["load"]
        .mean()
        .sort_values(["date", "hour"])
    )

    fig = px.line(
        summary,
        x="hour",
        y="load",
        color="date",
        title="Stündliche Lastprofile der ausgewählten Tage",
        labels={"hour": "Stunde des Tages", "load": "Netzlast (MWh)", "date": "Datum"},
        hover_data={"date": True, "hour": True, "load": ":.1f"},
    )

    fig.update_layout(
        xaxis=dict(tickmode="array", tickvals=list(range(0, 24)), ticktext=[str(h) for h in range(0, 24)]),
        yaxis=dict(title="Netzlast (MWh)", rangemode="tozero"),
        legend_title_text="Datum",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Tagesvergleich Detail")
    st.data_editor(summary.head(14), disabled=True)


def render_box_distribution(
    df: pd.DataFrame,
    group_by: str,
    selected_dates: list[str] | None = None,
    selected_weeks: list[str] | None = None,
):
    """Boxplot der Lastverteilung – entweder je Stunde (über ausgewählte Tage)
    oder je Wochentag (über einen ausgewählten Zeitraum).
    Hover aktiv, Zahlen auf ganze MW gerundet."""
    st.header("Boxplot: Lastverteilung")
    if df.empty:
        st.warning("Keine Daten verfügbar.")
        return

    FARBE_WERKTAG = "#4C9BE8"
    FARBE_WOCHENENDE = "#F4924A"

    if group_by == "Stunde des Tages":
        if not selected_dates:
            st.warning("Bitte wählen Sie mindestens einen Tag aus.")
            return
        if len(selected_dates) > 7:
            st.warning("Bitte wählen Sie maximal 7 Tage aus.")
            return

        subset = df[df["date"].astype(str).isin(selected_dates)].copy()
        if subset.empty:
            st.warning("Für die ausgewählten Tage gibt es keine Daten.")
            return

        # Stunden-Boxplot: einheitlich blau
        fig = px.box(
            subset,
            x="hour",
            y="load",
            points="outliers",
            title="Lastverteilung je Stunde über die ausgewählten Tage",
            labels={"hour": "Stunde des Tages", "load": "Netzlast (MWh)"},
        )
        fig.update_traces(
            marker_color=FARBE_WERKTAG,
            line_color=FARBE_WERKTAG,
            fillcolor=FARBE_WERKTAG,
            opacity=0.75,
        )
        fig.update_layout(
            xaxis=dict(
                tickmode="array",
                tickvals=list(range(0, 24)),
                ticktext=[str(h) for h in range(0, 24)],
                title="Stunde des Tages",
            ),
            yaxis=dict(title="Netzlast (MWh)", rangemode="tozero", hoverformat=",.0f"),
        )
        st.plotly_chart(fig, use_container_width=True)

    else:  # Wochentag
        if not selected_weeks:
            st.warning("Bitte wählen Sie mindestens eine Kalenderwoche aus.")
            return

        subset = df[df["week_label"].isin(selected_weeks)].copy()
        if subset.empty:
            st.warning("Für die ausgewählten Kalenderwochen gibt es keine Daten.")
            return

        subset["weekday_label"] = pd.Categorical(subset["weekday_label"], categories=WEEKDAY_ORDER, ordered=True)
        subset = subset.sort_values("weekday")

        # Wochentag-Boxplot: Wochenende farblich abgesetzt
        WOCHENENDE = {"Samstag", "Sonntag"}
        farben = [
            FARBE_WOCHENENDE if tag in WOCHENENDE else FARBE_WERKTAG
            for tag in WEEKDAY_ORDER
        ]

        fig = px.box(
            subset,
            x="weekday_label",
            y="load",
            points="outliers",
            title="Lastverteilung je Wochentag über den ausgewählten Zeitraum",
            labels={"weekday_label": "Wochentag", "load": "Netzlast (MWh)"},
            color="weekday_label",
            color_discrete_sequence=farben,
            category_orders={"weekday_label": WEEKDAY_ORDER},
        )
        fig.update_traces(opacity=0.80)
        fig.update_layout(
            xaxis=dict(title="Wochentag"),
            yaxis=dict(title="Netzlast (MWh)", rangemode="tozero", hoverformat=",.0f"),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🔵 Werktag (Mo–Fr)  🟠 Wochenende (Sa–So)")


def main():
    st.sidebar.header("Ansicht wählen")
    mode = st.sidebar.radio(
        "Modus",
        [
            "Standard-Ansicht (Datum von/bis)",
            "Kalenderwochen-Overlay",
            "Tage vergleichen (bis 7 Tage)",
            "Boxplot: Lastverteilung",
        ],
    )
    st.sidebar.caption("Wähle den Darstellungsmodus für deinen Lastvergleich.")
    st.sidebar.markdown(
        "- Standard-Ansicht: Lastprofile nacheinander von einem wählbaren Datum bis zu einem wählbaren Datum\n"
        "- Kalenderwochen-Overlay: Wochenverlauf pro Wochentag\n"
        "- Tage vergleichen: bis zu 7 einzelne Tage direkt nebeneinander\n"
        "- Boxplot: Lastverteilung je Stunde oder je Wochentag (Streuung, Median, Ausreißer)"
    )

    try:
        df = load_smard_hourly_data()
    except requests.RequestException as err:
        st.error(f"Daten konnten nicht geladen werden: {err}")
        return

    if df.empty:
        st.warning("Keine Daten verfügbar.")
        return

    if mode == "Standard-Ansicht (Datum von/bis)":
        start = st.sidebar.date_input("Startdatum", value=df["date"].min())
        end = st.sidebar.date_input("Enddatum", value=df["date"].max())
        if end < start:
            st.warning("Das Enddatum muss gleich oder später als das Startdatum sein.")
        else:
            filtered = df[(df["date"] >= start) & (df["date"] <= end)]
            render_time_series(filtered, start, end)

    elif mode == "Kalenderwochen-Overlay":
        week_options = available_weeks(df)
        selected_weeks = st.sidebar.multiselect(
            "Kalenderwochen",
            options=week_options,
            default=week_options[-2:] if len(week_options) >= 2 else week_options,
            help="Wähle eine oder mehrere Kalenderwochen zum Vergleich aus.",
        )
        render_weekly_overlay(df, selected_weeks)

    elif mode == "Tage vergleichen (bis 7 Tage)":
        date_options = available_dates(df)
        selected_dates = st.sidebar.multiselect(
            "Tage",
            options=date_options,
            default=date_options[-3:] if len(date_options) >= 3 else date_options,
            help="Wähle bis zu 7 einzelne Tage zum direkten Vergleich aus.",
        )
        render_day_compare(df, selected_dates)

    else:  # Boxplot: Lastverteilung
        box_mode = st.sidebar.radio(
            "Gruppierung",
            ["Pro Stunde (Tage wählen)", "Pro Wochentag (Zeitraum)"],
            help=(
                "Pro Stunde: Verteilung der Last je Stunde über die gewählten Tage. "
                "Pro Wochentag: Verteilung je Wochentag über den gewählten Zeitraum."
            ),
        )

        if box_mode == "Pro Stunde (Tage wählen)":
            date_options = available_dates(df)
            selected_dates = st.sidebar.multiselect(
                "Tage (max. 7)",
                options=date_options,
                default=date_options[-7:] if len(date_options) >= 7 else date_options,
                help="Wähle bis zu 7 Tage. Pro Stunde wird die Verteilung über diese Tage als Box dargestellt.",
            )
            render_box_distribution(df, group_by="Stunde des Tages", selected_dates=selected_dates)
        else:
            week_options = available_weeks(df)
            selected_weeks = st.sidebar.multiselect(
                "Kalenderwochen",
                options=week_options,
                default=week_options[-4:] if len(week_options) >= 4 else week_options,
                help="Wähle einen Zeitraum. Pro Wochentag wird die Verteilung über alle Stunden dieser Wochen als Box dargestellt.",
            )
            render_box_distribution(df, group_by="Wochentag", selected_weeks=selected_weeks)

    st.sidebar.markdown("---")
    st.sidebar.caption("Datenquelle: SMARD API")


if __name__ == "__main__":
    main()            f"https://www.smard.de/app/chart_data/"
            f"{FILTER}/{REGION}/"
            f"{FILTER}_{REGION}_hour_{ts}.json"
        )
        chunk = requests.get(data_url, timeout=10)
        chunk.raise_for_status()
        series = chunk.json().get("series", [])
        for row in series:
            if row[1] is not None:
                all_data.append(row)

    df = pd.DataFrame(all_data, columns=["timestamp", "load"])
    if df.empty:
        return df

    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_convert("Europe/Berlin")
    df["date"] = df["datetime"].dt.date
    df["hour"] = df["datetime"].dt.hour
    df["weekday"] = df["datetime"].dt.isocalendar().day
    df["weekday_label"] = df["weekday"].map(WEEKDAY_LABELS)
    df["iso_year"] = df["datetime"].dt.isocalendar().year
    df["iso_week"] = df["datetime"].dt.isocalendar().week
    df["week_label"] = df.apply(lambda row: f"{row.iso_year}-KW{row.iso_week:02d}", axis=1)
    return df


def available_weeks(df: pd.DataFrame) -> list[str]:
    unique_weeks = df["week_label"].unique().tolist()
    return sorted(unique_weeks, key=lambda label: (int(label.split("-KW")[0]), int(label.split("-KW")[1])))


def available_dates(df: pd.DataFrame) -> list[str]:
    unique_dates = df["date"].astype(str).unique().tolist()
    return sorted(unique_dates)


def render_time_series(df: pd.DataFrame, start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None):
    title = "Lastprofil: Netzlast"
    if start_date is not None and end_date is not None:
        title = f"Lastprofil: {start_date} bis {end_date}"

    st.header(title)
    if df.empty:
        st.warning("Keine Daten verfügbar.")
        return

    fig = px.line(
        df,
        x="datetime",
        y="load",
        title=title,
        labels={"datetime": "Zeit", "load": "Netzlast (MW)"},
    )
    fig.update_layout(xaxis_title="Datum", yaxis_title="Last (MW)")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Max Last", f"{df['load'].max():,.0f} MW")
    col2.metric("Min Last", f"{df['load'].min():,.0f} MW")
    col3.metric("Durchschnitt", f"{df['load'].mean():,.0f} MW")


def render_weekly_overlay(df: pd.DataFrame, selected_weeks: list[str]):
    st.header("Wochenvergleich: überlagerte Wochentage")
    if df.empty or not selected_weeks:
        st.warning("Bitte wählen Sie mindestens eine Kalenderwoche aus.")
        return

    filtered = df[df["week_label"].isin(selected_weeks)].copy()
    if filtered.empty:
        st.warning("Für die ausgewählten Kalenderwochen gibt es keine Daten.")
        return

    summary = (
        filtered
        .groupby(["week_label", "weekday", "weekday_label", "hour"], as_index=False)["load"]
        .mean()
        .sort_values(["week_label", "weekday", "hour"])
    )

    summary["weekday_label"] = pd.Categorical(
        summary["weekday_label"],
        categories=["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
        ordered=True,
    )

    fig = px.line(
        summary,
        x="hour",
        y="load",
        color="weekday_label",
        line_dash="week_label",
        title="Stündliche Lastprofile pro Wochentag und Kalenderwoche",
        labels={
            "hour": "Stunde des Tages",
            "load": "Netzlast (MW)",
            "weekday_label": "Wochentag",
            "week_label": "Kalenderwoche",
        },
        hover_data={"week_label": True, "weekday_label": True, "hour": True, "load": ":.1f"},
    )

    fig.update_layout(
        xaxis=dict(tickmode="array", tickvals=list(range(0, 24)), ticktext=[str(h) for h in range(0, 24)]),
        yaxis=dict(title="Netzlast (MW)", rangemode="tozero"),
        legend_title_text="Wochentag / Woche",
        margin=dict(l=50, r=280, t=90, b=50),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_day_compare(df: pd.DataFrame, selected_dates: list[str]):
    st.header("Tagesvergleich: bis zu 7 Tage")
    if df.empty or not selected_dates:
        st.warning("Bitte wählen Sie mindestens einen Tag aus.")
        return

    if len(selected_dates) > 7:
        st.warning("Bitte wählen Sie maximal 7 Tage aus.")
        return

    selected = df[df["date"].astype(str).isin(selected_dates)].copy()
    if selected.empty:
        st.warning("Für die ausgewählten Tage gibt es keine Daten.")
        return

    summary = (
        selected
        .groupby(["date", "hour"], as_index=False)["load"]
        .mean()
        .sort_values(["date", "hour"])
    )

    fig = px.line(
        summary,
        x="hour",
        y="load",
        color="date",
        title="Stündliche Lastprofile der ausgewählten Tage",
        labels={"hour": "Stunde des Tages", "load": "Netzlast (MW)", "date": "Datum"},
        hover_data={"date": True, "hour": True, "load": ":.1f"},
    )

    fig.update_layout(
        xaxis=dict(tickmode="array", tickvals=list(range(0, 24)), ticktext=[str(h) for h in range(0, 24)]),
        yaxis=dict(title="Netzlast (MW)", rangemode="tozero"),
        legend_title_text="Datum",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Tagesvergleich Detail")
    st.data_editor(summary.head(14), disabled=True)


def main():
    st.sidebar.header("Ansicht wählen")
    mode = st.sidebar.radio(
        "Modus",
        [
            "Standard-Ansicht (Datum von/bis)",
            "Kalenderwochen-Overlay",
            "Tage vergleichen (bis 7 Tage)",
        ],
    )
    st.sidebar.caption("Wähle den Darstellungsmodus für deinen Lastvergleich.")
    st.sidebar.markdown(
        "- Standard-Ansicht: Lastprofile nacheinander von einem wählbaren Datum bis zu einem wählbaren Datum\n"
        "- Kalenderwochen-Overlay: Wochenverlauf pro Wochentag\n"
        "- Tage vergleichen: bis zu 7 einzelne Tage direkt nebeneinander"
    )

    try:
        df = load_smard_hourly_data()
    except requests.RequestException as err:
        st.error(f"Daten konnten nicht geladen werden: {err}")
        return

    if df.empty:
        st.warning("Keine Daten verfügbar.")
        return

    if mode == "Standard-Ansicht (Datum von/bis)":
        start = st.sidebar.date_input("Startdatum", value=df["date"].min())
        end = st.sidebar.date_input("Enddatum", value=df["date"].max())
        if end < start:
            st.warning("Das Enddatum muss gleich oder später als das Startdatum sein.")
        else:
            filtered = df[(df["date"] >= start) & (df["date"] <= end)]
            render_time_series(filtered, start, end)

    elif mode == "Kalenderwochen-Overlay":
        week_options = available_weeks(df)
        selected_weeks = st.sidebar.multiselect(
            "Kalenderwochen",
            options=week_options,
            default=week_options[-2:] if len(week_options) >= 2 else week_options,
            help="Wähle eine oder mehrere Kalenderwochen zum Vergleich aus.",
        )
        render_weekly_overlay(df, selected_weeks)

    else:
        date_options = available_dates(df)
        selected_dates = st.sidebar.multiselect(
            "Tage",
            options=date_options,
            default=date_options[-3:] if len(date_options) >= 3 else date_options,
            help="Wähle bis zu 7 einzelne Tage zum direkten Vergleich aus.",
        )
        render_day_compare(df, selected_dates)

    st.sidebar.markdown("---")
    st.sidebar.caption("Datenquelle: SMARD API")


if __name__ == "__main__":
    main()
