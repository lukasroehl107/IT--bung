import requests
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")
st.title("SMARD Lastprofil Wochenvergleich")

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

@st.cache_data
def load_smard_hourly_data():
    index_url = (
        f"https://www.smard.de/app/chart_data/"
        f"{FILTER}/{REGION}/index_hour.json"
    )

    response = requests.get(index_url, timeout=10)
    response.raise_for_status()
    timestamps = response.json()["timestamps"]

    all_data = []
    for ts in timestamps[-20:]:
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
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_convert("Europe/Berlin")
    df["weekday"] = df["datetime"].dt.isocalendar().day
    df["weekday_label"] = df["weekday"].map(WEEKDAY_LABELS)
    df["hour"] = df["datetime"].dt.hour
    df["iso_year"] = df["datetime"].dt.isocalendar().year
    df["iso_week"] = df["datetime"].dt.isocalendar().week
    df["week_label"] = df.apply(lambda row: f"{row.iso_year}-KW{row.iso_week:02d}", axis=1)
    return df


def build_week_options(df: pd.DataFrame) -> list[str]:
    unique_weeks = df["week_label"].unique()
    return sorted(unique_weeks, key=lambda label: (int(label.split("-KW")[0]), int(label.split("-KW")[1])))


def build_hourly_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return (
        df.groupby(["week_label", "weekday", "weekday_label", "hour"], as_index=False)["load"]
        .mean()
        .sort_values(["week_label", "weekday", "hour"])
    )


def main():
    st.sidebar.header("Kalenderwoche auswählen")
    df = load_smard_hourly_data()

    week_options = build_week_options(df)
    default_weeks = week_options[-2:] if len(week_options) >= 2 else week_options
    selected_weeks = st.sidebar.multiselect(
        "Kalenderwochen",
        options=week_options,
        default=default_weeks,
        help="Wählen Sie eine oder mehrere Kalenderwochen zur Vergleichsansicht aus.",
    )

    if not selected_weeks:
        st.warning("Bitte wählen Sie mindestens eine Kalenderwoche aus.")
        return

    filtered = df[df["week_label"].isin(selected_weeks)].copy()
    if filtered.empty:
        st.warning("Für die ausgewählten Kalenderwochen konnten keine Daten geladen werden.")
        return

    summary = build_hourly_summary(filtered)
    summary["weekday_label"] = pd.Categorical(
        summary["weekday_label"],
        categories=[
            "Montag",
            "Dienstag",
            "Mittwoch",
            "Donnerstag",
            "Freitag",
            "Samstag",
            "Sonntag",
        ],
        ordered=True,
    )

    fig = px.line(
        summary,
        x="hour",
        y="load",
        color="weekday_label",
        line_dash="week_label",
        hover_data={
            "week_label": True,
            "weekday_label": True,
            "hour": True,
            "load": ":.1f",
        },
        title="Stündliche Lastprofile pro Wochentag und Kalenderwoche",
        labels={
            "hour": "Stunde des Tages",
            "load": "Netzlast (MW)",
            "weekday_label": "Wochentag",
            "week_label": "Kalenderwoche",
        },
    )

    fig.update_layout(
        legend_title_text="Wochentag / Woche",
        xaxis=dict(tickmode="array", tickvals=list(range(0, 24)), ticktext=[str(h) for h in range(0, 24)]),
        yaxis=dict(title="Netzlast (MW)", rangemode="tozero"),
        margin=dict(l=50, r=280, t=90, b=50),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Zusammenfassung")
    total_hours = summary.shape[0]
    st.markdown(f"- Ausgewählte Kalenderwochen: **{', '.join(selected_weeks)}**")
    st.markdown(f"- Angezeigte Stundenpunkte: **{total_hours}**")

    pivot = summary.pivot_table(
        index=["hour"],
        columns=["weekday_label", "week_label"],
        values="load",
        aggfunc="mean",
    )
    st.data_editor(pivot.head(10), disabled=True)


if __name__ == "__main__":
    main()
