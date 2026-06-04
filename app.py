import requests
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

st.title("SMARD Lastprofil Dashboard")

FILTER = "410"
REGION = "DE"

@st.cache_data
def load_data():

```
index_url = (
    f"https://www.smard.de/app/chart_data/"
    f"{FILTER}/{REGION}/index_hour.json"
)

response = requests.get(index_url)
timestamps = response.json()["timestamps"]

all_data = []

for ts in timestamps[-20:]:

    data_url = (
        f"https://www.smard.de/app/chart_data/"
        f"{FILTER}/{REGION}/"
        f"{FILTER}_{REGION}_hour_{ts}.json"
    )

    data = requests.get(data_url).json()["series"]

    for row in data:
        if row[1] is not None:
            all_data.append(row)

df = pd.DataFrame(
    all_data,
    columns=["timestamp", "load"]
)

df["datetime"] = pd.to_datetime(
    df["timestamp"],
    unit="ms",
    utc=True
).dt.tz_convert("Europe/Berlin")

return df
```

df = load_data()

st.sidebar.header("Filter")

start = st.sidebar.date_input(
"Startdatum",
value=df["datetime"].dt.date.min()
)

end = st.sidebar.date_input(
"Enddatum",
value=df["datetime"].dt.date.max()
)

filtered = df[
(df["datetime"].dt.date >= start)
& (df["datetime"].dt.date <= end)
]

fig = px.line(
filtered,
x="datetime",
y="load",
title="Deutsche Netzlast"
)

st.plotly_chart(
fig,
use_container_width=True
)

col1, col2, col3 = st.columns(3)

col1.metric(
"Max Last",
f"{filtered['load'].max():,.0f} MW"
)

col2.metric(
"Min Last",
f"{filtered['load'].min():,.0f} MW"
)

col3.metric(
"Durchschnitt",
f"{filtered['load'].mean():,.0f} MW"
)
