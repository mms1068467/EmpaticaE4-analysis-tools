import datetime
import sqlite3
import time
from zipfile import ZipFile
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
import shutil

import streamlit as st
import math
import numpy as np
import pandas as pd

import os
import pathlib

import random

import plotly.express as px
import plotly.graph_objects as go

#from HumanSensing_Preprocessing import process_zip_files as pzf
import E4_Analysis_tools as e4at
from MOS_Detection import MOS_rules_paper_verified as mrp
from MOS_Detection import MOS_signal_preparation_verified as msp_new
import MOS_Detection.MOS_rules_NEW as MOS_paper_new
from HumanSensing_Preprocessing import utilities

##### Functions
try:
    # temporarily saves the file
    def save_uploadedfile(uploaded_file, path: str):
        with open(os.path.join(path, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        # return st.success("Temporarily saved file: {} to {}".format(uploaded_file.name, path))


    def add_groundtruth_mos(fig, final_MOS_output):

        MOS_detected = final_MOS_output[~final_MOS_output['MOS_score'].isna()]

        for i in MOS_detected.index:
            if MOS_detected.MOS_score[i] > 75:
                fig.add_vline(MOS_detected['time_iso'][i], line_dash='dash', line_color='red')
                # fig.update_layout(title = "Preprocessed signals plot with MOS")

        return fig


    #### Caching the plot functions to (slightly) increase performance
    @st.cache
    def merge_data(signal_path, labels_path, signal):

        return_signal = e4at.merge_data(signal_path=signal_path, labels_path=labels_path, signal=signal)

        return return_signal


    @st.cache(allow_output_mutation=True)
    def plot_ACC(signal):

        return_plot = e4at.plot_ACC(signal)

        return return_plot


    @st.cache(allow_output_mutation=True)
    def plot_BVP(signal, raw=True):

        return_plot = e4at.plot_BVP(signal, raw)

        return return_plot

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



    #@st.cache
    #def open_and_extract_zip_pat(path, uploaded_E4_zip_folder):

    #    extract_zip = pzf.open_and_extract_zip_pat(path, uploaded_E4_zip_folder)

    #    return extract_zip


    #@st.cache
    #def find_all_csv_xslx_files(read_zip_files):

    #    find_csv_xslx = pzf.find_all_csv_xslx_files(read_zip_files)

    #    return find_csv_xslx

    #### Page setup

    st.set_page_config(
        page_title="SALK data processing",
        page_icon=None,
        layout="wide"
    )

    st.title("SALK Data Visualization Dashboard")

    expander_project_description = st.expander("Click Here to learn more about the project")
    expander_bug_description = st.expander("Click Here in case a bug appears")
    with expander_project_description:
        st.info("""
            SALK Data Visualization Dashboard is created to bring forth the processing capabilities of Empatica E4 biometric signals, generating Moments of Stress (MOS), applying a Butterworth filter and graphicaly displaying the results \n
            -------------------------------------------------------------------------------------
    
            This Steamlit Application is a platform to analyze biometric data that is recorded by the Empatica E4 wristband. Empatica data is downloaded as a .zip file and contains individual biometric signals, recorded at their respective sampling frequency, and a timestamp in unix format, indicating the starting time of the recordings.
    
            The app allows users to upload the .zip file containing the individual sensor recordings, and analyze them through a visual inspection.
            """)

    global_working_folder_path = None
    # If neccessary, add an users local path in order to use and store the files from the app
    # path = st.text_input("Please enter the path where you want to store the project data INCLUDING a '/' at the end and press Enter (Example: C:/Users/projects/data/)" )
    path = Path(__file__).parent.resolve()
    st.markdown("---")

    #### File uploader
    st.header("Drag and drop zip folder containing individual signals")

    uploaded_E4_zip_folder = st.file_uploader("Drag and drop your SALK E4 zip folder(s) here...", type=["zip", "7z"],
                                              accept_multiple_files=False)
    st.info("Upload zip folder")

    #### Main, branching part of the application as soon as the zip is uploaded
    if uploaded_E4_zip_folder is not None:
        try:

            ####UPLOAD AND READ ZIP FOLDER
            # save locally to access it
            save_uploadedfile(uploaded_file=uploaded_E4_zip_folder, path=path)
            full_file_name = uploaded_E4_zip_folder.name.split(".")[0] + "." + uploaded_E4_zip_folder.name.split(".")[1]
            saved_folder_path = str(path) + "\\" + full_file_name
            global_working_folder_path = saved_folder_path
            read_zip_files = open_and_extract_zip_pat(path, uploaded_E4_zip_folder)
            st.success("Temporarily saved folder: {} to {}".format(full_file_name, path))
            st.info("Note: please select (and plot) two or more individual signals before merging them.. ")
            # create a signal path list to access them
            create_csv_xlsx_list = find_all_csv_xslx_files(read_zip_files)

            # fetch signal directory path and pat number
            # individual_signal_path = create_csv_xlsx_list[0].rsplit("\\", 1)[0]
            individual_signal_path = os.path.join(read_zip_files, read_zip_files.split('\\')[-1])
            pat_number_code = individual_signal_path.split("/")[-1].split(".")[-1]

            try:

                # sidebar time filtering
                st.sidebar.title("Select signal time range")
                EDA_labeled_date_extract = merge_data(signal_path=os.path.join(individual_signal_path + "/EDA.csv"),
                                                     labels_path=os.path.join(
                                                         individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                             pat_number_code)),
                                                     signal="EDA")

                initial_start_time = EDA_labeled_date_extract['datetime'].min()
                initial_end_time = EDA_labeled_date_extract['datetime'].max().round('1s')

                duration = pd.to_datetime(EDA_labeled_date_extract['datetime'].max()) - pd.to_datetime(
                    EDA_labeled_date_extract['datetime'].min())

                min_dur = duration.seconds - duration.seconds
                max_dur = duration.seconds

                double_ended_seconds_slider_filter = st.sidebar.slider("Seconds after start of recording to display",
                                                                       value=[duration.seconds - duration.seconds,
                                                                              duration.seconds])
                #double_ended_seconds_slider_filter = st.sidebar.slider("Seconds after start of recording to display",
                #                                                       min_value = min_dur,
                #                                                       max_value = max_dur,
                #                                                       format = "%H:%M:%S")


                st.sidebar.write("Duration of recording: \t ", " \t => \t",
                                 time.strftime("%H:%M:%S", time.gmtime(duration.seconds)))

                # double_ended_seconds_slider_filter = st.sidebar.slider("Seconds after start of recording to display", min_value = start_date, value= end_date, max_value= end_date, format=format)
                start_time = EDA_labeled_date_extract['datetime'].min() + datetime.timedelta(
                    seconds=double_ended_seconds_slider_filter[0])
                end_time = EDA_labeled_date_extract['datetime'].min() + datetime.timedelta(
                    seconds=double_ended_seconds_slider_filter[1])


                #start_time = st.sidebar.slider("Start Time", value = min_dur, format = time.strftime("%H:%M:%S"))

                #end_time = st.sidebar.slider("End Time", value = max_dur, format = time.strftime("%H:%M:%S"))


                EDA_labeled = EDA_labeled_date_extract[
                    (EDA_labeled_date_extract['datetime'] >= start_time) & (EDA_labeled_date_extract['datetime'] <= end_time)]

                #st.write(EDA_labeled_date_extract)


                try:

                    st.markdown("---")
                    st.subheader("Filtered EDA Data")

                    EDA_butterworth_pass_filter = st.number_input('Butter filter order', value=1,
                                                                  key="edabutterfilter")
                    EDA_low_pass_filter = st.number_input('Low-pass cutoff frequency', value=0.50,
                                                          step=0.01,
                                                          format="%.2f", key="edalowpassfilter")
                    EDA_high_pass_filter = st.number_input('High-pass cutoff frequency', value=0.0025,
                                                           step=0.0001,
                                                           format="%.4f", key="edahighpassfilter")

                    EDA_preprocessed = e4at.preprocess_EDA(EDA_labeled, order=EDA_butterworth_pass_filter,
                                                           lowpass_cutoff_frequency=EDA_low_pass_filter,
                                                           highpass_cutoff_frequency=EDA_high_pass_filter)

                    EDAfigureFiltered = e4at.plot_EDA(EDA_preprocessed, raw=False)

                    st.plotly_chart(EDAfigureFiltered, use_container_width=True)
                except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError,
                        sqlite3.OperationalError):
                    st.error("""ERROR: looks like some of filtering values are out of range. Please adjust them accordingly: 
                                            \n Butter filter order: => 0 
                                            \nLow-pass and High-pass cutoff frequency: 0.001 - 0.999 
                                                """)

                raw_gsr_check = st.checkbox("Display Raw GSR Signal:")
                if raw_gsr_check:
                    EDAfigureRaw = e4at.plot_EDA(EDA_labeled, raw=True)

                    st.plotly_chart(EDAfigureRaw, use_container_width=True)


                st.sidebar.markdown("---")
                st.sidebar.title("MOS Detection")
                st.sidebar.markdown("Select MOS Algorithm to apply:")

                kyriakou2019 = st.sidebar.checkbox("Apply MOS Algorithm according to Kyriakou et al. (2019)")
                moser2023 = st.sidebar.checkbox("Apply individual-oriented MOS Algorithm (new)")


                st.sidebar.title("Visualization of other Signals")
                checkboxST = st.sidebar.checkbox("Skin Temperature (ST)")
                checkboxACC = st.sidebar.checkbox("Acceleration (ACC)")
                checkboxBVP = st.sidebar.checkbox("Blood Volume Pressure (BVP)")
                checkboxHR = st.sidebar.checkbox("Heart Rate (HR)")
                checkboxIBI = st.sidebar.checkbox("Interbeat Interval (IBI)")
                checkboxHRV = st.sidebar.checkbox("Heart Rate Variability (HRV)")


                if checkboxST:
                    try:
                        st.markdown("---")
                        st.subheader("ST signal plot")
                        ST_labeled = merge_data(signal_path=os.path.join(individual_signal_path + "/TEMP.csv"),
                                                labels_path=os.path.join(
                                                    individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                        pat_number_code)),
                                                signal="ST")
                        ST_labeled = ST_labeled[
                            (ST_labeled['datetime'] >= start_time) & (ST_labeled['datetime'] <= end_time)]

                        # st.dataframe(ST_labeled)

                        checkboxSTraw = st.checkbox("Plot ST raw")

                        if checkboxSTraw:
                            # st.dataframe(ST_labeled)

                            STfigure = e4at.plot_ST(ST_labeled)

                            st.plotly_chart(STfigure, use_container_width=True)

                        checkboxSTfiltered = st.checkbox("Plot ST filtered")

                        if checkboxSTfiltered:
                            try:
                                ST_butterworth_pass_filter = st.number_input('Butter filter order', value=2,
                                                                             key="stbutterfilter")
                                ST_low_pass_filter = st.number_input('Low-pass cutoff frequency', value=0.050,
                                                                     step=0.001,
                                                                     format="%.3f", key="stlowpassfilter")
                                ST_high_pass_filter = st.number_input('High-pass cutoff frequency', value=0.005,
                                                                      step=0.001,
                                                                      format="%.3f", key="sthighpassfilter")

                                ST_preprocessed = e4at.preprocess_ST(ST_labeled, order=ST_butterworth_pass_filter,
                                                                     lowpass_cutoff_frequency=ST_low_pass_filter,
                                                                     highpass_cutoff_frequency=ST_high_pass_filter)
                                STfigureFiltered = e4at.plot_ST(ST_preprocessed, raw=False)

                                st.plotly_chart(STfigureFiltered, use_container_width=True)
                            except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError,
                                    sqlite3.OperationalError):
                                st.error("""ERROR: looks like some of filtering values are out of range. Please adjust them accordingly: 
                                \n Butter filter order: => 0 
                                \nLow-pass and High-pass cutoff frequency: 0.001 - 0.999 
                                """)
                    except(FileNotFoundError):
                        st.error("ERROR: Looks like the TEMP.csv does not exist")

                if checkboxACC:
                    try:
                        st.markdown("---")
                        st.subheader("ACC signal plot:")
                        st.info("Accelerometers are devices that measure acceleration, which is the rate of change of the velocity of an object. They measure in meters per second squared (m/s2) or in G-forces (g).")

                        ACC_labeled = merge_data(signal_path=os.path.join(individual_signal_path + "/ACC.csv"),
                                                 labels_path=os.path.join(
                                                     individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                         pat_number_code)),
                                                 signal="ACC")
                        ACC_labeled = ACC_labeled[
                            (ACC_labeled['datetime'] >= start_time) & (ACC_labeled['datetime'] <= end_time)]


                        ACCfigure = plot_ACC(ACC_labeled)

                        st.plotly_chart(ACCfigure, use_container_width=True)

                    except(FileNotFoundError):
                        st.error("ERROR: Looks like the ACC.csv does not exist")

                if checkboxBVP:
                    try:
                        st.markdown("---")
                        st.subheader("BVP signal plot")

                        BVP_labeled = merge_data(signal_path=os.path.join(individual_signal_path + "/BVP.csv"),
                                                 labels_path=os.path.join(
                                                     individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                         pat_number_code)),
                                                 signal="BVP")
                        BVP_labeled = BVP_labeled[
                            (BVP_labeled['datetime'] >= start_time) & (BVP_labeled['datetime'] <= end_time)]

                        checkboxBVPraw = st.checkbox("Plot BVP raw")

                        if checkboxBVPraw:
                            BVPfigure = plot_BVP(BVP_labeled)

                            st.plotly_chart(BVPfigure, use_container_width=True)

                        checkboxBVPfiltered = st.checkbox("Plot BVP filtered")

                        if checkboxBVPfiltered:
                            try:
                                BVP_butterworth_pass_filter = st.number_input('Butter filter order', value=4,
                                                                              key="bvpbutterfilter")
                                BVP_low_pass_filter = st.number_input('Low-pass cutoff frequency', value=0.36,
                                                                      step=0.01,
                                                                      format="%.3f", key="bvplowpassfilter")
                                BVP_high_pass_filter = st.number_input('High-pass cutoff frequency', value=0.01,
                                                                       step=0.01,
                                                                       format="%.3f", key="bvphighpassfilter")

                                BVP_preprocessed = e4at.preprocess_BVP(BVP_labeled,
                                                                       low_order=BVP_butterworth_pass_filter,
                                                                       lowpass_cutoff_frequency=BVP_low_pass_filter,
                                                                       highpass_cutoff_frequency=BVP_high_pass_filter)

                                BVPfigureFiltered = plot_BVP(BVP_preprocessed, raw=False)

                                st.plotly_chart(BVPfigureFiltered, use_container_width=True)
                            except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError,
                                    sqlite3.OperationalError):
                                st.error("""ERROR: looks like some of filtering values are out of range. Please adjust them accordingly: 
                                \n Butter filter order: => 0 
                                \nLow-pass and High-pass cutoff frequency: 0.001 - 0.999 
                                """)
                    except(FileNotFoundError):
                        st.error("ERROR: Looks like the BVP.csv does not exist")

                if checkboxHR:
                    try:
                        st.markdown("---")
                        st.subheader("HR signal plot")
                        HR_labeled = e4at.merge_data(signal_path=os.path.join(individual_signal_path + "/HR.csv"),
                                                     labels_path=os.path.join(
                                                         individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                             pat_number_code)),
                                                     signal="HR")
                        HR_labeled = HR_labeled[
                            (HR_labeled['datetime'] >= start_time) & (HR_labeled['datetime'] <= end_time)]
                        HRfigure = e4at.plot_HR(HR_labeled)

                        st.plotly_chart(HRfigure, use_container_width=True)

                    except(FileNotFoundError):
                        st.error("ERROR: Looks like the HR.csv does not exist")

                if checkboxIBI:

                    try:
                        st.markdown("---")
                        st.subheader("IBI signal plot")
                        IBI_labeled = e4at.merge_data(signal_path=os.path.join(individual_signal_path + "/IBI.csv"),
                                                      labels_path=os.path.join(
                                                          individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                              pat_number_code)),
                                                      signal="IBI")
                        IBI_labeled = IBI_labeled[
                            (IBI_labeled['datetime'] >= start_time) & (IBI_labeled['datetime'] <= end_time)]

                        IBIfigure = e4at.plot_IBI(IBI_labeled)

                        st.plotly_chart(IBIfigure, use_container_width=True)

                    except(FileNotFoundError):
                        st.error("ERROR: Looks like the IBI.csv does not exist")

                if checkboxHRV:
                    try:
                        st.markdown("---")
                        st.subheader("HRV signal plot")
                        IBI_labeled = e4at.merge_data(signal_path=os.path.join(individual_signal_path + "/IBI.csv"),
                                                      labels_path=os.path.join(
                                                          individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                              pat_number_code)),
                                                      signal="IBI")
                        IBI_labeled = IBI_labeled[
                            (IBI_labeled['datetime'] >= start_time) & (IBI_labeled['datetime'] <= end_time)]

                        HRV_labeled = e4at.get_HRV_from_IBI(IBI_labeled)
                        HRV_labeled = HRV_labeled[
                            (HRV_labeled['datetime'] >= start_time) & (HRV_labeled['datetime'] <= end_time)]

                        HRVfigure = e4at.plot_HRV(HRV_labeled)

                        st.plotly_chart(HRVfigure, use_container_width=True)
                    except(FileNotFoundError):
                        st.error(
                            "ERROR: Looks like the IBI.csv does not exist or something is wrong with deriving HRV from IBI")

                st.header('Stress Detection Output')

                if kyriakou2019:

                    # Prepare EDA (i.e. GSR) for MOS generation
                    EDA_labeled_MOS = e4at.merge_data(
                        signal_path=os.path.join(individual_signal_path + "/EDA.csv"),
                        labels_path=os.path.join(
                            individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                pat_number_code)),
                        signal="EDA")
                    EDA_labeled_MOS = EDA_labeled_MOS[
                        (EDA_labeled_MOS['datetime'] >= start_time) & (EDA_labeled_MOS['datetime'] <= end_time)]
                    EDA_preprocessed_MOS = e4at.preprocess_EDA(EDA_labeled_MOS)

                    # Prepare ST for MOS generation
                    ST_labeled_MOS = merge_data(signal_path=os.path.join(individual_signal_path + "/TEMP.csv"),
                                                labels_path=os.path.join(
                                                    individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                        pat_number_code)),
                                                signal="ST")
                    ST_labeled_MOS = ST_labeled_MOS[
                        (ST_labeled_MOS['datetime'] >= start_time) & (ST_labeled_MOS['datetime'] <= end_time)]
                    ST_preprocessed_MOS = e4at.preprocess_ST(ST_labeled_MOS)

                    # fine-tuning of prepared GSR and ST by merging into single dataframe as well as generating TimeNum and renaming and removing of the columns
                    join_GSR_ST_MOS = pd.merge(EDA_preprocessed_MOS,
                                               ST_preprocessed_MOS[["ST", "ST_filtered", "datetime"]],
                                               left_on="datetime", right_on="datetime", how="left")
                    join_GSR_ST_MOS.rename(
                        columns={'datetime': 'time_iso', 'EDA': 'GSR_raw', 'EDA_filtered': 'GSR',
                                 'ST': 'ST_raw', 'ST_filtered': 'ST'}, inplace=True)
                    join_GSR_ST_MOS = join_GSR_ST_MOS.drop(["date", "time", "Vorgang", "Uhrzeit", "Anmerkung"],
                                                           axis=1)
                    join_GSR_ST_MOS['TimeNum'] = join_GSR_ST_MOS["time_iso"].map(pd.Timestamp.timestamp)
                    final_MOS_output, extended_MOS_output, mos_identified = mrp.MOS_main_df(df=join_GSR_ST_MOS)

                    ####### Visualization of combined Signals:

                    figure_merge = go.Figure()
                    dataframe_merge = pd.DataFrame()
                    # dataframe_merge_datetime = dataframe_merge.join(ST_labeled_date_extract['datetime'])
                    dataframe_merge['datetime'] = EDA_labeled_date_extract['datetime']

                    # list for Y-axis min and max values so the MOS stress lines can be plotted in according Y value range
                    MOS_ymin_list = []
                    MOS_ymax_list = []

                    figure_merge.add_trace(
                        go.Scatter(x=EDA_preprocessed['datetime'], y=EDA_preprocessed["EDA_filtered"],
                                   line=dict(color="blue"),
                                   name="Filtered Electrodermal Activity (EDA) in mircoSiemens"))

                    MOS_ymin_list.append(EDA_preprocessed['EDA_filtered'].min())
                    MOS_ymax_list.append(EDA_preprocessed['EDA_filtered'].max())

                    st.write("Number of MOS detected based on Kyriakou et al. (2019): **{}**".format(mos_identified))


                    # plotting vertical lines to the existing merged signals plot
                    MOS_figure = add_groundtruth_mos(figure_merge, final_MOS_output)
                    st.plotly_chart(MOS_figure, use_container_width=True)

                #else:
                #    st.plotly_chart(figure_merge, use_container_width=True)

                if moser2023:

                    #st.write("The initial start time is:", initial_start_time)
                    #st.write("The initial end time is:", initial_end_time)

                    start_time_trim = st.number_input("Number of seconds to trim from start (transient phase) - excluded from the baseline calculation (default = 3 minutes)",
                                                      value=180)
                    end_time_trim = st.number_input("Number of seconds to trim from end (when person took off sensor) - excluded from the baseline calculation (default = 30 seconds)",
                                                    value=30)

                    start_time = initial_start_time + pd.to_timedelta(start_time_trim, "s")
                    end_time = initial_end_time - pd.to_timedelta(end_time_trim, "s")

                    #st.write("Start time + start trim time:", initial_start_time + pd.to_timedelta(start_time_trim, "s"))
                    #st.write("End time - end trim time:", initial_end_time - pd.to_timedelta(end_time_trim, "s"))

                    st.info("New, individualized Algorithm")
                    # Prepare EDA (i.e. GSR) for MOS generation
                    EDA_labeled_MOS = e4at.merge_data(
                        signal_path=os.path.join(individual_signal_path + "/EDA.csv"),
                        labels_path=os.path.join(
                            individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                pat_number_code)),
                        signal="EDA")
                    EDA_labeled_MOS = EDA_labeled_MOS[
                        (EDA_labeled_MOS['datetime'] >= start_time) & (EDA_labeled_MOS['datetime'] <= end_time)]
                    EDA_preprocessed_MOS = e4at.preprocess_EDA(EDA_labeled_MOS)

                    # Prepare ST for MOS generation
                    ST_labeled_MOS = merge_data(signal_path=os.path.join(individual_signal_path + "/TEMP.csv"),
                                                labels_path=os.path.join(
                                                    individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                        pat_number_code)),
                                                signal="ST")
                    ST_labeled_MOS = ST_labeled_MOS[
                        (ST_labeled_MOS['datetime'] >= start_time) & (ST_labeled_MOS['datetime'] <= end_time)]
                    ST_preprocessed_MOS = e4at.preprocess_ST(ST_labeled_MOS)

                    # fine-tuning of prepared GSR and ST by merging into single dataframe as well as generating TimeNum and renaming and removing of the columns
                    join_GSR_ST_MOS = pd.merge(EDA_preprocessed_MOS,
                                               ST_preprocessed_MOS[["ST", "ST_filtered", "datetime"]],
                                               left_on="datetime", right_on="datetime", how="left")
                    join_GSR_ST_MOS.rename(
                        columns={'datetime': 'time_iso', 'EDA': 'GSR_raw', 'EDA_filtered': 'GSR',
                                 'ST': 'ST_raw', 'ST_filtered': 'ST'}, inplace=True)
                    join_GSR_ST_MOS = join_GSR_ST_MOS.drop(["date", "time", "Vorgang", "Uhrzeit", "Anmerkung"],
                                                           axis=1)
                    join_GSR_ST_MOS['TimeNum'] = join_GSR_ST_MOS["time_iso"].map(pd.Timestamp.timestamp)

                    #st.write(join_GSR_ST_MOS)

                    data_prep_f1 = msp_new.derive_GSR_and_ST_features(join_GSR_ST_MOS)

                    #st.write(data_prep_f1)

                    if "IBI" in data_prep_f1:
                        data_ready_f1 = msp_new.derive_IBI_and_HRV_features(join_GSR_ST_MOS)
                    # print(data_ready_f1.head())
                    else:
                        data_ready_f1 = data_prep_f1.copy()

                    # add features for GSR rules
                    data_ready_f11 = MOS_paper_new.GSR_amplitude_duration_slope(data_ready_f1)

                    #st.write(data_ready_f11.columns)

                    # TODO - add start_time_trim and end_time_trim values for trimmed baseline calculation as input
                    threshold_data = data_ready_f11.set_index("time_iso")[start_time:end_time]

                    #st.write("Threshold Data", threshold_data)

                    amplitude_mean = MOS_paper_new.calculate_GSR_ampltiude_baseline(threshold_data)
                    amplitude_std = MOS_paper_new.calculate_GSR_ampltiude_spread(threshold_data)
                    #st.write(amplitude_mean, amplitude_std)
                    duration_mean = MOS_paper_new.calculate_GRS_duration_baseline(threshold_data)
                    duration_std = MOS_paper_new.calculate_GRS_duration_spread(threshold_data)
                    #st.write(duration_mean, duration_std)
                    slope_mean = MOS_paper_new.calculate_GSR_Slope_baseline(threshold_data)
                    slope_std = MOS_paper_new.calculate_GSR_Slope_spread(threshold_data)
                    #st.write(slope_mean, slope_std)

                    ##### Skin Temperature Stats
                    #ST_mean, ST_median, ST_variance, ST_std = MOS_paper_new.calc_ST_rule_statistics(data_ready_f11,
                    #                                                                  trim_time=True,
                    #                                                                  start_mins=4,
                    #                                                                  end_mins=1)

                    MOS_thresh = st.number_input("Please enter the desired MOS threshold: ", value = 1.25)

                    MOS_out_martin = MOS_paper_new.MOS_rules_apply_n(data_ready_f11,
                                                                     amplitude_mean = amplitude_mean,
                                                                     amplitude_std = amplitude_std,
                                                                     slope_mean = slope_mean,
                                                                     slope_std = slope_std,
                                                                     MOSpercentage = MOS_thresh)

                    detected_MOS = MOS_out_martin[MOS_out_martin['MOS_Score'] > MOS_thresh]
                    df_GSR_rules_met = utilities.check_timestamp_gaps(detected_MOS, duration=10,
                                                                      col_name="MOS_not_within_10_seconds")

                    mos_identified = df_GSR_rules_met[df_GSR_rules_met['MOS_not_within_10_seconds'] == True]

                    MOS_gsr_and_st_clean = pd.merge(MOS_out_martin[MOS_out_martin.columns.difference(["detectedMOS"])],
                                                    mos_identified[['time_iso', "detectedMOS"]],
                                                    on='time_iso', how='left')

                    st.write(MOS_gsr_and_st_clean[MOS_gsr_and_st_clean['detectedMOS'] > 0])

                    MOS_gsr_and_st_clean["detectedMOS"] = MOS_gsr_and_st_clean["detectedMOS"].replace(np.nan, 0)

                    number_of_mos = len(MOS_gsr_and_st_clean[MOS_gsr_and_st_clean['detectedMOS'] > 0])
                    st.write("Number of MOS detected based on Moser et al. (2023): **{}**".format(number_of_mos))

                    figure_merge_moser = go.Figure()
                    dataframe_merge = pd.DataFrame()
                    # dataframe_merge_datetime = dataframe_merge.join(ST_labeled_date_extract['datetime'])
                    dataframe_merge['datetime'] = EDA_labeled_date_extract['datetime']

                    # list for Y-axis min and max values so the MOS stress lines can be plotted in according Y value range
                    MOS_ymin_list = []
                    MOS_ymax_list = []

                    figure_merge_moser.add_trace(
                        go.Scatter(x=EDA_preprocessed['datetime'], y=EDA_preprocessed["EDA_filtered"],
                                   line=dict(color="blue"),
                                   name="Filtered Electrodermal Activity (EDA) in mircoSiemens"))

                    MOS_ymin_list.append(EDA_preprocessed['EDA_filtered'].min())
                    MOS_ymax_list.append(EDA_preprocessed['EDA_filtered'].max())

                    # plotting vertical lines to the existing merged signals plot
                    for i in MOS_gsr_and_st_clean.index:
                        if MOS_gsr_and_st_clean.detectedMOS[i] > 0:
                            figure_merge_moser.add_vline(MOS_gsr_and_st_clean['time_iso'][i], line_dash='dash', line_color='red')
                    st.plotly_chart(figure_merge_moser, use_container_width=True)




                # merges a trace for each given signal and records its Y min and max values
                if checkboxST:
                    dataframe_merge = pd.merge(dataframe_merge, ST_labeled[["ST", "datetime"]],
                                               left_on="datetime", right_on="datetime", how="left")

                    if checkboxSTraw:
                        figure_merge.add_trace(
                            go.Scatter(x=ST_labeled['datetime'], y=ST_labeled["ST"], line=dict(color="orange"),
                                       name="Raw Skin Temperature (ST) in ° C"))

                        MOS_ymin_list.append(ST_labeled['ST'].min())
                        MOS_ymax_list.append(ST_labeled['ST'].max())

                    if checkboxSTfiltered:
                        figure_merge.add_trace(
                            go.Scatter(x=ST_labeled['datetime'], y=ST_preprocessed["ST_filtered"],
                                       line=dict(color="orange"), name="Filtered Temperature (ST) in ° C"))

                        MOS_ymin_list.append(ST_preprocessed['ST_filtered'].min())
                        MOS_ymax_list.append(ST_preprocessed['ST_filtered'].max())

                if checkboxACC:
                    figure_merge.add_trace(
                        go.Scatter(x=ACC_labeled["datetime"], y=ACC_labeled["X-axis"], line=dict(color="red"),
                                   name='X-Axis Acceleration in g'))
                    figure_merge.add_trace(
                        go.Scatter(x=ACC_labeled['datetime'], y=ACC_labeled['Y-axis'], line=dict(color='green'),
                                   name='X-Axis Acceleration in g'))
                    figure_merge.add_trace(
                        go.Scatter(x=ACC_labeled['datetime'], y=ACC_labeled['Z-axis'], line=dict(color='blue'),
                                   name='Z-Axis Acceleration in g'))

                    MOS_ymin_list.append(ACC_labeled['X-axis'].min())
                    MOS_ymax_list.append(ACC_labeled['X-axis'].max())
                    MOS_ymin_list.append(ACC_labeled['Y-axis'].min())
                    MOS_ymax_list.append(ACC_labeled['Y-axis'].max())
                    MOS_ymin_list.append(ACC_labeled['Z-axis'].min())
                    MOS_ymax_list.append(ACC_labeled['Z-axis'].max())

                if checkboxBVP:

                    if checkboxBVPraw:
                        figure_merge.add_trace(go.Scatter(x=BVP_labeled['datetime'], y=BVP_labeled["BVP"],
                                                          line=dict(color="purple"),
                                                          name="Raw Blood Volume Pressure (BVP)"))

                        MOS_ymin_list.append(BVP_labeled['BVP'].min())
                        MOS_ymax_list.append(BVP_labeled['BVP'].max())

                    if checkboxBVPfiltered:
                        figure_merge.add_trace(
                            go.Scatter(x=BVP_preprocessed['datetime'], y=BVP_preprocessed["BVP_filtered"],
                                       line=dict(color="firebrick"),
                                       name="Filtered Blood Volume Pressure (BVP)"))

                        MOS_ymin_list.append(BVP_preprocessed['BVP_filtered'].min())
                        MOS_ymax_list.append(BVP_preprocessed['BVP_filtered'].max())

                if checkboxHR:
                    figure_merge.add_trace(
                        go.Scatter(x=HR_labeled['datetime'], y=HR_labeled["HR"], line=dict(color="red"),
                                   name="Heart Rate (HR) in BPM"))

                    MOS_ymin_list.append(HR_labeled['HR'].min())
                    MOS_ymax_list.append(HR_labeled['HR'].max())

                if checkboxIBI:
                    dataframe_merge = pd.merge(dataframe_merge, IBI_labeled[["IBI", "datetime"]],
                                               left_on="datetime", right_on="datetime", how="left")

                    figure_merge.add_trace(
                        go.Scatter(x=IBI_labeled['datetime'], y=IBI_labeled["IBI"], line=dict(color="green"),
                                   name="Interbeat Interval (IBI) in Seconds"))

                    MOS_ymin_list.append(IBI_labeled['IBI'].min())
                    MOS_ymax_list.append(IBI_labeled['IBI'].max())

                    if checkboxHRV:
                        dataframe_merge = pd.merge(dataframe_merge, HRV_labeled[["HRV", "datetime"]],
                                                   left_on="datetime", right_on="datetime", how="left")

                        figure_merge.add_trace(
                            go.Scatter(x=HRV_labeled['datetime'], y=HRV_labeled["HRV"], line=dict(color="red"),
                                       name="Heart Rate Variability (HRV) in Seconds"))

                        MOS_ymin_list.append(HRV_labeled['HRV'].min())
                        MOS_ymax_list.append(HRV_labeled['HRV'].max())

                # assigning the Y-axis min and max values
                dmin = min(MOS_ymin_list)
                dmax = max(MOS_ymax_list)

                labels = EDA_labeled[~EDA_labeled["Vorgang"].isna()]
                for index in labels.index:
                    figure_merge.add_trace(
                        go.Scatter(x=[EDA_labeled['datetime'][index], EDA_labeled['datetime'][index]],
                                   y=[dmin, dmax], mode="lines", line=dict(color='black'),
                                   name=f"Stress section {EDA_labeled['Vorgang'][index]}"))

                # computes the MOS by timedate in data and plots it
                if checkboxST:
                    labels = ST_labeled[~ST_labeled["Vorgang"].isna()]

                    for index in labels.index:
                        figure_merge.add_trace(
                            go.Scatter(x=[ST_labeled['datetime'][index], ST_labeled['datetime'][index]],
                                       y=[dmin, dmax], mode="lines", line=dict(color='black'),
                                       name=f"Stress section {ST_labeled['Vorgang'][index]}"))

                elif checkboxACC:
                    labels = ACC_labeled[~ACC_labeled["Vorgang"].isna()]
                    for index in labels.index:
                        figure_merge.add_trace(
                            go.Scatter(x=[ACC_labeled['datetime'][index], ACC_labeled['datetime'][index]],
                                       y=[dmin, dmax], mode="lines", line=dict(color='black'),
                                       name=f"Stress section {ACC_labeled['Vorgang'][index]}"))

                elif checkboxBVP:
                    labels = BVP_labeled[~BVP_labeled["Vorgang"].isna()]
                    for index in labels.index:
                        figure_merge.add_trace(
                            go.Scatter(x=[BVP_labeled['datetime'][index], BVP_labeled['datetime'][index]],
                                       y=[dmin, dmax], mode="lines", line=dict(color='black'),
                                       name=f"Stress section {BVP_labeled['Vorgang'][index]}"))

                elif checkboxHR:
                    labels = HR_labeled[~HR_labeled["Vorgang"].isna()]

                    for index in labels.index:
                        figure_merge.add_trace(
                            go.Scatter(x=[HR_labeled['datetime'][index], HR_labeled['datetime'][index]],
                                       y=[dmin, dmax], mode="lines", line=dict(color='black'),
                                       name=f"Stress section {HR_labeled['Vorgang'][index]}"))

                elif checkboxIBI:
                    labels = IBI_labeled[~IBI_labeled["Vorgang"].isna()]
                    for index in labels.index:
                        figure_merge.add_trace(
                            go.Scatter(x=[IBI_labeled['datetime'][index], IBI_labeled['datetime'][index]],
                                       y=[dmin, dmax], mode="lines", line=dict(color='black'),
                                       name=f"Stress section {IBI_labeled['Vorgang'][index]}"))

                elif checkboxHRV:
                    labels = HRV_labeled[~HRV_labeled["Vorgang"].isna()]
                    for index in labels.index:
                        figure_merge.add_trace(
                            go.Scatter(x=[HRV_labeled['datetime'][index], HRV_labeled['datetime'][index]],
                                       y=[dmin, dmax], mode="lines", line=dict(color='black'),
                                       name=f"Stress section {HRV_labeled['Vorgang'][index]}"))  #

                st.markdown("---")
                st.subheader("MOS Download:")

                extract_start_time = st.time_input("Define Start time to extract number of MOS",
                                                   value = initial_start_time)
                extract_end_time = st.time_input("Define End time to extract number of MOS",
                                                 value = initial_end_time)

                st.info(initial_start_time)
                st.info(type(initial_start_time))

                #initial_start_time_t = datetime.datetime.strptime(initial_start_time, "%H:%M:%S")
                #initial_end_time_t = datetime.datetime.strptime(initial_end_time, "%H:%M:%S")

                # TODO - add start_time_trim and end_time_trim values for trimmed baseline calculation as input
                #selected_data = MOS_gsr_and_st_clean.set_index("time_iso")[start_time:end_time]
                #st.write(selected_data)

                extract_mins = st.number_input("Number of minutes to extract after a specific 'Vorgang':",
                                               value = 5)

                #EDA_labeled[~EDA_labeled['Vorgang'].isna()]

                vorgang_options = list(EDA_labeled[~EDA_labeled['Vorgang'].isna()]['Vorgang'])
                #st.write(vorgang_options)

                vorgang_selection = st.radio("Check event from when to extract data", vorgang_options)
                #st.write(EDA_labeled)
                vorgang_selection_ts = EDA_labeled.loc[EDA_labeled.Vorgang == vorgang_selection, 'datetime'].values[0]

                vorgang_selection_ts_end = vorgang_selection_ts + pd.to_timedelta(extract_mins, 'm')

                #MOS_gsr_and_st_clean[MOS_gsr_and_st_clean['time_iso'] > vorgang_selection_ts]
                extraction_subset = MOS_gsr_and_st_clean.set_index("time_iso")[vorgang_selection_ts:vorgang_selection_ts_end]
                st.write(extraction_subset[['GSR', 'GSR_raw', 'ST', 'ST_raw', 'MOS_Score', 'detectedMOS']].reset_index())
                MOS_cnt = len(extraction_subset[extraction_subset['detectedMOS'] == 1])
                st.write("Number of MOS in selected Subset: ", MOS_cnt)

                # TODO - create download option here


                #st.write(EDA_labeled.loc[EDA_labeled.Vorgang == vorgang_selection, 'datetime'].values[0])

                #st.plotly_chart(figure_merge, use_container_width=True)

                #combined_signals = st.checkbox("Visualize MOS with other signals:")
                #if combined_signals:
                #    st.plotly_chart(figure_merge, use_container_width=True)

                #else:
                #    st.plotly_chart(figure_merge, use_container_width=True)

            except(FileNotFoundError):
                st.error("ERROR: Looks like the EDA.csv does not exist")



        # zipped file uploader clause
        except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError, sqlite3.OperationalError):
            print("\nRng{}: Unable to process your request ! Something wrong in the SALK E4 zip file section".format(
                random.randint(0, 50)))
        finally:
            st.info("Finally executed")
            # removes the .zip file when saved locally
            #os.remove(os.path.join(path, uploaded_E4_zip_folder.name))


except (st.StreamlitAPIException):
    print("StreamlitAPIException was handled")

