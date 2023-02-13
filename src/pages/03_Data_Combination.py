# Contents of ~/my_app/pages/page_3.py
import streamlit as st
from pathlib import Path
import os
import pandas as pd
import numpy as np
from io import BytesIO

# temporarily saves the file
def save_uploadedfile(uploaded_file, path: str):
    with open(os.path.join(path, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())

    return st.success("Temporarily saved file: {} to {}".format(uploaded_file.name, path))



st.markdown("# Drag and drop a .csv or .xlsx file and explore correlations:")

path = Path(__file__).parent.resolve()


uploaded_stress_file = st.file_uploader("Upload your Stress Detection file here ...", type=["xlsx"],
                                          accept_multiple_files=False)


uploaded_data_file = st.file_uploader("Drag and drop your file here ...", type=["csv", "xlsx"],
                                          accept_multiple_files=False)

if (uploaded_data_file is not None) and (uploaded_stress_file is not None):

    # save locally to access it
    save_uploadedfile(uploaded_file=uploaded_data_file, path=path)
    save_uploadedfile(uploaded_file=uploaded_stress_file, path=path)
    #file_extension = uploaded_data_file.name.split(".")[-1]
    file_name_data = uploaded_data_file.name.split(".")[0] + "." + uploaded_data_file.name.split(".")[1]
    file_name_stress = uploaded_stress_file.name.split(".")[0] + "." + uploaded_stress_file.name.split(".")[1]
    st.write("Data File name", file_name_data)
    st.write("Stress File name", file_name_stress)

    #saved_folder_path = str(path) + "\\" + file_name_data
    #st.write("saved_folder_path", saved_folder_path)

    path_to_data_file = str(path) + "\\" + file_name_data
    path_to_stress_file = str(path) + "\\" + file_name_stress

    sheets_dict = pd.read_excel(path_to_data_file,
                                sheet_name=['PatInfos','PatData'])

    Patient_infos = sheets_dict.get("PatInfos")
    Patient_data = sheets_dict.get("PatData")

    Stress_data = pd.read_excel(path_to_stress_file)

    st.write("List of Patients \n", Patient_infos)

    st.write("Patient Data \n", Patient_data)

    st.write("Stress Data \n", Stress_data)

    psycho_cols = [col for col in Patient_data if col.startswith("STAI")]
    #st.write("Columns starting with 'STAI' - Psychology related ",psycho_cols)

    T1_cols = [col for col in Patient_data if "T1" in col]
    #st.write("Columns containing 'T1' = 'Abdeckung steril' ", T1_cols)
    T2_cols = [col for col in Patient_data if "T2" in col]
    #st.write("Columns containing 'T2' = 'Lokalanästhesie'", T2_cols)
    T3_cols = [col for col in Patient_data if "T3" in col]
    #st.write("Columns containing 'T3' = 'Hautschnitt'", T3_cols)
    T4_cols = [col for col in Patient_data if "T4" in col]
    #st.write("Columns containing 'T4 = 'Implantation''", T4_cols)
    T5_cols = [col for col in Patient_data if "T5" in col]
    #st.write("Columns containing 'T5 = 'Naht ''", T5_cols)
    T6_cols = [col for col in Patient_data if "T6" in col]
    #st.write("Columns containing 'T6' = 'Entfernen der Abdeckung'", T6_cols)



    HS_cols = [col for col in Patient_data if "HS" in col and "5" not in col]
    #st.write("Hautschnitt columns", HS_cols)
    five_mins_HS_cols = [col for col in Patient_data if "5min" in col]
    #st.write("Hautschnitt after 5 mins columns", five_mins_HS_cols)

    vorgang_options = list(Stress_data[~Stress_data['Vorgang'].isna()]['Vorgang'].unique())
    #st.write(vorgang_options)

    patient_measurements = []
    measurements_HS_5mins_past = []
    measurements_section_times = []

    for index in Patient_data.index:

        patient_id = Patient_data['Lfd. Patiennr.'][index]
        stress_subset = Stress_data[Stress_data["ID"] == patient_id]
        st.write("Patient Subset", stress_subset)

        st.write("List of Vorgang values in file # ", patient_id, "is: ", list(stress_subset["Vorgang"].unique()))

        # TODO -- add this .values[0]

        try:

            patient_id_HS_ts = stress_subset[stress_subset["Vorgang"] == "Hautschnitt"]["time_iso"].values[0]
            patient_id_T1_ts = stress_subset[stress_subset["Vorgang"] == "Abdeckung steril"]["time_iso"].values[0]
            patient_id_T2_ts = stress_subset[stress_subset["Vorgang"] == "Lokalanästhesie"]["time_iso"].values[0]
            patient_id_T3_ts = stress_subset[stress_subset["Vorgang"] == "Hautschnitt"]["time_iso"].values[0]
            patient_id_T4_ts = stress_subset[stress_subset["Vorgang"] == "Implantation"]["time_iso"].values[0]
            patient_id_T5_ts = stress_subset[stress_subset["Vorgang"] == "Naht "]["time_iso"].values[0]
            patient_id_T6_ts = stress_subset[stress_subset["Vorgang"] == "Entfernen der Abdeckung"]["time_iso"].values[0]

            st.write("Timestamp  ", stress_subset[stress_subset["Vorgang"] == "Hautschnitt"]["time_iso"])

            # FIXME -- looks like there is no 'time_iso' value for filtering stress_subset["Vorgang"] == "Hautschnitt"


            st.write("Hautschnitt Uhrzeit timestamp", patient_id_HS_ts)
            patient_id_HS_ts_plus5 = patient_id_HS_ts + pd.to_timedelta(5, 'm')
            #st.write(patient_id_HS_ts_plus5)
            st.write("5 mins after Hautschnitt Uhrzeit timestamp", patient_id_HS_ts_plus5)

            #temp_data = pd.DataFrame( {"ID": [patient_id, patient_id],
            #                           "Uhrzeit": [patient_id_HS_ts, patient_id_HS_ts_plus5],
            #                           "StressHS": [Patient_data['StressHS'][index], 0],
            #                           "RRsysHS": [Patient_data['RRsysHS'][index], Patient_data['RRsysHS5min'][index]],
            #                           "RRsysT3": [Patient_data['RRsysT3'][index], 0],
            #                           "RRdiaHS": [Patient_data['RRdiaHS'][index], Patient_data['RRdiaHS5min'][index]],
            #                           "RRdiaT3": [Patient_data['RRdiaT3'][index], 0],
            #                           "RRmeanHS": [Patient_data['RRmeanHS'][index], Patient_data['RRmeanHS5min'][index]],
            #                           "RRmeanT3": [Patient_data['RRmeanT3'][index], 0],
            #                           "HFHS": [Patient_data['HFHS'][index], Patient_data['HFHS5min'][index]],
            #                           "HFT3": [Patient_data['HFT3'][index], 0],
            #                           "SpO2HS": [Patient_data['SpO2HS'][index], Patient_data['SpO2HS5min'][index]],
            #                           "SpO2T3": [Patient_data['SpO2T3'][index], 0],
            #                           "BISHS": [Patient_data['BISHS'][index], Patient_data['BISHS5min'][index]] } )

            temp_data = pd.DataFrame( {"ID": [patient_id, patient_id],
                                       "Uhrzeit": [patient_id_HS_ts, patient_id_HS_ts_plus5],
                                       "RRsysHS": [Patient_data['RRsysHS'][index], Patient_data['RRsysHS5min'][index]],
                                       "RRdiaHS": [Patient_data['RRdiaHS'][index], Patient_data['RRdiaHS5min'][index]],
                                       "RRmeanHS": [Patient_data['RRmeanHS'][index], Patient_data['RRmeanHS5min'][index]],
                                       "HFHS": [Patient_data['HFHS'][index], Patient_data['HFHS5min'][index]],
                                       "SpO2HS": [Patient_data['SpO2HS'][index], Patient_data['SpO2HS5min'][index]],
                                       "BISHS": [Patient_data['BISHS'][index], Patient_data['BISHS5min'][index]] } )

            #st.write("Data at HS time and 5 mins after", temp_data.replace(0, np.nan))
            #temp_data_replaced = temp_data.replace(0, np.nan)
            measurements_HS_5mins_past.append(temp_data)

            T_temp_data = pd.DataFrame( {"ID": [patient_id, patient_id, patient_id, patient_id, patient_id, patient_id],
                                         "Uhrzeit": [patient_id_T1_ts, patient_id_T2_ts, patient_id_T3_ts, patient_id_T4_ts, patient_id_T5_ts, patient_id_T6_ts],
                                         "RRsys": [Patient_data['RRsysT1'][index], Patient_data['RRsysT2'][index], Patient_data['RRsysT3'][index], Patient_data['RRsysT4'][index], Patient_data['RRsysT5'][index], Patient_data['RRsysT6'][index]],
                                         "RRdia": [Patient_data['RRdiaT1'][index], Patient_data['RRdiaT2'][index], Patient_data['RRdiaT3'][index], Patient_data['RRdiaT4'][index], Patient_data['RRdiaT5'][index], Patient_data['RRdiaT6'][index]],
                                         "RRmean": [Patient_data['RRmeanT1'][index], Patient_data['RRmeanT2'][index], Patient_data['RRmeanT3'][index], Patient_data['RRmeanT4'][index], Patient_data['RRmeanT5'][index], Patient_data['RRmeanT6'][index]],
                                         "HF": [Patient_data['HFT1'][index], Patient_data['HFT2'][index], Patient_data['HFT3'][index], Patient_data['HFT4'][index], Patient_data['HFT5'][index], Patient_data['HFT6'][index]],
                                         "SpO2": [Patient_data['SpO2T1'][index], Patient_data['SpO2T2'][index], Patient_data['SpO2T3'][index], Patient_data['SpO2T4'][index], Patient_data['SpO2T5'][index], Patient_data['SpO2T6'][index]],
                                         "BIS": [Patient_data['BIST1'][index], Patient_data['BIST2'][index], Patient_data['BIST3'][index], Patient_data['BIST4'][index], Patient_data['BIST5'][index], Patient_data['BIST6'][index]]
                                         })

            #st.write("Values measured at given Section times: ", T_temp_data)
            measurements_section_times.append(T_temp_data)

            general_info_temp_data = pd.DataFrame( {"ID": patient_id,
                                                    "STAI-T": [Patient_data['STAI-T'][index]],
                                                    "STAI-T/T-Werte": [Patient_data['STAI-T/T-Werte'][index]],
                                                    "STAI-S1": [Patient_data['STAI-S1'][index]],
                                                    "STAI-S2": [Patient_data['STAI-S2'][index]],
                                                    "PostOPFrage": [Patient_data['PostOPFrage'][index]],
                                                    "IL-6 in pg/ml": [Patient_data['IL-6 in pg/ml'][index]],
                                                    "Cortisol in ng/ml": [Patient_data['Cortisol in ng/ml'][index]],
                                                    "Sedierung erhalten": [Patient_data['Sedierung erhalten'][index]],
                                                    "Mepivacain 1%/ml": [Patient_data['Mepivacain 1%/ml'][index]],
                                                    "NRS max": [Patient_data['NRS max'][index]],
                                                    "NRS PACU": [Patient_data['NRS PACU'][index]],
                                                    "BISmin": [Patient_data['BISmin'][index]],
                                                    "BISmax": [Patient_data['BISmax'][index]],
                                                    } )

            #st.write("General Values: ", general_info_temp_data)
            patient_measurements.append(general_info_temp_data)

        except IndexError:
            st.write("Index Error when trying to extract 'time_iso' value for timestamp at Patient ID # ", patient_id)
            st.write("Timestamp  ", stress_subset[stress_subset["Vorgang"] == "Hautschnitt"]["time_iso"])

    st.header("Final Data:")

    patient_measurements_combined = pd.concat(patient_measurements)
    st.write("Patient measurements", patient_measurements_combined)

    measurements_HS_5mins_past_combined = pd.concat(measurements_HS_5mins_past)
    st.write("Patient measurements at Hautschnitt and 5 minutes afterwards", measurements_HS_5mins_past_combined)

    measurements_section_times_combined = pd.concat(measurements_section_times)
    st.write("Patient measurements at sections times", measurements_section_times_combined)

    if st.sidebar.checkbox("Download combined Patient measurements:"):
        # download detected MOS based on Kyriakou et al. 2019
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            patient_measurements_combined.to_excel(writer, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name="PatientMeasurements.xlsx",
                                            mime="application/vnd.ms-excel")

    if st.sidebar.checkbox("Measurements Hautschnitt:"):
        # download detected MOS based on Kyriakou et al. 2019
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            measurements_HS_5mins_past_combined.to_excel(writer, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name="Masurements_HS_HS5_times.xlsx",
                                            mime="application/vnd.ms-excel")


    if st.sidebar.checkbox("Download measurements based on section times:"):
        # download detected MOS based on Kyriakou et al. 2019
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            measurements_section_times_combined.to_excel(writer, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name="Masurements_section_times.xlsx",
                                            mime="application/vnd.ms-excel")



    # TODO - write download options for files:




    #HS_ts = st.number_input("Number of minutes to extract after a specific 'Vorgang':",
    #                               value=5)

    #HS_ts_5mins = vorgang_selection_ts + pd.to_timedelta(5, 'm')



    # TODO - check if we can manage timestamps / map timestamps with partial column name matching

    # TODO - S1 = before OP
    # TODO - S2 = during OP
    # TODO - PostOPFrage = Sum over questionnaire (high value if OP was stressful for patient)
    # TODO - Interleukin 6 (IL-6 in pg/ml) und Cortisol (Cortisol in ng/ml) = right after OP
    # TODO - Mepivacain 1%/ml = Lokalanästhethikum used (could re-check to see what patients received a follow-up doses)
    # TODO - NRS columns indicates perceived pain, NRS PACU = maximum pain in wake-up room, NRS max = maximum pain during OP
    # TODO - timespans between Hautschnitt (HS) and 5 mins afterwards
    #           Blood pressure values (RR) - systolic, diastolys, middle pressure, oxygen saturation (SpO2), heart beart (HF), BIS (Bispektralanalyse based on EEG)
    #           all values were recorded at Hautschnitt time (HS) and 5 mins afterwards -- additional values for difference between the values
    # TODO - Blood pressure values (RR) - systolic, diastolys, middle pressure, oxygen saturation (SpO2), heart beart (HF), BIS (Bispektralanalyse based on EEG)
    #           all values at Section points
    #           T1 = 'Abdeckung steril'
    #           T2 = 'Lokalanästhesie'
    #           T3 = 'Hautschnitt'
    #           T4 = 'Implantation'
    #           T5 = 'Naht '
    #           T6 = 'Entfernen der Abdeckung'

    # TODO - use output file from Stress Detection and load this dataset

    # TODO - for specific Patient ID (filter for ID), get time of Hautschnitt, and then add 5 mins to this timestamp to get second measurement time

    # Vorgang values
    #0: "Eintritt OP Bereich"
    #1: "Wartezeit "
    #2: "Einschleusen"
    #3: "Abdeckung steril"
    #4: "Lokalanästhesie"
    #5: "Hautschnitt"
    #6: "Implantation"
    #7: "Naht "
    #8: "Entfernen der Abdeckung"
    #9: "Verlassen OP/Beginn PACU postOP"

    #pd.read_csv("combined_MOS_file.csv")

