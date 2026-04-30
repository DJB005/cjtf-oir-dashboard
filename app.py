import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional
import plotly.express as px

st.set_page_config(page_title="CJTF-OIR Dashboard", layout="wide")
st.title("CJTF-OIR Dashboard")
st.caption(
    "This dashboard loads automatically from the repo's `data/` folder (recommended). "
    "If you want to test a variation, you can optionally override with an upload or URL."
)

STRIKES_PATH = Path("data/cjtf_oir_strikes_clean.csv")
GEO_PATH = Path("data/cjtf_oir_strikes_geocoded.csv")
AFCENT_PATH = Path("data/afcent_macro_clean.csv")


@st.cache_data(show_spinner=False)
def _read_csv(source) -> pd.DataFrame:
    df = pd.read_csv(source)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def load_dataset(path: Path, label: str, *, key: str) -> Optional[pd.DataFrame]:
    if path.exists():
        st.success(f"Loaded `{path}` from the repo.")
        return _read_csv(path)

    with st.expander(f"Optional override for {label}"):
        uploaded = st.file_uploader(
            f"Upload {label}",
            type=["csv"],
            key=f"{key}_uploader",
        )
        if uploaded is not None:
            st.success("Loaded uploaded CSV.")
            return _read_csv(uploaded)

        csv_url = st.text_input("Or paste a CSV URL", key=f"{key}_url")
        if csv_url:
            st.success("Loaded CSV from URL.")
            return _read_csv(csv_url)

        st.info("No data provided yet.")

    return None


st.sidebar.markdown("### Data sources")
strikes_df = load_dataset(STRIKES_PATH, "CJTF-OIR strikes (clean)", key="strikes")
geo_df = load_dataset(GEO_PATH, "Geocoded strikes (optional)", key="geo")
afcent_df = load_dataset(AFCENT_PATH, "AFCENT macro (optional)", key="afcent")

if strikes_df is None:
    st.warning(
        "CJTF-OIR strikes dataset not available yet. Add it to `data/` or upload above."
    )
    st.stop()

if "strike_count" not in strikes_df.columns:
    strikes_df["strike_count"] = 1

strikes_df = strikes_df.copy()
strikes_df["date"] = pd.to_datetime(strikes_df.get("date"), errors="coerce")
strikes_df = strikes_df.dropna(subset=["date"]).sort_values("date")
strikes_df["cum_strikes"] = strikes_df["strike_count"].cumsum()

st.subheader("Quick preview")
st.dataframe(strikes_df.head(), use_container_width=True)
st.write("Rows:", len(strikes_df))
st.write("Columns:", list(strikes_df.columns))

st.subheader("Cumulative strike timeline")
fig = px.line(
    strikes_df,
    x="date",
    y="cum_strikes",
    title="Cumulative strikes over time",
)
fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig, width="stretch")

if geo_df is not None:
    st.subheader("Cumulative strikes by location (map)")

    required = {"country", "location", "date"}
    if not required.issubset(geo_df.columns):
        st.warning(
            "Geocoded dataset is missing required columns. Expected columns like: "
            "`country`, `location`, `date`, `lat`, `lon`."
        )
    else:
        geo = geo_df.copy()

        if "strike_count" not in geo.columns:
            geo["strike_count"] = 1

        geo["date"] = pd.to_datetime(geo["date"], errors="coerce")
        geo = geo.dropna(subset=["date"])

        if geo.empty:
            st.warning(
                "Geocoded dataset has no valid dates after parsing. Check the `date` column format."
            )
        else:
            geo["location_key"] = (
                geo["country"].fillna("Unknown")
                + " | "
                + geo["location"].fillna("Unknown")
            )
            geo = geo.sort_values("date")
            geo["cum_strikes"] = geo.groupby("location_key")["strike_count"].cumsum()

            min_date = geo["date"].min().date()
            max_date = geo["date"].max().date()

            selected_date = st.slider(
                "Cumulative through",
                min_value=min_date,
                max_value=max_date,
                value=max_value,
                format="YYYY-MM-DD",
            )

            filtered = geo[geo["date"].dt.date <= selected_date].copy()
            latest = filtered.sort_values("date").groupby(
                "location_key", as_index=False
            ).tail(1)

            st.write(f"{len(latest)} locations shown through {selected_date}.")
            st.dataframe(
                latest[["country", "location", "cum_strikes"]]
                .sort_values("cum_strikes", ascending=False),
                use_container_width=True,
            )

            if {"lat", "lon"}.issubset(latest.columns):
                map_fig = px.scatter_geo(
                    latest,
                    lat="lat",
                    lon="lon",
                    size="cum_strikes",
                    color="country",
                    hover_name="location",
                    hover_data={
                        "cum_strikes": True,
                        "country": True,
                        "lat": False,
                        "lon": False,
                    },
                    title="Cumulative strikes by location (bubble size)",
                )
                map_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(map_fig, width="stretch")
            else:
                st.warning(
                    "No `lat`/`lon` columns detected. Add geocoded coordinates to show the map."
                )
else:
    st.info(
        "Add `data/cjtf_oir_strikes_geocoded.csv` (or upload it) to enable the cumulative map."
    )

if afcent_df is not None:
    st.subheader("AFCENT macro (quick view)")
    st.dataframe(afcent_df.head(), use_container_width=True)
