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
from io import BytesIO

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

def adjust_ts(data, time_col, hours = 1):

    df = data.copy()
    df[time_col] = pd.to_datetime(df[time_col].astype(str))
    df[time_col] += pd.to_timedelta(hours, unit = 'h')
    df[time_col] = df[time_col].dt.time
    return df


#### Caching the plot functions to (slightly) increase performance
@st.cache(allow_output_mutation=True)
def merge_data(signal_path, labels_path, signal, adjust_timestamp):

    return_signal = e4at.merge_data(signal_path=signal_path, labels_path=labels_path, signal=signal, adjust_timestamp = adjust_timestamp)

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


st.markdown("# Drag and drop a zip file containing multiple candidates (zipped) and begin Stress Analysis")

global_working_folder_path = None
# If neccessary, add an users local path in order to use and store the files from the app
# path = st.text_input("Please enter the path where you want to store the project data INCLUDING a '/' at the end and press Enter (Example: C:/Users/projects/data/)" )
path = Path(__file__).parent.resolve()

uploaded_E4_zip_folder = st.file_uploader("Drag and drop your SALK E4 zip folder(s) here...", type=["zip", "7z"],
                                          accept_multiple_files=False)

#### Main, branching part of the application as soon as the zip is uploaded
if uploaded_E4_zip_folder is not None:

    st.sidebar.title("Choose Stress Detection Algorithm to apply:")

    kyriakou2019 = st.sidebar.checkbox(
        "MOS Algorithm - Kyriakou et al. (2019)")

    moser2023 = st.sidebar.checkbox("Individual-oriented MOS Algorithm - Moser et al. (2023)")


    # TODO - potentially uncomment this

    #filename = uploaded_E4_zip_folder.name
    #filetype = uploaded_E4_zip_folder.type

    # st.write("File name is ", filename)
    # st.write("File type is ", filetype)

    #if filename.endswith(".zip"):

        # st.write("ID is: ", filename.split(".zip")[0])
    #    folderID = filename.split(".zip")[0]

        # st.write(uploaded_E4_zip_folder)

    #    with zipfile.ZipFile(uploaded_E4_zip_folder, 'r') as zipObj:
            # extract all content of zip file in current directory
    #        list_of_files = zipObj.namelist()

    #        zipObj.extractall(path)

    #        for fl in list_of_files:
    #            subfolder_path = Path.joinpath(path, fl)

    #            st.write("File Name: ", subfolder_path)

    #            with zipfile.ZipFile(subfolder_path, 'r') as zipO:
    #                file_ls = zipO.namelist()

    #                zipO.extractall(path)

                    #st.write(Path.joinpath(path, file_ls))

    #                patID = file_ls[0].split("/")[0]

    #                st.write("patID which will be set to ID is: ", patID)

    try:

        if kyriakou2019:

            st.header("Stress Detection Output - Kyriakou et al. 2019")

            kyriakou_MOS_outputs = []

            eda_file_list = []

            # TODO - uncomment this to get the older working version

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

                        #st.write(subfolder_path)
                        #if subfolder_path.endswith('.zip'):


                        with zipfile.ZipFile(subfolder_path, 'r') as zipO:
                            file_ls = zipO.namelist()
                            st.write(file_ls)

                            zipO.extractall(path)

                            #st.write(Path.joinpath(path, file_ls))
                            patID = file_ls[0].split("/")[0]

                        #else:

                            st.write("patID which will be set to ID is: ", patID)

                            for filen in file_ls:
                                if 'EDA' in filen and 'MACOSX' not in filen:
                                    path_to_EDA_file = Path.joinpath(path, filen)
                                    #st.write("Path to the EDA file is: ", path_to_EDA_file)

                                    patientPath = Path.joinpath(path, filen.split("/")[0])

                                    #st.write("Path to Patient is patientPath", patientPath)

                                    patientNr = fl.split(".")[1]

                                    st.write("Patient Number:", patientNr)

                                    #st.write("Path to EDA file: ", Path.joinpath(patientPath, "EDA.csv"))
                                    #st.write("Path to Auswertungsfile file: ", Path.joinpath(
                                    #        patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                    #            patientNr)))

                                    # TODO - Timestamp Adjustment --> add 1 hour in seconds to Uhrzeit in Zeitenauswertung
                                    patients_to_adjust = ["Pat.18", "Pat.19", "Pat.20",
                                                          "Pat.21", "Pat.22", "Pat.23", "Pat.24", "Pat.25",
                                                          "Pat.26", "Pat.27", "Pat.28", "Pat.29", "Pat.30"]
                                    #patients_to_adjust = [18, 19, 20, 21, 22, 23, 24, 25,
                                    #                      26, 27, 28, 29, 30]

                                    if patID in patients_to_adjust:

                                        st.write("Adjusting Timestamp:")

                                        EDA_labeled_date_extract = merge_data(
                                            signal_path=Path.joinpath(patientPath, "EDA.csv"),
                                            labels_path=Path.joinpath(
                                                patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                    patientNr)),
                                            signal="EDA",
                                        adjust_timestamp = True)


                                        EDA_preprocessed_MOS = e4at.preprocess_EDA(EDA_labeled_date_extract)

                                        EDA_labeled_date_extract["ID"] = patID
                                        # st.write(EDA_labeled_date_extract)

                                        # Prepare ST for MOS generation
                                        ST_labeled_MOS = merge_data(
                                            signal_path=Path.joinpath(patientPath, "TEMP.csv"),
                                            labels_path=Path.joinpath(
                                                patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                    patientNr)),
                                            signal="ST",
                                        adjust_timestamp = True)

                                        ST_preprocessed_MOS = e4at.preprocess_ST(ST_labeled_MOS)

                                        ST_preprocessed_MOS["ID"] = patID

                                        # fine-tuning of prepared GSR and ST by merging into single dataframe as well as generating TimeNum and renaming and removing of the columns
                                        join_GSR_ST_MOS = pd.merge(EDA_preprocessed_MOS,
                                                                   ST_preprocessed_MOS[
                                                                       ["ST", "ST_filtered", "datetime"]],
                                                                   left_on="datetime", right_on="datetime", how="left")

                                        ########## individual file imports for debugging purposes (adjusting timestamps of certain files)
                                        #Zeitenauswertung = pd.read_excel(Path.joinpath(
                                        #    patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                        #        patientNr)))

                                        #st.write("Zeitenauswertung von Patient VOR Adjustment:", Zeitenauswertung)

                                        #Zeitenauswertung = adjust_ts(Zeitenauswertung, time_col = "Uhrzeit")

                                        #EDA_file = e4at.EDA_processing(Path.joinpath(patientPath, "EDA.csv"))
                                        #st.write("EDA file for Patient", patID, " :", EDA_file)

                                    else:

                                        EDA_labeled_date_extract = merge_data(
                                            signal_path=Path.joinpath(patientPath, "EDA.csv"),
                                            labels_path=Path.joinpath(
                                                patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                    patientNr)),
                                            signal="EDA",
                                        adjust_timestamp = False)

                                        EDA_preprocessed_MOS = e4at.preprocess_EDA(EDA_labeled_date_extract)

                                        EDA_labeled_date_extract["ID"] = patID
                                        # st.write(EDA_labeled_date_extract)

                                        # Prepare ST for MOS generation
                                        ST_labeled_MOS = merge_data(
                                            signal_path=Path.joinpath(patientPath, "TEMP.csv"),
                                            labels_path=Path.joinpath(
                                                patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                    patientNr)),
                                            signal="ST",
                                        adjust_timestamp = False)

                                        ST_preprocessed_MOS = e4at.preprocess_ST(ST_labeled_MOS)

                                        ST_preprocessed_MOS["ID"] = patID

                                        # fine-tuning of prepared GSR and ST by merging into single dataframe as well as generating TimeNum and renaming and removing of the columns
                                        join_GSR_ST_MOS = pd.merge(EDA_preprocessed_MOS,
                                                                   ST_preprocessed_MOS[
                                                                       ["ST", "ST_filtered", "datetime"]],
                                                                   left_on="datetime", right_on="datetime", how="left")


                                    #st.write("Joined GSR and ST MOS Data", join_GSR_ST_MOS)


                                    join_GSR_ST_MOS.rename(
                                        columns={'datetime': 'time_iso', 'time': 'time_unix', 'EDA': 'GSR_raw', 'EDA_filtered': 'GSR',
                                                 'ST': 'ST_raw', 'ST_filtered': 'ST'}, inplace=True)

                                    SALK_info = join_GSR_ST_MOS[["time_iso", "date", "time_unix", "Vorgang", "Uhrzeit", "Anmerkung"]]

                                    #join_GSR_ST_MOS = join_GSR_ST_MOS.drop(
                                    #    ["date", "time", "Vorgang", "Uhrzeit", "Anmerkung"],
                                    #   axis=1)


                                    join_GSR_ST_MOS['TimeNum'] = join_GSR_ST_MOS["time_iso"].map(pd.Timestamp.timestamp)


                                    #st.write(join_GSR_ST_MOS)

                                    #st.write("Kyriakou et al. MOS Input Data", join_GSR_ST_MOS)

                                    final_MOS_output, extended_MOS_output, mos_identified = mrp.MOS_main_df_SALK(
                                        df=join_GSR_ST_MOS)

                                    st.write("Length of data", len(final_MOS_output))

                                    st.write("Number of MOS Detected: ", mos_identified)

                                    #st.write(len(final_MOS_output[final_MOS_output["detectedMOS"] == 1]))

                                    #st.write("Kyriakou et al. MOS Ouptut", final_MOS_output)

                                    #st.write("Extended Output: ", extended_MOS_output)

                                    # TODO -- rename columns here: GSR_filtered = EDA, ST_filtered = ST, MOS_score = MOS_Score

                                    #st.write(final_MOS_output)
                                    MOS_output_renamed = final_MOS_output.rename(
                                        columns={'GSR_filtered': 'EDA',
                                                 'ST_filtered': 'ST',
                                                 'MOS_score': 'MOS_Score'})

                                    #st.write(MOS_output_renamed)
                                    MOS_output_renamed_rel = MOS_output_renamed[
                                                 ["time_iso", "ID", "Vorgang", "Uhrzeit", "Anmerkung", "TimeNum", "EDA", "ST", "MOS_Score",
                                                  "detectedMOS"]]

                                    #st.write(MOS_output_renamed[
                                    #             ["time_iso", "ID", "Vorgang", "Uhrzeit", "Anmerkung", "TimeNum", "EDA", "ST", "MOS_Score",
                                    #              "detectedMOS"]])

                                    kyriakou_MOS_outputs.append(MOS_output_renamed_rel)


            else:
                pass

            combined_MOS_kyriakou = pd.concat(kyriakou_MOS_outputs)
            st.write("Length of combined MOS Outputs", len(combined_MOS_kyriakou))
            st.write(combined_MOS_kyriakou)
            overall_mos_nr_kyriakou = len(combined_MOS_kyriakou[combined_MOS_kyriakou["detectedMOS"] == 1])
            st.write("Overall Number of MOS Detected: ", overall_mos_nr_kyriakou)

            if st.checkbox("Download Kyriakou et al. 2019 - MOS Analysis:"):
                # download detected MOS based on Kyriakou et al. 2019
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine = "xlsxwriter") as writer:
                    combined_MOS_kyriakou.to_excel(writer, sheet_name = "Sheet1")

                download_excel = st.download_button(label="Download Excel file", data=buffer,
                                                            file_name="MOS-Detection_kyriakou2019.xlsx",
                                                            mime="application/vnd.ms-excel")

            #combined_MOS_kyriakou.to_csv(f"{path}_MOS_output.csv", index=False)

        if moser2023:

            st.header("Stress Detection Output - Moser et al. 2023")

            moser_MOS_outputs = []

            start_time_trim = st.number_input(
                "Number of seconds to trim from start (transient phase) - excluded from the baseline calculation (default = 3 minutes)",
                value=180)
            end_time_trim = st.number_input(
                "Number of seconds to trim from end (when person took off sensor) - excluded from the baseline calculation (default = 30 seconds)",
                value=30)

            MOS_thresh = st.number_input("Please enter the desired MOS threshold: ", value=0.75)


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

                        #st.write(subfolder_path)
                        #if subfolder_path.endswith('.zip'):


                        with zipfile.ZipFile(subfolder_path, 'r') as zipO:
                            file_ls = zipO.namelist()
                            st.write(file_ls)

                            zipO.extractall(path)

                            #st.write(Path.joinpath(path, file_ls))
                            patID = file_ls[0].split("/")[0]

                        #else:

                            st.write("patID which will be set to ID is: ", patID)

                            for filen in file_ls:
                                if 'EDA' in filen and 'MACOSX' not in filen:
                                    path_to_EDA_file = Path.joinpath(path, filen)
                                    #st.write("Path to the EDA file is: ", path_to_EDA_file)

                                    patientPath = Path.joinpath(path, filen.split("/")[0])

                                    #st.write("Path to Patient is patientPath", patientPath)

                                    patientNr = fl.split(".")[1]

                                    st.write("Patient Number:", patientNr)


                                    # TODO - Timestamp Adjustment --> add 1 hour in seconds to Uhrzeit in Zeitenauswertung
                                    patients_to_adjust = ["Pat.18", "Pat.19", "Pat.20",
                                                          "Pat.21", "Pat.22", "Pat.23", "Pat.24", "Pat.25",
                                                          "Pat.26", "Pat.27", "Pat.28", "Pat.29", "Pat.30"]
                                    #patients_to_adjust = [18, 19, 20, 21, 22, 23, 24, 25,
                                    #                      26, 27, 28, 29, 30]

                                    if patID in patients_to_adjust:

                                        st.write("Adjusting Timestamp:")

                                        EDA_labeled_date_extract = merge_data(
                                            signal_path=Path.joinpath(patientPath, "EDA.csv"),
                                            labels_path=Path.joinpath(
                                                patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                    patientNr)),
                                            signal="EDA",
                                        adjust_timestamp = True)

                                        EDA_preprocessed_MOS = e4at.preprocess_EDA(EDA_labeled_date_extract)

                                        EDA_labeled_date_extract["ID"] = patID
                                        # st.write(EDA_labeled_date_extract)

                                        # Prepare ST for MOS generation
                                        ST_labeled_MOS = merge_data(
                                            signal_path=Path.joinpath(patientPath, "TEMP.csv"),
                                            labels_path=Path.joinpath(
                                                patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                    patientNr)),
                                            signal="ST",
                                        adjust_timestamp = True)

                                        ST_preprocessed_MOS = e4at.preprocess_ST(ST_labeled_MOS)

                                        ST_preprocessed_MOS["ID"] = patID

                                        # fine-tuning of prepared GSR and ST by merging into single dataframe as well as generating TimeNum and renaming and removing of the columns
                                        join_GSR_ST_MOS = pd.merge(EDA_preprocessed_MOS,
                                                                   ST_preprocessed_MOS[
                                                                       ["ST", "ST_filtered", "datetime"]],
                                                                   left_on="datetime", right_on="datetime", how="left")

                                        ########## individual file imports for debugging purposes (adjusting timestamps of certain files)
                                        #Zeitenauswertung = pd.read_excel(Path.joinpath(
                                        #    patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                        #        patientNr)))

                                        #st.write("Zeitenauswertung von Patient VOR Adjustment:", Zeitenauswertung)

                                        #Zeitenauswertung = adjust_ts(Zeitenauswertung, time_col = "Uhrzeit")

                                        #EDA_file = e4at.EDA_processing(Path.joinpath(patientPath, "EDA.csv"))
                                        #st.write("EDA file for Patient", patID, " :", EDA_file)

                                    else:

                                        EDA_labeled_date_extract = merge_data(
                                            signal_path=Path.joinpath(patientPath, "EDA.csv"),
                                            labels_path=Path.joinpath(
                                                patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                    patientNr)),
                                            signal="EDA",
                                        adjust_timestamp = False)

                                        EDA_preprocessed_MOS = e4at.preprocess_EDA(EDA_labeled_date_extract)

                                        EDA_labeled_date_extract["ID"] = patID
                                        # st.write(EDA_labeled_date_extract)

                                        # Prepare ST for MOS generation
                                        ST_labeled_MOS = merge_data(
                                            signal_path=Path.joinpath(patientPath, "TEMP.csv"),
                                            labels_path=Path.joinpath(
                                                patientPath, "ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                    patientNr)),
                                            signal="ST",
                                        adjust_timestamp = False)

                                        ST_preprocessed_MOS = e4at.preprocess_ST(ST_labeled_MOS)

                                        ST_preprocessed_MOS["ID"] = patID

                                        # fine-tuning of prepared GSR and ST by merging into single dataframe as well as generating TimeNum and renaming and removing of the columns
                                        join_GSR_ST_MOS = pd.merge(EDA_preprocessed_MOS,
                                                                   ST_preprocessed_MOS[
                                                                       ["ST", "ST_filtered", "datetime"]],
                                                                   left_on="datetime", right_on="datetime", how="left")


                                    #st.write("Joined GSR and ST MOS Data", join_GSR_ST_MOS)


                                    join_GSR_ST_MOS.rename(
                                        columns={'datetime': 'time_iso', 'time': 'time_unix', 'EDA': 'GSR_raw', 'EDA_filtered': 'GSR',
                                                 'ST': 'ST_raw', 'ST_filtered': 'ST'}, inplace=True)



                                    initial_start_time = EDA_labeled_date_extract['datetime'].min()
                                    initial_end_time = EDA_labeled_date_extract['datetime'].max().round('1s')

                                    start_time = initial_start_time + pd.to_timedelta(start_time_trim, "s")
                                    end_time = initial_end_time - pd.to_timedelta(end_time_trim, "s")


                                    SALK_info = join_GSR_ST_MOS[["time_iso", "date", "time_unix", "Vorgang", "Uhrzeit", "Anmerkung"]]

                                    #join_GSR_ST_MOS = join_GSR_ST_MOS.drop(
                                    #    ["date", "time", "Vorgang", "Uhrzeit", "Anmerkung"],
                                    #   axis=1)

                                    join_GSR_ST_MOS['TimeNum'] = join_GSR_ST_MOS["time_iso"].map(pd.Timestamp.timestamp)

                                    #st.write(join_GSR_ST_MOS)

                                    data_prep_f1 = msp_new.derive_GSR_and_ST_features(join_GSR_ST_MOS)
                                    #st.write(data_prep_f1)

                                    # st.write(data_prep_f1)

                                    if "IBI" in data_prep_f1:
                                        data_ready_f1 = msp_new.derive_IBI_and_HRV_features(join_GSR_ST_MOS)
                                    # print(data_ready_f1.head())
                                    else:
                                        data_ready_f1 = data_prep_f1.copy()

                                    # add features for GSR rules
                                    data_ready_f11 = MOS_paper_new.GSR_amplitude_duration_slope(data_ready_f1)

                                    # st.write(data_ready_f11.columns)

                                    # TODO - add start_time_trim and end_time_trim values for trimmed baseline calculation as input
                                    threshold_data = data_ready_f11.set_index("time_iso")[start_time:end_time]

                                    # st.write("Threshold Data", threshold_data)

                                    amplitude_mean = MOS_paper_new.calculate_GSR_ampltiude_baseline(threshold_data)
                                    amplitude_std = MOS_paper_new.calculate_GSR_ampltiude_spread(threshold_data)
                                    # st.write(amplitude_mean, amplitude_std)
                                    duration_mean = MOS_paper_new.calculate_GRS_duration_baseline(threshold_data)
                                    duration_std = MOS_paper_new.calculate_GRS_duration_spread(threshold_data)
                                    # st.write(duration_mean, duration_std)
                                    slope_mean = MOS_paper_new.calculate_GSR_Slope_baseline(threshold_data)
                                    slope_std = MOS_paper_new.calculate_GSR_Slope_spread(threshold_data)

                                    MOS_out_martin = MOS_paper_new.MOS_rules_apply_n(data_ready_f11,
                                                                                     amplitude_mean=amplitude_mean,
                                                                                     amplitude_std=amplitude_std,
                                                                                     slope_mean=slope_mean,
                                                                                     slope_std=slope_std,
                                                                                     MOSpercentage=MOS_thresh)

                                    detected_MOS = MOS_out_martin[MOS_out_martin['MOS_Score'] > MOS_thresh]
                                    df_GSR_rules_met = utilities.check_timestamp_gaps(detected_MOS, duration=10,
                                                                                      col_name="MOS_not_within_10_seconds")

                                    mos_identified = df_GSR_rules_met[
                                        df_GSR_rules_met['MOS_not_within_10_seconds'] == True]

                                    MOS_gsr_and_st_clean = pd.merge(
                                        MOS_out_martin[MOS_out_martin.columns.difference(["detectedMOS"])],
                                        mos_identified[['time_iso', "detectedMOS"]],
                                        on='time_iso', how='left')

                                    MOS_gsr_and_st_clean["detectedMOS"] = MOS_gsr_and_st_clean["detectedMOS"].fillna(0)

                                    #st.write("MOS Subset", MOS_gsr_and_st_clean[MOS_gsr_and_st_clean['detectedMOS'] > 0])

                                    #st.write(MOS_gsr_and_st_clean)

                                    number_of_mos = len(MOS_gsr_and_st_clean[MOS_gsr_and_st_clean['detectedMOS'] > 0])

                                    st.write("Length of data", len(MOS_gsr_and_st_clean))

                                    st.write("Number of MOS Detected: ", number_of_mos)

                                    MOS_output_renamed_moser = MOS_gsr_and_st_clean.rename(
                                        columns={'GSR': 'EDA'})

                                    MOS_output_renamed_moser_rel = MOS_output_renamed_moser[["time_iso", "ID", "Vorgang", "Uhrzeit", "Anmerkung", "TimeNum", "EDA", "ST", "MOS_Score", "detectedMOS"]]

                                    #st.write("Number of MOS detected based on Moser et al. (2023): **{}**".format(
                                    #    number_of_mos))


                                    # TODO -- rename columns here: GSR = EDA, ST = ST, MOS_Score = MOS_score


                                    moser_MOS_outputs.append(MOS_output_renamed_moser_rel)

                                # initial_start_time = EDA_labeled_date_extract['datetime'].min()
                                # initial_end_time = EDA_labeled_date_extract['datetime'].max().round('1s')


            else:
                pass

            combined_MOS_moser = pd.concat(moser_MOS_outputs)
            st.write("Length of combined MOS Outputs", len(combined_MOS_moser))
            st.write(combined_MOS_moser)
            overall_mos_nr_moser = len(
                combined_MOS_moser[combined_MOS_moser["detectedMOS"] == 1])
            st.write("Overall Number of MOS Detected: ", overall_mos_nr_moser)



            if st.checkbox("Download Moser et al. 2023 - MOS Analysis:"):
                # download detected MOS based on Kyriakou et al. 2019
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine = "xlsxwriter") as writer:
                    combined_MOS_moser.to_excel(writer, sheet_name = "Sheet1")

                download_excel = st.download_button(label="Download Excel file", data=buffer,
                                                            file_name="MOS-Detection_moser2023.xlsx",
                                                            mime="application/vnd.ms-excel")

            # writes output to .csv file located in 'src' -- name is 'pages_MOS_output.csv'
            #combined_MOS_moser.to_csv(f"{path}_MOS_output.csv", index=False)


    except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError, sqlite3.OperationalError):

        print("\nRng{}: Unable to process your request ! Something wrong in the SALK E4 zip file section".format(

            random.randint(0, 50)))

    finally:

        st.info("Finally executed")


    #st.write("Result List of EDA files: ", path_to_EDA_file)



