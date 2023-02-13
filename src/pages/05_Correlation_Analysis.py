import streamlit as st
from pathlib import Path
import os
import pandas as pd
import numpy as np

# temporarily saves the file
@st.cache
def save_uploadedfile(uploaded_file, path: str):
    with open(os.path.join(path, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())

st.markdown("# Drag and drop the Stress Output .xlsx file and explore correlations:")


path = Path(__file__).parent.resolve()

