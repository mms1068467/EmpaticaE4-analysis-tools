# Contents of ~/my_app/pages/page_3.py
import streamlit as st
from pathlib import Path
import os

# temporarily saves the file
def save_uploadedfile(uploaded_file, path: str):
    with open(os.path.join(path, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())

    return st.success("Temporarily saved file: {} to {}".format(uploaded_file.name, path))


st.markdown("# Drag and drop a .csv or .xlsx file and explore correlations:")

path = Path(__file__).parent.resolve()

#
uploaded_data_file = st.file_uploader("Drag and drop your file here ...", type=["csv", "xlsx"],
                                          accept_multiple_files=False)

if uploaded_data_file is not None:

    # save locally to access it
    save_uploadedfile(uploaded_file=uploaded_data_file, path=path)
    full_file_name = uploaded_data_file.name.split(".")[0] + "." + uploaded_data_file.name.split(".")[1]
    saved_folder_path = str(path) + "\\" + full_file_name

    bytes_data = uploaded_data_file.getvalue()

    #data = uploaded_data_file.getvalue()
    #st.write(data)

    #st.session_state["preview"] == ''

    #for i in range(0, min(5, len(data))):
        #st.session_state['preview'] += data[i]

#preview = st.text_area("XLSX Preview", "", height = 150, key = "preview")