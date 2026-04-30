import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="CJTF-OIR Dashboard", layout="wide")
st.title("CJTF-OIR Dashboard")

st.caption("The app will load from `data/cjtf_oir_strikes_clean.csv` if present. If not, you can upload a CSV or paste a URL.")

DATA_PATH = Path("data/cjtf_oir_strikes_clean.csv")


def get_df() -> pd.DataFrame:
    if DATA_PATH.exists():
        st.success("Loaded data/cjtf_oir_strikes_clean.csv from the repo")
        return pd.read_csv(DATA_PATH)

    uploaded = st.file_uploader("Upload cjtf_oir_strikes_clean.csv", type=["csv"])
    if uploaded is not None:
        st.success("Loaded uploaded CSV")
        return pd.read_csv(uploaded)

    csv_url = st.text_input("Or paste a CSV URL (GitHub raw, etc.)")
    if csv_url:
        st.success("Loaded CSV from URL")
        return pd.read_csv(csv_url)

    st.warning("Dataset not found. Provide a file above to continue.")
    st.stop()


df = get_df()

st.subheader("Quick preview")
st.dataframe(df.head())
st.write("Rows:", len(df))
st.write("Columns:", list(df.columns))
