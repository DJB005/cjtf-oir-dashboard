import streamlit as st
import pandas as pd
from pathlib import Path

st.title("CJTF-OIR Dashboard")

st.write("Deployment scaffold. Upload your data CSV to `data/cjtf_oir_strikes_clean.csv`.")

data_path = Path("data/cjtf_oir_strikes_clean.csv")
if data_path.exists():
    df = pd.read_csv(data_path)
    st.success("Loaded dataset")
    st.write(df.head())
else:
    st.warning("Dataset not found yet.")
