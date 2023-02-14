import streamlit as st
from pathlib import Path
import os
import pandas as pd
import numpy as np

#import E4_Analysis_tools as e4at

import altair as alt


# temporarily saves the file
@st.cache
def save_uploadedfile(uploaded_file, path: str):
    with open(os.path.join(path, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())


def get_MOS_per_second(data, number_of_mos, number_of_seconds):

    df = data.copy()

    mos_per_sec = number_of_mos / number_of_seconds

    return mos_per_sec



path = Path(__file__).parent.resolve()


uploaded_data_file = st.file_uploader("Upload your Excel file with the combined analysis output", type=["xlsx"],
                                          accept_multiple_files=False)

if uploaded_data_file is not None:

    st.markdown("# Drag and drop the Stress Output .xlsx file and explore correlations:")

    save_uploadedfile(uploaded_file=uploaded_data_file, path=path)
    # file_extension = uploaded_data_file.name.split(".")[-1]
    file_name_data = uploaded_data_file.name.split(".")[0] + "." + uploaded_data_file.name.split(".")[1]

    st.write("Data File name", file_name_data)

    path_to_data_file = str(path) + "\\" + file_name_data


    sheets_dict = pd.read_excel(path_to_data_file,
                                sheet_name=['OneTimeMeasurements', 'SectionBasedMeasurements', 'SectionBasedStress'])

    Patient_one_time = sheets_dict.get("OneTimeMeasurements")
    Patient_section_times = sheets_dict.get('SectionBasedMeasurements')
    Patient_stress = sheets_dict.get("SectionBasedStress")

    st.write("One time measurements", Patient_one_time)
    st.write("Section-based Measurements", Patient_section_times)
    st.write("Section-based Stress Moments", Patient_stress)

    stress_subset = Patient_stress[["ID", "Gender", "Age",
                    "MOS_total_new", "MOS_total_new_per_sec",
                    "MOS_HS_HS5min_new", "MOS_HS_HS5min_new_per_sec",
                    "MOS_T1_T2_new", "MOS_T1_T2_new_per_sec",
                    "MOS_T2_T3_new", "MOS_T2_T3_new_per_sec",
                    "MOS_T3_T4_new", "MOS_T3_T4_new_per_sec",
                    "MOS_T4_T5_new", "MOS_T4_T5_new_per_sec",
                    "MOS_T5_T6_new", "MOS_T5_T6_new_per_sec"]]

    stress_subset.rename(
        columns={'MOS_total_new': 'MOS_total',
                 'MOS_total_new_per_sec': 'MOS/s',
                 'MOS_HS_HS5min_new': 'HS_HS5',
                 'MOS_HS_HS5min_new_per_sec': 'HS_HS5/s',
                 'MOS_T1_T2_new': 'T1_T2',
                 'MOS_T1_T2_new_per_sec': 'T1_T2/s',
                 'MOS_T2_T3_new': 'T2_T3',
                 'MOS_T2_T3_new_per_sec': 'T2_T3/s',
                 'MOS_T3_T4_new': 'T3_T4',
                 'MOS_T3_T4_new_per_sec': 'T3_T4/s',
                 'MOS_T4_T5_new': 'T4_T5',
                 'MOS_T4_T5_new_per_sec': 'T4_T5/s',
                 'MOS_T5_T6_new': 'T5_T6',
                 'MOS_T5_T6_new_per_sec': 'T5_T6/s'}, inplace=True)

    st.write(stress_subset)


    st.header("Basic Visuals:")

    MOS_vs_Age_gender_based = alt.Chart(Patient_one_time).mark_circle(size = 60).encode(
        x = "Age",
        y = "MOS_total",
        color = "Gender",
        tooltip = ["STAI-T/T-Werte", "PostOPFrage", "Sedierung erhalten", "Mepivacain 1%/ml", "NRS max"]
    ).interactive()

    st.altair_chart(MOS_vs_Age_gender_based, use_container_width=True)


    st.header("One-time Measurement Analysis")

    col1, col2 = st.columns(2, gap="medium")

    with col1:

        options_one = Patient_one_time.columns
        var1 = st.selectbox("Please select the Measurement variable you want to visualize on the X-axis",
                     options = options_one)
        var1_series = Patient_one_time[var1]
        #st.write(var1_series)

    with col2:

        options_two = Patient_one_time.columns
        var2 = st.selectbox("Please select the Stress variables you want to visualize on the Y-axis",
                     options=options_two)
        var2_series = Patient_one_time[var2]
        #st.write(var2_series)

    try:

        combined_plot_data = pd.concat([var1_series, var2_series,
                                        Patient_one_time["ID"],
                                        Patient_one_time["Gender"],
                                        Patient_one_time["STAI-T/T-Werte"],
                                        Patient_one_time["PostOPFrage"],
                                        Patient_one_time["Sedierung erhalten"],
                                        Patient_one_time["Mepivacain 1%/ml"],
                                        Patient_one_time["NRS max"]], axis=1)

        combined_plot = alt.Chart(combined_plot_data).mark_circle(size = 60).encode(
            x = var1,
            y = var2,
            tooltip=["ID", "Gender", "STAI-T/T-Werte", "PostOPFrage", "Sedierung erhalten", "Mepivacain 1%/ml", "NRS max"]
        ).interactive()

        st.altair_chart(combined_plot, use_container_width=True)

        add_color_var = st.checkbox("Add color indicator variable: ")

        if add_color_var:
            options_three = Patient_one_time.columns

            var3 = st.selectbox("Select variable for coloring:",
                                options=options_three)
            var3_series = Patient_one_time[var3]

            combined_plot_data = pd.concat([var1_series, var2_series, var3_series], axis=1)

            combined_plot = alt.Chart(combined_plot_data).mark_circle(size=60).encode(
                x=var1,
                y=var2,
                color = var3
            ).interactive()

            st.altair_chart(combined_plot, use_container_width=True)


    except st.StreamlitAPIException:
        st.info("You need to select two different columns to display")

    st.header("Section-based Analysis")





    col_sec1, col_sec2 = st.columns(2, gap="medium")






st.sidebar.subheader("Signal Visualization")

visualize_eda = st.sidebar.checkbox("Visualize EDA recordings for a specific patient: ")

if visualize_eda:
    uploaded_signal_measurements = st.file_uploader("Upload the Excel file with the combined sensor measurements", type=["xlsx"],
                                          accept_multiple_files=False)

    if uploaded_signal_measurements is not None:
        st.markdown("# Drag and drop the Stress Output .xlsx file and explore correlations:")

        save_uploadedfile(uploaded_file=uploaded_signal_measurements, path=path)
        # file_extension = uploaded_data_file.name.split(".")[-1]
        file_name_signals = uploaded_signal_measurements.name.split(".")[0] + "." + uploaded_signal_measurements.name.split(".")[1]

        st.write("Data File name", file_name_signals)

        path_to_signals_file = str(path) + "\\" + file_name_signals

        sensor_measurements = pd.read_excel(path_to_signals_file)

        st.write(sensor_measurements)

        patients = list(sensor_measurements["ID"].unique())

        #if "visibility" not in st.session_state:
        #    st.session_state.visibility = "visible"
        #    st.session_state.disabled = False

        st.sidebar.checkbox("Disable Patient selection:", key = "disabled")

        st.radio(
            "Set Patient for which sensor measurements should be displayed: ",
        #    key="visibility",
            options=patients,
        )








