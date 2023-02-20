import streamlit as st
from pathlib import Path
import os
import pandas as pd
import numpy as np

#import E4_Analysis_tools as e4at

import altair as alt
from io import BytesIO

# temporarily saves the file
@st.cache
def save_uploadedfile(uploaded_file, path: str):
    with open(os.path.join(path, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())


def get_MOS_per_second(data, number_of_mos, number_of_seconds):

    df = data.copy()

    mos_per_sec = number_of_mos / number_of_seconds

    return mos_per_sec

#TODO - use Section-based Stress Moments to calculate MOS over user-defined time interval based on number of MOS and duration / number of datapoints

def MOS_per_time_interval(data, MOS_stress_section, durationCol = "MOS_total_dur4Hz", colName = "MOS/s", time_interval = 1):

    df = data.copy()
    # Calculate number of data points per second - division by 4 as we have a 4Hz sampling frequency for EDA
    number_of_mos_per_second = df[durationCol] / 4
    # Calculate number of stress moments per second and then multiply by user-defined time interval
    df[colName] = (df[MOS_stress_section] / number_of_mos_per_second) * time_interval

    return df

def section_averge(data, MOS_stress_section):
    df = data.copy()
    pass

def patient_average(data, MOS_stress_section):
    df = data.copy()
    pass





path = Path(__file__).parent.resolve()

st.header("Drag and drop the Stress Output .xlsx file and explore data & correlations:")

uploaded_data_file = st.file_uploader("Upload your Excel file with the combined analysis output", type=["xlsx"],
                                          accept_multiple_files=False)

if uploaded_data_file is not None:

    save_uploadedfile(uploaded_file=uploaded_data_file, path=path)
    # file_extension = uploaded_data_file.name.split(".")[-1]
    file_name_data = uploaded_data_file.name.split(".")[0] + "." + uploaded_data_file.name.split(".")[1]

    st.write("Data File name", file_name_data)

    path_to_data_file = str(path) + "/" + file_name_data


    sheets_dict = pd.read_excel(path_to_data_file,
                                sheet_name=['OneTimeMeasurements', 'SectionBasedMeasurements', 'SectionBasedStress'])

    Patient_one_time = sheets_dict.get("OneTimeMeasurements")
    Patient_section_times = sheets_dict.get('SectionBasedMeasurements')
    Patient_stress = sheets_dict.get("SectionBasedStress")

    st.header("Datasets within the Output file:")

    show_hide_tables = st.checkbox("Show / Hide Tables (includes Download Option):")

    if show_hide_tables:

        st.write("One time measurements", Patient_one_time)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            Patient_one_time.to_excel(writer, index = False, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name="One-time-measurements.xlsx",
                                            mime="application/vnd.ms-excel")

        st.write("Section-based Measurements", Patient_section_times)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            Patient_section_times.to_excel(writer, index = False, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name="Patient-section-times.xlsx",
                                            mime="application/vnd.ms-excel")

        st.write("Section-based Stress Moments", Patient_stress)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            Patient_stress.to_excel(writer, index = False, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name="Patient-stress-times.xlsx",
                                            mime="application/vnd.ms-excel")




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

    st.sidebar.subheader("Stress Analysis and Data Exploration")

    stress_analysis_checkbox = st.sidebar.checkbox("Stress Analysis & Data Exploration")

    if stress_analysis_checkbox:

        st.header("Section-based Stress Analysis")

        st.write(stress_subset)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            stress_subset.to_excel(writer, index = False, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name="Patient-stress-sections.xlsx",
                                            mime="application/vnd.ms-excel")


        st.header("Basic Visuals:")

        MOS_vs_Age_gender_based = alt.Chart(Patient_one_time).mark_circle(size = 60).encode(
            x = "Age",
            y = "MOS_total",
            color = "Gender",
            tooltip = ["STAI-T/T-Werte", "PostOPFrage", "Sedierung erhalten", "Mepivacain 1%/ml", "NRS max"]
        ).properties(
            title = "Number of Stress Moments vs. Age based (gender color-coded)"
        ).interactive()
        MOS_vs_Age_gender_based.configure_header(
            titleColor='black',
            titleFontSize=14,
        )

        st.altair_chart(MOS_vs_Age_gender_based, use_container_width=True)


        st.header("One-time Measurement Analysis")

        col1, col2 = st.columns(2, gap="medium")

        with col1:

            options_one = Patient_one_time.columns
            var1 = st.selectbox("Please select the Measurement variable you want to visualize on the X-axis",
                         options = options_one)
            var1_series = Patient_one_time[var1]

        with col2:

            options_two = Patient_one_time.columns
            var2 = st.selectbox("Please select the Stress variables you want to visualize on the Y-axis",
                         options=options_two)
            var2_series = Patient_one_time[var2]

        try:

            #st.write(Patient_one_time)

            if var1 == "ID":
                combined_plot = alt.Chart(Patient_one_time).mark_circle(size=60).encode(
                    x=alt.X(var1, sort = ['Pat.1, Pat.2']),
                    y=var2,
                    tooltip=["ID", "Gender", "STAI-T/T-Werte", "PostOPFrage", "Sedierung erhalten", "Mepivacain 1%/ml",
                             "NRS max"]
                ).interactive()

            #elif var2 == "ID":
            #    combined_plot = alt.Chart(Patient_one_time).mark_circle(size=60).encode(
            #        x = var1,
            #        y=alt.Y(var2, sort = ['Pat.1, Pat.2']),
            #        tooltip=["ID", "Gender", "STAI-T/T-Werte", "PostOPFrage", "Sedierung erhalten", "Mepivacain 1%/ml",
            #                 "NRS max"]
            #    ).interactive()

            else:
                combined_plot = alt.Chart(Patient_one_time).mark_circle(size = 60).encode(
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

                combined_plot = alt.Chart(Patient_one_time).mark_circle(size=60).encode(
                    x=var1,
                    y=var2,
                    color = var3
                ).interactive()

                st.altair_chart(combined_plot, use_container_width=True)


        except st.StreamlitAPIException:
            st.info("You need to select two different columns to display")

    section_based_analysis_checkbox = st.sidebar.checkbox("Section-based Stress Analysis")
    if section_based_analysis_checkbox:

        st.header("Section-based Analysis")

        st.subheader("Calculate own MOS / time interval for desired section:")

        MOS_sections = Patient_stress[["MOS_total_old", "MOS_total_new", "MOS_HS_HS5min_old", "MOS_HS_HS5min_new",
                                       "MOS_T1_T2_old", "MOS_T1_T2_new",
                                       "MOS_T2_T3_old", "MOS_T2_T3_new",
                                       "MOS_T3_T4_old", "MOS_T3_T4_new",
                                       "MOS_T4_T5_old", "MOS_T4_T5_new",
                                       "MOS_T5_T6_old", "MOS_T5_T6_new"]]

        MOS_section_options = MOS_sections.columns
        MOS_stress_section = st.selectbox("Select Column for Section you want to calculate Stress Moments for: ",
                                          options=MOS_section_options)

        # user-defined time duration for MOS per time interval calculation (e.g. number of MOS per second)
        time_duration = st.number_input(
            "Please specify the time interval (in seconds) for which you want the number of Stress Moments", value=1)

        stress_subset_py_calc = MOS_per_time_interval(Patient_stress,
                                                      MOS_stress_section=MOS_stress_section,
                                                      colName=f"{MOS_stress_section}/{time_duration}s",
                                                      time_interval=time_duration)

        rel_cols_stress_subset = stress_subset_py_calc[["ID", "Gender", "Age", f"{MOS_stress_section}/{time_duration}s"]]
        st.write(rel_cols_stress_subset)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            rel_cols_stress_subset.to_excel(writer, index = False, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name=f"Stress-section-{MOS_stress_section}-timeInterval-{time_duration}-seconds.xlsx",
                                            mime="application/vnd.ms-excel")

        st.write("Average number of Stress moments per", time_duration, "seconds for interval ", MOS_stress_section,
                 " is:", stress_subset_py_calc[f"{MOS_stress_section}/{time_duration}s"].mean())

        # st.write(stress_subset_py_calc)

        # TODO - get mean & standard deviation

        st.header("Trimmed Stress Subset: ")

        st.write(stress_subset)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            stress_subset.to_excel(writer, index = False, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name=f"Stress-subset-new-Algorithm.xlsx",
                                            mime="application/vnd.ms-excel")

        st.write("Average number of Stress moments per second over whole OP is: ", stress_subset['MOS/s'].mean())

        # TODO - throw these average and std calculations into one function, where columns can be selected and calculations are done

        MOS_total_mean = stress_subset['MOS/s'].mean()
        MOS_total_std = stress_subset['MOS/s'].std()

        HS_HS5_mean = stress_subset['HS_HS5/s'].mean()
        HS_HS5_std = stress_subset['HS_HS5/s'].std()

        T1_T2_mean = stress_subset['T1_T2/s'].mean()
        T1_T2_std = stress_subset['T1_T2/s'].std()

        T2_T3_mean = stress_subset['T2_T3/s'].mean()
        T2_T3_std = stress_subset['T2_T3/s'].std()

        T3_T4_mean = stress_subset['T3_T4/s'].mean()
        T3_T4_std = stress_subset['T3_T4/s'].std()

        T4_T5_mean = stress_subset['T4_T5/s'].mean()
        T4_T5_std = stress_subset['T4_T5/s'].std()

        T5_T6_mean = stress_subset['T5_T6/s'].mean()
        T5_T6_std = stress_subset['T5_T6/s'].std()

        sections = list(stress_subset.loc[:, ~stress_subset.columns.isin(["ID", "Gender", "Age", "MOS_total", "HS_HS5", "T1_T2",
                                                                          "T2_T3", "T3_T4", "T4_T5", "T5_T6"])].columns)

        section_mean_std_df = pd.DataFrame(columns = sections)
        section_means = [MOS_total_mean, HS_HS5_mean, T1_T2_mean, T2_T3_mean, T3_T4_mean, T4_T5_mean, T5_T6_mean]
        section_stds = [MOS_total_std, HS_HS5_std, T1_T2_std, T2_T3_std, T3_T4_std, T4_T5_std, T5_T6_std]
        section_mean_std_df.loc["mean"] = section_means
        section_mean_std_df.loc["std"] = section_stds
        #datf.append(section_stds)

        #st.write("Long Format", section_mean_std_df_long)

        st.subheader("Mean & Standard Deviation Stress Moments per second for each Section: ")
        st.write(section_mean_std_df)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            section_mean_std_df.to_excel(writer, index = False, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name=f"mean_std_per_second_per_section.xlsx",
                                            mime="application/vnd.ms-excel")

        ### long format to plot mean & std for each section
        section_mean_std_df_long = pd.DataFrame(columns = ["Section", "Mean", "StandardDev"])
        section_mean_std_df_long["Section"] = ["MOS_total", "HS_HS5", "T1_T2","T2_T3", "T3_T4", "T4_T5", "T5_T6"]
        section_mean_std_df_long["Mean"] = section_means
        section_mean_std_df_long["StandardDev"] = section_stds

        section_mean_std_df_long_grouped_bar = section_mean_std_df_long.melt(id_vars="Section", value_vars=["Mean", "StandardDev"])
        #st.write(section_mean_std_df_long.melt(id_vars="Section", value_vars=["Mean", "StandardDev"]))

        st.subheader("Bar Chart Display of Mean & Standard Deviation for each Section")

        section_based_barChart_grouped = alt.Chart(section_mean_std_df_long_grouped_bar).mark_bar().encode(
            x = "Section:N",
            y = "value:Q",
            color = "variable:N",
            column = "variable:N"
        )

        st.altair_chart(section_based_barChart_grouped, use_container_width=True)



        #section_based_barChart = alt.Chart(section_mean_std_df_long).mark_bar().encode(
        #    x = "Section:N",
        #    y = "Mean:Q"
        #)

        #st.altair_chart(section_based_barChart, use_container_width=True)

        # TODO -- combine mean and standard deviation measurements for each section into one dataframe


        # TODO - average and std per participant (for each row)

        patient_stress_sections = stress_subset.loc[:, ~stress_subset.columns.isin(["Gender", "Age", "MOS_total", "HS_HS5",
                                                                                    "MOS/s",
                                                                                    "T1_T2", "T2_T3",
                                                                                    "T3_T4", "T4_T5", "T5_T6"])]

        st.write("Patient Stress Section Data for Mean and Standard Deviation Calculation: ", patient_stress_sections)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            patient_stress_sections.to_excel(writer, index = False, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name=f"mean_std_per_second_per_patient_and_section.xlsx",
                                            mime="application/vnd.ms-excel")

        patient_means_stds = stress_subset[["ID"]]

        # Patient Mean and Standard Deviation over all sections
        patient_means_stds["PatMean"] = patient_stress_sections.mean(axis = 1)
        patient_means_stds["PatStd"] = patient_stress_sections.std(axis=1)

        #st.subheader("Mean and Standard Deviation per Patient:")
        #st.write(patient_means_stds)

        # TODO - creating the desired form of the dataframe with pd.pivot() would be a more elegant solution
        patients = list(Patient_one_time["ID"].unique())
        patient_mean_std_df = pd.DataFrame(columns = patients)
        patient_means = list(patient_means_stds["PatMean"])
        patient_stds = list(patient_means_stds["PatStd"])

        patient_mean_std_df.loc["mean"] = patient_means
        patient_mean_std_df.loc["std"] = patient_stds
        #section_means = [MOS_total_mean, HS_HS5_mean, T1_T2_mean, T2_T3_mean, T3_T4_mean, T4_T5_mean, T5_T6_mean]
        #section_stds = [MOS_total_std, HS_HS5_std, T1_T2_std, T2_T3_std, T3_T4_std, T4_T5_std, T5_T6_std]

        #patient_mean_std_df_pivot = patient_means_stds.pivot(index = ["PatMean", "PatStd"], columns = ["ID"])
        #st.write(patient_mean_std_df_pivot)

        st.subheader("Mean & Standard Deviation Stress Moments per second for each Patient: ")

        st.write(patient_mean_std_df)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            patient_mean_std_df.to_excel(writer, index = False, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name=f"mean_std_per_second_per_patient.xlsx",
                                            mime="application/vnd.ms-excel")


        #st.subheader("Mean and Standard Deviation per Patient:")
        #st.write(patient_means_stds)

        stress_subset_cols = patient_stress_sections[["HS_HS5/s", "T1_T2/s", "T2_T3/s",
          "T3_T4/s", "T4_T5/s", "T5_T6/s"]].columns

        patient_stress_sections_long = pd.melt(patient_stress_sections, id_vars = ['ID'],
                                               value_vars = ["HS_HS5/s", "T1_T2/s", "T2_T3/s",
                                                             "T3_T4/s", "T4_T5/s", "T5_T6/s"],
                                               var_name = "Section", value_name = "MOS/s")

        #st.write("Patient_stress_section_long: ", patient_stress_sections_long)

        selected_section = st.sidebar.radio(
            "Select Section to display Stress level: ",
            #    key="visibility",
            options=stress_subset_cols,
        )

        #st.write(patient_stress_sections_long[patient_stress_sections_long['Section'] == selected_section]['MOS/s'])
        sub_patient_stress_sections_long = patient_stress_sections_long[patient_stress_sections_long['Section'] == selected_section]

        #st.write(patient_stress_sections_long['MOS/s'])

        st.subheader("Bar Chart displaying Number of MOS per Patient, for selected Section:")

        bars_sections = alt.Chart(sub_patient_stress_sections_long).mark_bar().encode(
            x = alt.X("ID:N", sort = ['Pat.1, Pat.2']),
            #y = alt.Y(f"{patient_stress_sections_long[patient_stress_sections_long['Section'] == selected_section]['MOS/s']}:Q", sort = 'ascending')
            y=alt.Y("MOS/s:Q", sort='ascending')
        )

        add_means = st.checkbox("Add Section Mean:")

        if add_means:
            section_mean = section_mean_std_df[[selected_section]].head(1)
            #st.write(section_mean)
            section_std = section_mean_std_df[[selected_section]].tail(1)
            #st.write(section_std)
            #section_mean_std = section_mean[selected_section] + (2 * section_std[selected_section])
            #st.write(section_mean_std)
            section_mean_value = section_mean[selected_section].values[0]

            mean_line = alt.Chart(section_mean).mark_rule(color = "red").encode(y = selected_section)
            #mean_text = alt.Chart(section_mean).mark_text(
            #    text = f"Section {selected_section} with Mean: {section_mean_value}",
            #    align="right",
            #    baseline = "bottom"
            #)
            #mean_line = alt.Chart().mark_rule().encode(y = alt.datum(section_mean_value))

            #bars_sections.configure_header(
            #    title=f"Section {selected_section} with Mean: {section_mean_value}")


            barChart = (bars_sections + mean_line)

            #st.altair_chart(barChart)

        else:
            barChart = bars_sections



        ###################### TODOs ######################

        # TODO - add section mean based on 'section_mean_std_df' -- columns are sections & 1st row = mean, 2nd row = std
        # TODO - make all the tables downloadable as excel


        #st.altair_chart(barChart)
        st.altair_chart(barChart, use_container_width=True)

        #threshold = pd.DataFrame([{"threshold": 90}])

        #bars = alt.Chart(source).mark_bar().encode(
        #    x="year:O",
        #    y="wheat:Q",
        #)

        #highlight = alt.Chart(source).mark_bar(color="#e45755").encode(
        #    x='year:O',
        #    y='baseline:Q',
        #    y2='wheat:Q'
        #).transform_filter(
        #    alt.datum.wheat > 90
        #).transform_calculate("baseline", "90")

        #rule = alt.Chart(threshold).mark_rule().encode(
        #    y='threshold:Q'
        #)

        #(bars + highlight + rule).properties(width=600)


        # TODO - plot Mean of number of Stress sections (y-axis) vs. each section (on x-axis)









        col_sec1, col_sec2 = st.columns(2, gap="medium")






st.sidebar.subheader("Signal Visualization")

visualize_eda = st.sidebar.checkbox("Visualize EDA recordings for a specific patient: (Note: this takes some time to process)")

if visualize_eda:

    patients = list(Patient_one_time["ID"].unique())

    selected_patient = st.sidebar.radio(
        "Set Patient for which sensor measurements should be displayed: ",
        #    key="visibility",
        options=patients,
    )

    uploaded_signal_measurements = st.file_uploader("Upload the Excel file with the combined sensor measurements", type=["xlsx", "csv"],
                                          accept_multiple_files=False)

    if uploaded_signal_measurements is not None:
        st.markdown("# Drag and drop the Stress Output .xlsx file and explore correlations:")

        save_uploadedfile(uploaded_file=uploaded_signal_measurements, path=path)
        file_extension = uploaded_signal_measurements.name.split(".")[-1]
        st.write("File Type is", file_extension)
        file_name_signals = uploaded_signal_measurements.name.split(".")[0] + "." + uploaded_signal_measurements.name.split(".")[1]

        #st.write("Data File name: ", file_name_signals)

        path_to_signals_file = str(path) + "/" + file_name_signals

        st.write(path_to_signals_file)

        # TODO - try to adjust import subset of one patient
        # Example(s): https://programtalk.com/python-more-examples/streamlit.file_uploader/

        if file_extension == "xlsx":
            sensor_measurements = pd.read_excel(path_to_signals_file)

            st.write(sensor_measurements.head())

            sensor_measurements_filtered = sensor_measurements[sensor_measurements["ID"] == selected_patient]

            st.write(sensor_measurements_filtered)

            eda_visual = st.sidebar.checkbox(f"Visualize EDA measurement of patient: {selected_patient}")

            if eda_visual:
                EDA_plot = alt.Chart(sensor_measurements_filtered).mark_area().encode(
                    x = "time_iso:T",
                    y = "EDA:Q"
                ).interactive()

                st.altair_chart(EDA_plot, use_container_width=True)

        elif file_extension == "csv":
            sensor_measurements = pd.read_csv(path_to_signals_file, delimiter=";")
            #iter_csv = pd.read_csv(path_to_signals_file, iterator=True, chunksize=30000)
            #sensor_measurements = pd.concat([chunk[chunk['ID'] == selected_patient] for chunk in iter_csv])

            st.write(sensor_measurements)



        #patients = list(sensor_measurements["ID"].unique())

        #if "visibility" not in st.session_state:
        #    st.session_state.visibility = "visible"
        #    st.session_state.disabled = False

        #st.sidebar.checkbox("Disable Patient selection:", key = "disabled")

        #st.radio(
        #    "Set Patient for which sensor measurements should be displayed: ",
        #    key="visibility",
        #    options=patients,
        #)








