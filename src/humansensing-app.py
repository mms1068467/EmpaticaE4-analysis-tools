"""
SALK Streamlit -- Version 1.0

#Data loader:
    loads, saves zipped and unzipped version locally, subsequently deleting zipped version
    deletes _MACOSX folder to avoid multiple (and redundant?) .csv and .xslx files contained inside the folder

#Data display:
    sidebar for user choice which signals to plot
    signal display width is dynamic
    signals with butterworth filtering have raw or filtered checkbox
    in case displayed signal does not exist in the given folder, FileNotFoundError() displays error message as signal could not be found

#Combined data display:
    conjoined through siple add_trace() function
    implement option for plotting stress sections?

SALK Streamlit -- Version 2.0

####WARNING: DO NOT ADD ANY NEW FOLDERS TO THE SRC DIRECTORY BEFORE ADDING IT TO THE
<<<<<<< HEAD
            known_files_list LIST OR IT WILL BE DELETED AFTER THE APP IS CLOSED OR
=======
            known_files_list LIST OR IT WILL BE DELETED AFTER THE APP IS CLOSED OR 
>>>>>>> cbbdf35 (added the deleting of temporary files)
            UPLOADED FILE REMOVED

- Integrated the butterworth filter for available individual signals (ST, BVP and EDA)
- Integrated the signal time range filter
- Set the HRV as an signal independent from IBI
- Integrated the Generate MOS on combined signals plot.
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
- Set generated files to delete on closed browser to avoid memory leak issue (commented out for now)
    - ISSUE: loading the same file for 2nd time caches it or something and keeps it deleted

SALK Streamlit -- Version 2.1

- Replace the Generate MOS to a sidebar
- Set the streamlit inform to choose 2 or more individual signals before applying the merge function

=======
- 
>>>>>>> cbbdf35 (added the deleting of temporary files)
=======
- Set generated files to delete on closed browser to avoid memory leak issue (going to keep eye on it)
=======
- Set generated files to delete on closed browser to avoid memory leak issue (commented out for now)
    - ISSUE: loading the same file for 2nd time caches it or something and keeps it deleted
>>>>>>> 0c4647b (source code for SALK app V 2.1)

SALK Streamlit -- Version 2.1

- Replace the Generate MOS to a sidebar 
- Set the streamlit inform to choose 2 or more individual signals before applying the merge function

>>>>>>> bad14e6 (source code for SALK app V 2.1)
#TODO


"""

import sys
import datetime
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
import shutil
import threading

import streamlit as st
import math
import pandas as pd
import numpy as np
import typing
import openpyxl
import os

# map libaries
import folium
from folium import plugins
import geopandas
from streamlit_folium import st_folium
from geopy import distance
from scipy import signal

from io import BytesIO
import xlsxwriter
import random

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
#
from io import StringIO  # for hashing the .sqlite file

from MOS_Detection import MOS_signal_preparation as msp
# from MOS_Detection import MOS_rules as rules
# from HumanSensing_Preprocessing import utilities
from HumanSensing_Preprocessing import preprocess_signals as pps
from HumanSensing_Preprocessing import sensor_check
# from MOS_Detection import MOS_parameters as mp
# from MOS_Detection import MOS_main as mm
from MOS_Detection import MOS_rules_paper_verified as mrp
from HumanSensing_Preprocessing import data_loader as dl
from HumanSensing_Visualization import map_loader as ml
from HumanSensing_Preprocessing import process_zip_files as pzf
import E4_Analysis_tools as e4at

##### Functions
try:
    # temporarily saves the file
    def save_uploadedfile(uploaded_file, path: str):
        with open(os.path.join(path, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        # return st.success("Temporarily saved file: {} to {}".format(uploaded_file.name, path))


    def add_groundtruth_mos(fig, MOS_detected):
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
    def open_and_extract_zip_pat(path, uploaded_E4_zip_folder):

        extract_zip = pzf.open_and_extract_zip_pat(path, uploaded_E4_zip_folder)

        return extract_zip


    @st.cache
    def find_all_csv_xslx_files(read_zip_files):

        find_csv_xslx = pzf.find_all_csv_xslx_files(read_zip_files)

        return find_csv_xslx

    
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
            individual_signal_path = create_csv_xlsx_list[0].rsplit("\\", 1)[0]
            pat_number_code = individual_signal_path.split("/")[-1].split(".")[-1]

            # print("Individual path", individual_signal_path)
            # print("Pat number code: ", pat_number_code)

            try:
                #### SIDEBAR
                # sidebar signal options
                st.sidebar.title("Select signals to display")
                checkboxST = st.sidebar.checkbox("Skin Temperature (ST)")
                checkboxACC = st.sidebar.checkbox("Acceleration (ACC)")
                checkboxBVP = st.sidebar.checkbox("Blood Volume Pressure (BVP)")
                checkboxEDA = st.sidebar.checkbox("Electrodermal Activity (EDA)")
                checkboxHR = st.sidebar.checkbox("Heart Rate (HR)")
                checkboxIBI = st.sidebar.checkbox("Interbeat Interval (IBI)")
                checkboxHRV = st.sidebar.checkbox("Heart Rate Variability (HRV)")

                # sidebar time filtering
                st.sidebar.markdown("---")
                st.sidebar.title("Select signal time range")
                ST_labeled_date_extract = merge_data(signal_path=os.path.join(individual_signal_path + "/TEMP.csv"),
                                                     labels_path=os.path.join(
                                                         individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                             pat_number_code)),
                                                     signal="ST")

                duration = pd.to_datetime(ST_labeled_date_extract['datetime'].max()) - pd.to_datetime(
                    ST_labeled_date_extract['datetime'].min())

                double_ended_seconds_slider_filter = st.sidebar.slider("Seconds after start of recording to display",
                                                                       value=[duration.seconds - duration.seconds,
                                                                              duration.seconds])

                st.sidebar.write("Duration of recording: \t ", " \t => \t",
                                 time.strftime("%H:%M:%S", time.gmtime(duration.seconds)))

                # double_ended_seconds_slider_filter = st.sidebar.slider("Seconds after start of recording to display", min_value = start_date, value= end_date, max_value= end_date, format=format)
                start_time = ST_labeled_date_extract['datetime'].min() + datetime.timedelta(
                    seconds=double_ended_seconds_slider_filter[0])
                end_time = ST_labeled_date_extract['datetime'].min() + datetime.timedelta(
                    seconds=double_ended_seconds_slider_filter[1])
                # filtered_data = ST_labeled_date_extract[(ST_labeled_date_extract['datetime'] >= start_time) & (ST_labeled_date_extract['datetime'] <= end_time)]

                # (pre)processes the individual signals and plots them as raw or filtered
                # throws an error if a given signal .csv file is not found in the initial folder
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
                        st.subheader("ACC signal plot")

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

                if checkboxEDA:
                    try:
                        st.markdown("---")
                        st.subheader("EDA signal plot")

                        EDA_labeled = e4at.merge_data(signal_path=os.path.join(individual_signal_path + "/EDA.csv"),
                                                      labels_path=os.path.join(
                                                          individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(
                                                              pat_number_code)),
                                                      signal="EDA")
                        EDA_labeled = EDA_labeled[
                            (EDA_labeled['datetime'] >= start_time) & (EDA_labeled['datetime'] <= end_time)]

                        checkboxEDAraw = st.checkbox("Plot EDA raw")

                        if checkboxEDAraw:
                            EDAfigureRaw = e4at.plot_EDA(EDA_labeled, raw=True)

                            st.plotly_chart(EDAfigureRaw, use_container_width=True)

                        checkboxEDAfiltered = st.checkbox("Plot EDA filtered")

                        # needs to undergo preprocess_EDA() butterworth
                        if checkboxEDAfiltered:
                            try:

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
                    except(FileNotFoundError):
                        st.error("ERROR: Looks like the EDA.csv does not exist")

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

                ####Combining of the signals into a single graph
                st.sidebar.markdown("---")
                st.sidebar.title("Merge signals")
                apply_merge_signals = st.sidebar.checkbox("Apply merging of selected signals")

                if apply_merge_signals:
                    try:
                        figure_merge = go.Figure()
                        dataframe_merge = pd.DataFrame()
                        # dataframe_merge_datetime = dataframe_merge.join(ST_labeled_date_extract['datetime'])
                        dataframe_merge['datetime'] = ST_labeled_date_extract['datetime']

                        # list for Y-axis min and max values so the MOS stress lines can be plotted in according Y value range
                        MOS_ymin_list = []
                        MOS_ymax_list = []

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

                        if checkboxEDA:
                            if checkboxEDAraw:
                                figure_merge.add_trace(
                                    go.Scatter(x=EDA_labeled['datetime'], y=EDA_labeled["EDA"], line=dict(color="blue"),
                                               name="Raw Electrodermal Activity (EDA) in mircoSiemens"))

                                MOS_ymin_list.append(EDA_labeled['EDA'].min())
                                MOS_ymax_list.append(EDA_labeled['EDA'].max())

                            if checkboxEDAfiltered:
                                figure_merge.add_trace(
                                    go.Scatter(x=EDA_preprocessed['datetime'], y=EDA_preprocessed["EDA_filtered"],
                                               line=dict(color="blue"),
                                               name="Filtered Electrodermal Activity (EDA) in mircoSiemens"))

                                MOS_ymin_list.append(EDA_preprocessed['EDA_filtered'].min())
                                MOS_ymax_list.append(EDA_preprocessed['EDA_filtered'].max())

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

                        elif checkboxEDA:
                            labels = EDA_labeled[~EDA_labeled["Vorgang"].isna()]
                            for index in labels.index:
                                figure_merge.add_trace(
                                    go.Scatter(x=[EDA_labeled['datetime'][index], EDA_labeled['datetime'][index]],
                                               y=[dmin, dmax], mode="lines", line=dict(color='black'),
                                               name=f"Stress section {EDA_labeled['Vorgang'][index]}"))

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
                        st.subheader("Combined signals:")
                        # plots all the merged signals that were given
                        checkboxGenerateMOS = st.sidebar.checkbox("Generate MOS")
                        # st.plotly_chart(figure_merge, use_container_width=True)


                        if checkboxGenerateMOS:

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

                            # plotting vertical lines to the existing merged signals plot
                            MOS_figure = add_groundtruth_mos(figure_merge, final_MOS_output)
                            st.plotly_chart(MOS_figure, use_container_width=True)
                            st.write("Number of MOS detected based on ST & GSR rules: **{}**".format(mos_identified))
                        else:
                            st.plotly_chart(figure_merge, use_container_width=True)
                        # print("Min list: ", MOS_ymin_list)
                        # print("Max list: ", MOS_ymax_list)

                        # print ("\nMin value: ", min(MOS_ymin_list))
                        # print ("Max value: ", max(MOS_ymax_list))

                    # apply merge signal clause
                    except (
                    ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError, sqlite3.OperationalError):
                        print("\nRng{}: Something went wrong in the Apply_merge section".format(
                            random.randint(0, 50)))
                        st.error(
                            "Cannot apply merge function. Either selected signal does not exist or try to select more than 1 existing signal")

                        # signal processing clause
            except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError, sqlite3.OperationalError):
                print("\nRng{}: Something went wrong in the checkbox section".format(
                    random.randint(0, 50)))





        # zipped file uploader clause
        except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError, sqlite3.OperationalError):
            print("\nRng{}: Unable to process your request ! Something wrong in the SALK E4 zip file section".format(
                random.randint(0, 50)))
        finally:
            # removes the .zip file when saved locally
            os.remove(os.path.join(path, uploaded_E4_zip_folder.name))


    #elif uploaded_E4_zip_folder is None:
    #    try:
    #        print("\nDelete working directory files initialized")
    #        #access the current working directory and delte files
    #        store_directory = os.getcwd()
    #        files_wd_csv = [file for file in os.listdir(store_directory)]

    #
    #        known_files_list = ["E4_Analysis_tools.py", "humansensing-app-main-branch.py",
    #                            "humansensing-app.py", "HumanSensing_Preprocessing",
    #                            "HumanSensing_Visualization", "MOS_Detection",
    #                            "requirements3.txt", "SALK_analysis_notebook.ipynb",
    #                            "__init__.py", "__pycache__"]
    #
    #        #compare two directories and return unknown files to us
    #        print("Unknown files: ")
    #        unknown_files_list = [x for x in files_wd_csv if x not in known_files_list]
    #        #print(unknown_files_list)
    #        if len(unknown_files_list) > 0:
    #            for unknown in unknown_files_list:
    #                print(os.path.join(store_directory, unknown))
    #                shutil.rmtree(os.path.join(store_directory, unknown))
    #    except(NotADirectoryError):
    #        print("Found an untracked file in the repository")

    # st.info(f"All csv files in the WD: {files_wd_csv}")
    # print("\nWorking files: ")
    # remove temporarily stored files (.csv, .xlsx, etc.)

    # create a list of files known to us, if there is an intruder, delete it!
    # if file == saved_folder_path:
    #    print("Yes it is")
    # os.remove(path_to_file)

    # os.remove(os.path.join(path, uploaded_data_files.name))

    #    files_wd = [f for f in os.listdir(store_directory) if os.path.isfile(f)]
    # print(f"All files in the WD after removing temporarily stored files: {files_wd}")
    elif uploaded_E4_zip_folder is None:
        try:
            print("\nDelete working directory files initialized")
            #access the current working directory and delte files
            store_directory = os.getcwd()
            files_wd_csv = [file for file in os.listdir(store_directory)]
            
            known_files_list = ["E4_Analysis_tools.py", "humansensing-app-main-branch.py", 
                                "humansensing-app.py", "HumanSensing_Preprocessing", 
                                "HumanSensing_Visualization", "MOS_Detection", 
                                "requirements3.txt", "SALK_analysis_notebook.ipynb", 
                                "__init__.py", "__pycache__"]
            
            #compare two directories and return unknown files to us
            print("Unknown files: ")
            unknown_files_list = [x for x in files_wd_csv if x not in known_files_list]
            #print(unknown_files_list)
            if len(unknown_files_list) > 0:
                for unknown in unknown_files_list:
                    
                    print(os.path.join(store_directory, unknown))
                    shutil.rmtree(os.path.join(store_directory, unknown))
        except(NotADirectoryError):
            print("Found an untracked file in the repository")
        #st.info(f"All csv files in the WD: {files_wd_csv}")
        #print("\nWorking files: ")
        # remove temporarily stored files (.csv, .xlsx, etc.)
        

            #create a list of files known to us, if there is an intruder, delete it!
            #if file == saved_folder_path:
            #    print("Yes it is")
            #os.remove(path_to_file)
            
        #os.remove(os.path.join(path, uploaded_data_files.name))

    #    files_wd = [f for f in os.listdir(store_directory) if os.path.isfile(f)]
        #print(f"All files in the WD after removing temporarily stored files: {files_wd}")


# handles the initial streamlit page loading error which relates to multiple loading of st.set_page_config
except (st.StreamlitAPIException):
    print("StreamlitAPIException was handled")


