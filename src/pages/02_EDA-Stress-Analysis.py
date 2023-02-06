# Contents of ~/my_app/pages/page_2.py
import streamlit as st
import datetime
import sqlite3
import time
import zipfile
from contextlib import contextmanager
from pathlib import Path
import pandas as pd
import random
import zipfile
import base64
import io
#import filetype
import shutil

import E4_Analysis_tools as e4at

from MOS_Detection import MOS_rules_paper_verified as mrp
from MOS_Detection import MOS_signal_preparation_verified as msp_new
import MOS_Detection.MOS_rules_NEW as MOS_paper_new
from HumanSensing_Preprocessing import utilities

# temporarily saves the file
def save_uploadedfile(uploaded_file, path: str):
    with open(os.path.join(path, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())

    return st.success("Temporarily saved file: {} to {}".format(uploaded_file.name, path))


#### Caching the plot functions to (slightly) increase performance
@st.cache(allow_output_mutation=True)
def merge_data(signal_path, labels_path, signal):

    return_signal = e4at.merge_data(signal_path=signal_path, labels_path=labels_path, signal=signal)

    return return_signal


@st.cache
def open_and_extract_zip_pat(path, zip_folder: str) -> list:
    path_str = str(path)
    zip_folder_name = zip_folder.name.split(".")[0] + "." + zip_folder.name.split(".")[1]

    folder_location = path_str + "\\" + zip_folder_name
    print("\n\nOpen_and_extract_zip_pat() log\nFolder path: ", folder_location)
    if not os.path.isdir(folder_location):
        os.makedirs(folder_location)

    z = ZipFile(zip_folder)
    for name in z.namelist():
        # print(name)
        z.extract(name, folder_location)

    return folder_location


@st.cache
def find_all_csv_xslx_files(folder_path: str) -> list:
    csv_xslx_files = []

    if os.path.isfile(folder_path):
        csv_xslx_files.append(folder_path)
        print("Yep")


    else:
        if os.path.exists(folder_path + "\\" + "__MACOSX"):
            shutil.rmtree(folder_path + "\\" + "__MACOSX")

        for root, dirs, files in os.walk(folder_path):
            # print("Root: \n", root)
            # print("Directory: \n", dirs)
            # print('Files: \n', files)
            for file in files:
                if file.endswith('.csv') or file.endswith('.xlsx'):
                    csv_xslx_files.append(os.path.join(root, file))

    print(f"Found {len(csv_xslx_files)} .csv and .xslx files. \n")
    return csv_xslx_files


st.markdown("# Drag and drop a zip file containing multiple candidates and begin Stress Analysis")

global_working_folder_path = None
# If neccessary, add an users local path in order to use and store the files from the app
# path = st.text_input("Please enter the path where you want to store the project data INCLUDING a '/' at the end and press Enter (Example: C:/Users/projects/data/)" )
path = Path(__file__).parent.resolve()

uploaded_E4_zip_folder = st.file_uploader("Drag and drop your SALK E4 zip folder(s) here...", type=["zip", "7z"],
                                          accept_multiple_files=False)

#### Main, branching part of the application as soon as the zip is uploaded
if uploaded_E4_zip_folder is not None:
    try:

        eda_file_list = []

        filename = uploaded_E4_zip_folder.name
        filetype = uploaded_E4_zip_folder.type

        #st.write("File name is ", filename)
        #st.write("File type is ", filetype)

        if filename.endswith(".zip"):

            #st.write("ID is: ", filename.split(".zip")[0])
            folderID = filename.split(".zip")[0]

            #st.write(uploaded_E4_zip_folder)

            with zipfile.ZipFile(uploaded_E4_zip_folder, 'r') as zipObj:
                # extract all content of zip file in current directory
                list_of_files = zipObj.namelist()

                zipObj.extractall(path)

                for fl in list_of_files:
                    subfolder_path = Path.joinpath(path, fl)

                    #st.write("File Name: ", subfolder_path.split(".zip")[0])


                    with zipfile.ZipFile(subfolder_path, 'r') as zipO:
                        file_ls = zipO.namelist()

                        zipO.extractall(path)

                        #st.write(Path.joinpath(path, file_ls))
                        patID = file_ls[0].split("/")[0]



                        for filen in file_ls:
                            if 'EDA' in filen and 'MACOSX' not in filen:
                                path_to_EDA_file = Path.joinpath(path, filen)
                                #st.write("Path to the EDA file is: ", path_to_EDA_file)

                                patientPath = Path.joinpath(path, filen.split("/")[0])

                                #st.write("Path to Patient is patientPath", patientPath)

                                patientNr = fl.split(".")[1]

                                #st.write("Path to EDA file: ", Path.joinpath(patientPath, "EDA.csv"))
                                #st.write("Path to Auswertungsfile file: ", Path.joinpath(
                                #        patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                #            patientNr)))

                                EDA_labeled_date_extract = merge_data(
                                    signal_path=Path.joinpath(patientPath, "EDA.csv"),
                                    labels_path=Path.joinpath(
                                        patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                            patientNr)),
                                    signal="EDA")

                                EDA_preprocessed_MOS = e4at.preprocess_EDA(EDA_labeled_date_extract)

                                EDA_labeled_date_extract["ID"] = patID
                                st.write(EDA_labeled_date_extract)

                                #initial_start_time = EDA_labeled_date_extract['datetime'].min()
                                #initial_end_time = EDA_labeled_date_extract['datetime'].max().round('1s')

                                kyriakou2019 = st.sidebar.checkbox(
                                    "MOS Algorithm according to Kyriakou et al. (2019)")

                                moser2023 = st.sidebar.checkbox("Individual-oriented MOS Algorithm (new)")

                                if kyriakou2019:

                                    EDA_data_MOS = EDA_labeled_date_extract.copy()

                                    #EDA_preprocessed_MOS = e4at.preprocess_EDA(EDA_data_MOS)

                                    # Prepare ST for MOS generation
                                    ST_labeled_MOS = merge_data(
                                        signal_path=Path.joinpath(patientPath, "TEMP.csv"),
                                        labels_path=Path.joinpath(
                                            patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                patientNr)),
                                        signal="ST")

                                    ST_preprocessed_MOS = e4at.preprocess_ST(ST_labeled_MOS)

                                    #st.write(ST_preprocessed_MOS)

                                    # fine-tuning of prepared GSR and ST by merging into single dataframe as well as generating TimeNum and renaming and removing of the columns
                                    join_GSR_ST_MOS = pd.merge(EDA_preprocessed_MOS,
                                                               ST_preprocessed_MOS[["ST", "ST_filtered", "datetime"]],
                                                               left_on="datetime", right_on="datetime", how="left")

                                    join_GSR_ST_MOS.rename(
                                        columns={'datetime': 'time_iso', 'EDA': 'GSR_raw', 'EDA_filtered': 'GSR',
                                                 'ST': 'ST_raw', 'ST_filtered': 'ST'}, inplace=True)

                                    #st.write(join_GSR_ST_MOS)

                                    join_GSR_ST_MOS = join_GSR_ST_MOS.drop(
                                        ["date", "time", "Vorgang", "Uhrzeit", "Anmerkung"],
                                        axis=1)

                                    join_GSR_ST_MOS['TimeNum'] = join_GSR_ST_MOS["time_iso"].map(pd.Timestamp.timestamp)

                                    #st.write("Joined MOS Detection Input", join_GSR_ST_MOS)

                                    final_MOS_output, extended_MOS_output, mos_identified = mrp.MOS_main_df(
                                        df=join_GSR_ST_MOS)


                                    st.write("MOS Output")


                                if moser2023:
                                    pass


                                # TODO -- perform Stress Detection here


    except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError, sqlite3.OperationalError):

        print("\nRng{}: Unable to process your request ! Something wrong in the SALK E4 zip file section".format(

            random.randint(0, 50)))

    finally:

        st.info("Finally executed")


    #st.write("Result List of EDA files: ", path_to_EDA_file)



