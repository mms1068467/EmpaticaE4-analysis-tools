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

"""

import sys
import datetime
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import streamlit as st
import math
import pandas as pd
import numpy as np
import typing
import openpyxl
import os

#map libaries
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

from io import StringIO # for hashing the .sqlite file

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
    #temporarily saves the file
    def save_uploadedfile(uploaded_file, path: str):
        with open(os.path.join(path, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        return st.success("Temporarily saved file: {} to {}".format(uploaded_file.name, path))


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
    def plot_BVP(signal, raw = True):

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

    with expander_project_description:
        st.info("""
            SALK Data Visualization Dashboard is created to bring forth the processing capabilities of Empatica E4 biometric signals, generating Moments of Stress (MOS), applying a Butterworth filter and graphicaly displaying the results \n
            -------------------------------------------------------------------------------------

            This Steamlit Application is a platform to analyze biometric data that is recorded by the Empatica E4 wristband. Empatica data is downloaded as a .zip file and contains individual biometric signals, recorded at their respective sampling frequency, and a timestamp in unix format, indicating the starting time of the recordings.

            The app allows users to upload the .zip file containing the individual sensor recordings, and analyze them through a visual inspection.
            """)

    
    # If neccessary, add an users local path in order to use and store the files from the app
    # path = st.text_input("Please enter the path where you want to store the project data INCLUDING a '/' at the end and press Enter (Example: C:/Users/projects/data/)" )
    path = Path(__file__).parent.resolve()
    st.markdown("---")

    #### File uploader
    st.header("Drag and drop zip folder containing individual signals")

    uploaded_E4_zip_folder = st.file_uploader("Drag and drop your SALK E4 zip folder(s) here...", type=["zip", "7z"], accept_multiple_files= False)
    st.info("Upload zip folder")


    #### Main, branching part of the application as soon as the zip is uploaded
    if uploaded_E4_zip_folder is not None:
        try:
            
            ####UPLOAD AND READ ZIP FOLDER
            #save locally to access it
            save_uploadedfile(uploaded_file=uploaded_E4_zip_folder, path=path)
            full_file_name = uploaded_E4_zip_folder.name.split(".")[0] + "." + uploaded_E4_zip_folder.name.split(".")[1]
            saved_folder_path = str(path) + "\\" + full_file_name
            
            #read and extract files from zip to create a list
            read_zip_files = open_and_extract_zip_pat(path, uploaded_E4_zip_folder)
            #print("Pathway to Pat.x: ", read_zip_files)

            #create a signal path list to access them
            create_csv_xlsx_list = find_all_csv_xslx_files(read_zip_files)
            
            #fetch signal directory path and pat number 
            individual_signal_path = create_csv_xlsx_list[0].rsplit("\\", 1)[0]
            pat_number_code = individual_signal_path.split("/")[-1].split(".")[-1]
            #print("Individual path", individual_signal_path)
            #print("Pat number code: ", pat_number_code)

        except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError, sqlite3.OperationalError):
            print("\nRng{}: Unable to process your request ! Something wrong in the SALK E4 zip file section".format(
                random.randint(0, 50)))
        finally:
            #removes the file when saved locally
            os.remove(os.path.join(path, uploaded_E4_zip_folder.name))
    

        ####PROCESS THE DATA
        
        try:
            #sidebar signal options
            st.sidebar.title("Select signals to display:")
            checkboxST = st.sidebar.checkbox("Skin Temperature (ST)")
            checkboxACC = st.sidebar.checkbox("Acceleration (ACC)")
            checkboxBVP = st.sidebar.checkbox("Blood Volume Pressure (BVP)")
            checkboxEDA = st.sidebar.checkbox("Electrodermal Activity (EDA)")
            checkboxHR = st.sidebar.checkbox("Heart Rate (HR)")
            checkboxIBI = st.sidebar.checkbox("Interbeat Interval (IBI)")
            
            #(pre)processes the individual signals and plots them as raw or filtered
            #throws an error if a given signal .csv file is not found in the initial folder
            if checkboxST:
                try:
                    st.markdown("---")
                    st.subheader("ST signal plot")
                    
                    # get list of temporarily stored files (.csv, .xlsx, .sqlite, etc.)
                    store_directory = os.getcwd()
                    st.info(f"In read_zip_files directory: {read_zip_files}")
                    
                    st.info(f"Individual signal path is: {individual_signal_path} ")
                    
                    dire = os.path.join(read_zip_files, read_zip_files.split('\\')[-1])
                    st.info(dire)
                    
                    files_wd_csv = [file for file in os.listdir(dire)]

                    st.info(f"All csv and excel files in the WD: {files_wd_csv}")
                    

                    
                    ST_labeled = merge_data(signal_path = os.path.join(individual_signal_path + "/TEMP.csv"),
                                    labels_path = os.path.join(individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(pat_number_code)),
                                    signal = "ST")
                    ST_preprocessed = e4at.preprocess_ST(ST_labeled)

                    checkboxSTraw = st.checkbox("Plot ST raw")
                    
                    if checkboxSTraw:

                        STfigure = e4at.plot_ST(ST_labeled)
                        
                        st.plotly_chart(STfigure, use_container_width=True)

                    checkboxSTfiltered = st.checkbox("Plot ST filtered")

                    if checkboxSTfiltered:
                        STfigureFiltered = e4at.plot_ST(ST_preprocessed, raw = False)
                        
                        st.plotly_chart(STfigureFiltered, use_container_width=True)

                except(FileNotFoundError):
                    st.error("ERROR: Looks like the TEMP.csv does not exist")


            if checkboxACC:
                try:      
                    st.markdown("---")
                    st.subheader("ACC signal plot")
                    
                    ACC_labeled = merge_data(signal_path = os.path.join(individual_signal_path + "/ACC.csv"),
                                    labels_path = os.path.join(individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(pat_number_code)),
                                    signal = "ACC")
                    ACCfigure = plot_ACC(ACC_labeled)
                    
                    st.plotly_chart(ACCfigure, use_container_width=True)

                except(FileNotFoundError):
                    st.error("ERROR: Looks like the ACC.csv does not exist")


            if checkboxBVP:
                try:
                    st.markdown("---")
                    st.subheader("BVP signal plot")

                    BVP_labeled = merge_data(signal_path = os.path.join(individual_signal_path + "/BVP.csv"),
                                        labels_path = os.path.join(individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(pat_number_code)),
                                        signal = "BVP")
                    BVP_preprocessed = e4at.preprocess_BVP(BVP_labeled)

                    checkboxBVPraw = st.checkbox("Plot BVP raw")
                    
                    if checkboxBVPraw:
                        
                        BVPfigure = plot_BVP(BVP_labeled)
                        BVPfigure.update_xaxes(automargin=True)
                        
                        st.plotly_chart(BVPfigure, use_container_width=True)
                    
                    checkboxBVPfiltered = st.checkbox("Plot BVP filtered")

                    if checkboxBVPfiltered:

                        BVPfigureFiltered = plot_BVP(BVP_preprocessed, raw = False)
                        
                        st.plotly_chart(BVPfigureFiltered, use_container_width=True)

                except(FileNotFoundError):
                    st.error("ERROR: Looks like the BVP.csv does not exist")


            if checkboxEDA:
                try:
                    st.markdown("---")
                    st.subheader("EDA signal plot")

                    EDA_labeled = e4at.merge_data(signal_path = os.path.join(individual_signal_path + "/EDA.csv"),
                                    labels_path = os.path.join(individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(pat_number_code)),
                                    signal = "EDA")
                    EDA_preprocessed = e4at.preprocess_EDA(EDA_labeled)

                    checkboxEDAraw = st.checkbox("Plot EDA raw")

                    if checkboxEDAraw:

                        EDAfigureRaw = e4at.plot_EDA(EDA_labeled, raw = True)
                        
                        st.plotly_chart(EDAfigureRaw, use_container_width=True)

                    checkboxEDAfiltered = st.checkbox("Plot EDA filtered")
                    
                    #needs to undergo preprocess_EDA() butterworth
                    if checkboxEDAfiltered:
                        
                        EDAfigureFiltered = e4at.plot_EDA(EDA_preprocessed, raw = False)
                        
                        st.plotly_chart(EDAfigureFiltered, use_container_width=True)

                except(FileNotFoundError):
                    st.error("ERROR: Looks like the EDA.csv does not exist")


            if checkboxHR:
                try:
                    st.markdown("---")
                    st.subheader("HR signal plot")
                    HR_labeled = e4at.merge_data(signal_path = os.path.join(individual_signal_path + "/HR.csv"),
                                    labels_path = os.path.join(individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(pat_number_code)),
                                    signal = "HR")
                    HRfigure = e4at.plot_HR(HR_labeled)
                    
                    st.plotly_chart(HRfigure, use_container_width=True)

                except(FileNotFoundError):
                    st.error("ERROR: Looks like the HR.csv does not exist")


            if checkboxIBI:
                checkboxHRV = st.sidebar.checkbox("Heart Rate Variability (HRV)")

                try:
                    st.markdown("---")
                    st.subheader("IBI signal plot")
                    IBI_labeled = e4at.merge_data(signal_path = os.path.join(individual_signal_path + "/IBI.csv"),
                                    labels_path = os.path.join(individual_signal_path + "/ZeitenauswertungEmpaticaPat{}.xlsx".format(pat_number_code)),
                                    signal = "IBI")
                    IBIfigure = e4at.plot_IBI(IBI_labeled)
                    
                    st.plotly_chart(IBIfigure, use_container_width=True)

                except(FileNotFoundError):
                    st.error("ERROR: Looks like the IBI.csv does not exist")

                if checkboxHRV:
                    try:

                        st.markdown("---")
                        st.subheader("HRV signal plot")

                        HRV_labeled = e4at.get_HRV_from_IBI(IBI_labeled)
                        HRVfigure = e4at.plot_HRV(HRV_labeled)
                        
                        st.plotly_chart(HRVfigure, use_container_width=True)
                    except(FileNotFoundError):
                        st.error("ERROR: Looks like the IBI.csv does not exist or something is wrong with deriving HRV from IBI")
                    

            ####Combining of the signals into a single graph
            apply_merge_signals = st.sidebar.button("Apply merging of selected signals")
            if apply_merge_signals:
                try:
                    figure_merge = go.Figure()
                    #list for Y-axis min and max values so the MOS stress lines can be plotted in according Y value range
                    MOS_ymin_list = []
                    MOS_ymax_list = []

                  
                    #merges a trace for each given signal and records its Y min and max values
                    if checkboxST:
                     
                        if checkboxSTraw:
                            figure_merge.add_trace(go.Scatter(x = ST_labeled['datetime'], y = ST_labeled["ST"], line = dict(color = "orange"), name = "Raw Skin Temperature (ST) in ° C"))
                            
                            MOS_ymin_list.append(ST_labeled['ST'].min())
                            MOS_ymax_list.append(ST_labeled['ST'].max())
                  
                        if checkboxSTfiltered:
                            figure_merge.add_trace(go.Scatter(x = ST_labeled['datetime'], y = ST_preprocessed["ST_filtered"], line = dict(color = "orange"), name = "Filtered Temperature (ST) in ° C"))
                            
                            MOS_ymin_list.append(ST_preprocessed['ST'].min())
                            MOS_ymax_list.append(ST_preprocessed['ST'].max())

                
                    if checkboxACC:
                        figure_merge.add_trace(go.Scatter(x = ACC_labeled["datetime"], y = ACC_labeled["X-axis"], line=dict(color="red"),
                                        name = 'X-Axis Acceleration in g'))
                        figure_merge.add_trace(go.Scatter(x = ACC_labeled['datetime'], y = ACC_labeled['Y-axis'], line = dict(color = 'green'),
                                name = 'X-Axis Acceleration in g'))
                        figure_merge.add_trace(go.Scatter(x = ACC_labeled['datetime'], y = ACC_labeled['Z-axis'], line = dict(color = 'blue'),
                                name = 'Z-Axis Acceleration in g'))

                        MOS_ymin_list.append(ACC_labeled['X-axis'].min())
                        MOS_ymax_list.append(ACC_labeled['X-axis'].max())
                        MOS_ymin_list.append(ACC_labeled['Y-axis'].min())
                        MOS_ymax_list.append(ACC_labeled['Y-axis'].max())
                        MOS_ymin_list.append(ACC_labeled['Z-axis'].min())
                        MOS_ymax_list.append(ACC_labeled['Z-axis'].max())

                  
                    if checkboxBVP:
                      
                        if checkboxBVPraw:
                            figure_merge.add_trace(go.Scatter(x = BVP_labeled['datetime'], y = BVP_labeled["BVP"], line = dict(color = "purple"), name = "Raw Blood Volume Pressure (BVP)"))
                            
                            MOS_ymin_list.append(BVP_labeled['BVP'].min())
                            MOS_ymax_list.append(BVP_labeled['BVP'].max())


                        if checkboxBVPfiltered:
                            figure_merge.add_trace(go.Scatter(x = BVP_preprocessed['datetime'], y = BVP_preprocessed["BVP_filtered"], line = dict(color = "firebrick"), name = "Filtered Blood Volume Pressure (BVP)"))
                            
                            MOS_ymin_list.append(BVP_preprocessed['BVP_filtered'].min())
                            MOS_ymax_list.append(BVP_preprocessed['BVP_filtered'].max())


                    if checkboxEDA:
                        if checkboxEDAraw:
                            figure_merge.add_trace(go.Scatter(x = EDA_labeled['datetime'], y = EDA_labeled["EDA"], line = dict(color = "blue"), name = "Raw Electrodermal Activity (EDA) in mircoSiemens"))
                            
                            MOS_ymin_list.append(EDA_labeled['EDA'].min())
                            MOS_ymax_list.append(EDA_labeled['EDA'].max())


                        if checkboxEDAfiltered:
                            figure_merge.add_trace(go.Scatter(x = EDA_preprocessed['datetime'], y = EDA_preprocessed["EDA_filtered"], line = dict(color = "blue"), name = "Filtered Electrodermal Activity (EDA) in mircoSiemens"))

                            MOS_ymin_list.append(EDA_preprocessed['EDA_filtered'].min())
                            MOS_ymax_list.append(EDA_preprocessed['EDA_filtered'].max())


                    if checkboxHR:
                        figure_merge.add_trace(go.Scatter(x = HR_labeled['datetime'], y = HR_labeled["HR"], line = dict(color = "red"), name = "Heart Rate (HR) in BPM"))
                        
                        MOS_ymin_list.append(HR_labeled['HR'].min())
                        MOS_ymax_list.append(HR_labeled['HR'].max())


                    if checkboxIBI:
                        figure_merge.add_trace(go.Scatter(x = IBI_labeled['datetime'], y = IBI_labeled["IBI"], line = dict(color = "green"), name = "Interbeat Interval (IBI) in Seconds"))
                        
                        MOS_ymin_list.append(IBI_labeled['IBI'].min())
                        MOS_ymax_list.append(IBI_labeled['IBI'].max())


                        if checkboxHRV:
                            figure_merge.add_trace(go.Scatter(x = HRV_labeled['datetime'], y = HRV_labeled["HRV"], line = dict(color = "red"), name = "Heart Rate Variability (HRV) in Seconds"))

                            MOS_ymin_list.append(HRV_labeled['HRV'].min())
                            MOS_ymax_list.append(HRV_labeled['HRV'].max())
                    
                    #assigning the Y-axis min and max values
                    dmin = min(MOS_ymin_list)
                    dmax = max(MOS_ymax_list)
                    
                    #computes the MOS by timedate in data and plots it
                    if checkboxST:
                        labels = ST_labeled[~ST_labeled["Vorgang"].isna()]
                        
                        for index in labels.index:
                            figure_merge.add_trace(go.Scatter(x = [ST_labeled['datetime'][index], ST_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {ST_labeled['Vorgang'][index]}"))
                        
                    elif checkboxACC:
                        labels = ACC_labeled[~ACC_labeled["Vorgang"].isna()]
                        for index in labels.index:
                            figure_merge.add_trace(go.Scatter(x = [ACC_labeled['datetime'][index], ACC_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {ACC_labeled['Vorgang'][index]}"))
                    
                    elif checkboxBVP:
                        labels = BVP_labeled[~BVP_labeled["Vorgang"].isna()]
                        for index in labels.index:
                            figure_merge.add_trace(go.Scatter(x = [BVP_labeled['datetime'][index], BVP_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {BVP_labeled['Vorgang'][index]}"))

                    elif checkboxEDA:
                        labels = EDA_labeled[~EDA_labeled["Vorgang"].isna()]
                        for index in labels.index:
                            figure_merge.add_trace(go.Scatter(x = [EDA_labeled['datetime'][index], EDA_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {EDA_labeled['Vorgang'][index]}"))
                    
                    elif checkboxHR:
                        labels = HR_labeled[~HR_labeled["Vorgang"].isna()]

                        for index in labels.index:
                            figure_merge.add_trace(go.Scatter(x = [HR_labeled['datetime'][index], HR_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {HR_labeled['Vorgang'][index]}"))

                    elif checkboxIBI:
                        labels = IBI_labeled[~IBI_labeled["Vorgang"].isna()]
                        for index in labels.index:
                            figure_merge.add_trace(go.Scatter(x = [IBI_labeled['datetime'][index], IBI_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {IBI_labeled['Vorgang'][index]}"))

                    elif checkboxHRV:
                        labels = HRV_labeled[~HRV_labeled["Vorgang"].isna()]
                        for index in labels.index:
                            figure_merge.add_trace(go.Scatter(x = [HRV_labeled['datetime'][index], HRV_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {HRV_labeled['Vorgang'][index]}")) # 
                        

                    
                    st.markdown("---")
                    st.subheader("Combined signals:")
                    #plots all the merged signals that were given
                    st.plotly_chart(figure_merge, use_container_width=True)
                    
                    #print("Min list: ", MOS_ymin_list)
                    #print("Max list: ", MOS_ymax_list)

                    #print ("\nMin value: ", min(MOS_ymin_list))
                    #print ("Max value: ", max(MOS_ymax_list))
                    
                except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError, sqlite3.OperationalError):
                    print("\nRng{}: Something went wrong in the Apply_merge section".format(
                    random.randint(0, 50)))
                    st.error("Cannot apply merge function. Either selected signal does not exist or try to select more than 1 existing signal")   
                 
        
        except (ValueError, RuntimeError, TypeError, NameError, pd.io.sql.DatabaseError, sqlite3.OperationalError):
                print("\nRng{}: Something went wrong in the checkbox section".format(
                    random.randint(0, 50)))
                    
#handles the initial streamlit page loading error which relates to multiple loading of st.set_page_config
except (st.StreamlitAPIException): 
    print("StreamlitAPIException was handled")


