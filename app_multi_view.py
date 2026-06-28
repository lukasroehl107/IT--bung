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

WEEKDAY_ORDER = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]

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

    df["datetime"] = pd.to_datetime(
        df["timestamp"], unit="ms", utc=True
    ).dt.tz_convert("Europe/Berlin")

    df["date"] = df["datetime"].dt.date
    df["hour"] = df["datetime"].dt.hour
    df["weekday"] = df["datetime"].dt.isocalendar().day
    df["weekday_label"] = df["weekday"].map(WEEKDAY_LABELS)
    df["iso_year"] = df["datetime"].dt.isocalendar().year
    df["iso_week"] = df["datetime"].dt.isocalendar().week

    df["week_label"] = df.apply(
        lambda row: f"{row.iso_year}-KW{row.iso_week:02d}",
        axis=1
    )

    return df


def available_weeks(df):
    unique_weeks = df["week_label"].unique().tolist()
    return sorted(
        unique_weeks,
        key=lambda label: (
            int(label.split("-KW")[0]),
            int(label.split("-KW")[1])
        )
    )


def available_dates(df):
    unique_dates = df["date"].astype(str).unique().tolist()
    return sorted(unique_dates)


def render_time_series(df, start_date=None, end_date=None):
    title = "Lastprofil: Netzlast"

    if start_date and end_date:
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
        labels={
            "datetime": "Zeit",
            "load": "Netzlast (MWh)"
        }
    )

    fig.update_layout(
        xaxis_title="Datum",
        yaxis_title="Last (MWh)"
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    col1.metric("Max Last", f"{df['load'].max():,.0f} MWh")
    col2.metric("Min Last", f"{df['load'].min():,.0f} MWh")
    col3.metric("Durchschnitt", f"{df['load'].mean():,.0f} MWh")


def render_weekly_overlay(df, selected_weeks):
    st.header("Wochenvergleich")

    if df.empty or not selected_weeks:
        st.warning("Bitte Wochen auswählen.")
        return

    filtered = df[df["week_label"].isin(selected_weeks)].copy()

    summary = (
        filtered.groupby(
            ["week_label", "weekday", "weekday_label", "hour"],
            as_index=False
        )["load"]
        .mean()
        .sort_values(["week_label", "weekday", "hour"])
    )

    fig = px.line(
        summary,
        x="hour",
        y="load",
        color="weekday_label",
        line_dash="week_label",
        title="Wöchentlicher Vergleich"
    )

    st.plotly_chart(fig, use_container_width=True)


def render_day_compare(df, selected_dates):
    st.header("Tagesvergleich")

    if df.empty or not selected_dates:
        st.warning("Bitte Tage auswählen.")
        return

    if len(selected_dates) > 7:
        st.warning("Maximal 7 Tage.")
        return

    selected = df[df["date"].astype(str).isin(selected_dates)].copy()

    summary = (
        selected.groupby(["date", "hour"], as_index=False)["load"]
        .mean()
        .sort_values(["date", "hour"])
    )

    fig = px.line(
        summary,
        x="hour",
        y="load",
        color="date",
        title="Tagesvergleich"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.data_editor(summary.head(24), disabled=True)


def render_box_distribution(df, selected_dates):
    st.header("Boxplot Lastverteilung")

    if df.empty or not selected_dates:
        st.warning("Bitte Tage auswählen.")
        return

    subset = df[df["date"].astype(str).isin(selected_dates)].copy()

    fig = px.box(
        subset,
        x="hour",
        y="load",
        points="outliers",
        title="Verteilung je Stunde"
    )

    st.plotly_chart(fig, use_container_width=True)


def main():
    st.sidebar.header("Ansicht wählen")

    mode = st.sidebar.radio(
        "Modus",
        [
            "Standard",
            "Wochenvergleich",
            "Tagesvergleich",
            "Boxplot"
        ]
    )

    try:
        df = load_smard_hourly_data()
    except requests.RequestException as err:
        st.error(f"Daten konnten nicht geladen werden: {err}")
        return

    if df.empty:
        st.warning("Keine Daten verfügbar.")
        return

    if mode == "Standard":
        start = st.sidebar.date_input(
            "Startdatum",
            value=df["date"].min()
        )

        end = st.sidebar.date_input(
            "Enddatum",
            value=df["date"].max()
        )

        filtered = df[
            (df["date"] >= start) &
            (df["date"] <= end)
        ]

        render_time_series(filtered, start, end)

    elif mode == "Wochenvergleich":
        week_options = available_weeks(df)

        selected_weeks = st.sidebar.multiselect(
            "Kalenderwochen",
            options=week_options,
            default=week_options[-2:]
        )

        render_weekly_overlay(df, selected_weeks)

    elif mode == "Tagesvergleich":
        date_options = available_dates(df)

        selected_dates = st.sidebar.multiselect(
            "Tage",
            options=date_options,
            default=date_options[-3:]
        )

        render_day_compare(df, selected_dates)

    elif mode == "Boxplot":
        date_options = available_dates(df)

        selected_dates = st.sidebar.multiselect(
            "Tage",
            options=date_options,
            default=date_options[-7:]
        )

        render_box_distribution(df, selected_dates)


if __name__ == "__main__":
    main()