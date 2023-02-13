import streamlit as st
from pathlib import Path
import os
import pandas as pd
import numpy as np
from io import BytesIO

# temporarily saves the file
@st.cache
def save_uploadedfile(uploaded_file, path: str):
    with open(os.path.join(path, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())

st.markdown("# Drag and drop the Stress Output .xlsx file and calculate Number of MOS based on OP Sections:")


path = Path(__file__).parent.resolve()



uploaded_stress_file = st.file_uploader("Upload your Stress Detection file here ...", type=["xlsx"],
                                          accept_multiple_files=False)

def MOS_time_sections(data, ts_col1, ts_col2):

    df = data.copy()
    df.set_index('time_iso', inplace = True)
    section_subset = df[ts_col1:ts_col2]
    section_subset_mos = section_subset[section_subset['detectedMOS'] == 1]
    mos_cnt = len(section_subset_mos)
    df.reset_index()

    return mos_cnt




if uploaded_stress_file is not None:

    save_uploadedfile(uploaded_file=uploaded_stress_file, path=path)

    file_name_stress = uploaded_stress_file.name.split(".")[0] + "." + uploaded_stress_file.name.split(".")[1]

    st.write("Stress File name", file_name_stress)

    path_to_stress_file = str(path) + "\\" + file_name_stress

    st.write('path_to_stress_file', path_to_stress_file)

    Stress_data = pd.read_excel(path_to_stress_file)

    st.write("Stress Data \n", Stress_data)

    patient_ids = list(Stress_data['ID'].unique())

    #st.write(patient_ids)

    problem_files = []

    patients_MOS = []

    for patient_id in patient_ids:
        stress_subset = Stress_data[Stress_data["ID"] == patient_id]
        st.write("Patient Subset", stress_subset)
        available_sections = list(stress_subset['Vorgang'].unique())
        #st.write(available_sections)

        MOS_cnt_total = len(stress_subset[stress_subset['detectedMOS'] == 1])

        if "Hautschnitt" in available_sections:
            try:
                patient_id_HS_ts = stress_subset[stress_subset["Vorgang"] == "Hautschnitt"]["time_iso"].values[0]
                patient_id_HS_ts_plus5 = patient_id_HS_ts + pd.to_timedelta(5, 'm')

                patient_id_T1_ts = stress_subset[stress_subset["Vorgang"] == "Abdeckung steril"]["time_iso"].values[0]
                patient_id_T2_ts = stress_subset[stress_subset["Vorgang"] == "Lokalanästhesie"]["time_iso"].values[0]
                patient_id_T3_ts = stress_subset[stress_subset["Vorgang"] == "Hautschnitt"]["time_iso"].values[0]
                patient_id_T4_ts = stress_subset[stress_subset["Vorgang"] == "Implantation"]["time_iso"].values[0]
                patient_id_T5_ts = stress_subset[stress_subset["Vorgang"] == "Naht "]["time_iso"].values[0]
                patient_id_T6_ts = stress_subset[stress_subset["Vorgang"] == "Entfernen der Abdeckung"]["time_iso"].values[0]

                st.write("Timestamp Hautschnitt: ", patient_id_HS_ts)
                st.write("Timestamp Hautschnitt + 5 Minutes: ", patient_id_HS_ts_plus5)

                MOS_HS_HS5min = MOS_time_sections(stress_subset, patient_id_HS_ts, patient_id_HS_ts_plus5)
                MOS_T1_T2 = MOS_time_sections(stress_subset, patient_id_T1_ts, patient_id_T2_ts)
                MOS_T2_T3 = MOS_time_sections(stress_subset, patient_id_T2_ts, patient_id_T3_ts)
                MOS_T3_T4 = MOS_time_sections(stress_subset, patient_id_T3_ts, patient_id_T4_ts)
                MOS_T4_T5 = MOS_time_sections(stress_subset, patient_id_T4_ts, patient_id_T5_ts)
                MOS_T5_T6 = MOS_time_sections(stress_subset, patient_id_T5_ts, patient_id_T6_ts)

                st.write("Number of MOS between Hautschnitt and 5 Minutes afterwards: ", MOS_time_sections(stress_subset, patient_id_HS_ts, patient_id_HS_ts_plus5))

                if "moser" in file_name_stress:

                    temp_data_Moser = pd.DataFrame( {"ID": [patient_id],
                                               "MOS_total_new": [MOS_cnt_total],
                                               "MOS_HS_HS5min_new": [MOS_HS_HS5min],
                                               "MOS_T1_T2_new": [MOS_T1_T2],
                                               "MOS_T2_T3_new": [MOS_T2_T3],
                                               "MOS_T3_T4_new": [MOS_T3_T4],
                                               "MOS_T4_T5_new": [MOS_T4_T5],
                                               "MOS_T5_T6_new": [MOS_T5_T6] } )

                    patients_MOS.append(temp_data_Moser)

                elif "kyriakou" in file_name_stress:

                    temp_data_Kyriakou = pd.DataFrame( {"ID": [patient_id],
                                               "MOS_total_old": [MOS_cnt_total],
                                               "MOS_HS_HS5min_old": [MOS_HS_HS5min],
                                               "MOS_T1_T2_old": [MOS_T1_T2],
                                               "MOS_T2_T3_old": [MOS_T2_T3],
                                               "MOS_T3_T4_old": [MOS_T3_T4],
                                               "MOS_T4_T5_old": [MOS_T4_T5],
                                               "MOS_T5_T6_old": [MOS_T5_T6] } )

                    patients_MOS.append(temp_data_Kyriakou)

            except IndexError:
                st.write("Index Error in Patient: ", patient_id)

        else:
            problem_files.append(patient_id)


    st.write("Problem Files: ", problem_files)

    output_data = pd.concat(patients_MOS)

    st.write("Section-based MOS Output: ", output_data)

    if st.sidebar.checkbox("Download section-based MOS Output:"):
        # download detected MOS based on Kyriakou et al. 2019
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            output_data.to_excel(writer, sheet_name="Sheet1")

        download_excel = st.download_button(label="Download Excel file", data=buffer,
                                            file_name="Section-based-MOS-Detection.xlsx",
                                            mime="application/vnd.ms-excel")

    #for index in Stress_data.index:
    #    patient_id = Stress_data['ID'][index]
    #    stress_subset = Stress_data[Stress_data["ID"] == patient_id]
    #    st.write("Patient Subset", stress_subset)


    #### Section Timestamps:
    #patient_id_HS_ts = stress_subset[stress_subset["Vorgang"] == "Hautschnitt"]["time_iso"].values[0]
    #patient_id_T1_ts = stress_subset[stress_subset["Vorgang"] == "Abdeckung steril"]["time_iso"].values[0]
    #patient_id_T2_ts = stress_subset[stress_subset["Vorgang"] == "Lokalanästhesie"]["time_iso"].values[0]
    #patient_id_T3_ts = stress_subset[stress_subset["Vorgang"] == "Hautschnitt"]["time_iso"].values[0]
    #patient_id_T4_ts = stress_subset[stress_subset["Vorgang"] == "Implantation"]["time_iso"].values[0]
    #patient_id_T5_ts = stress_subset[stress_subset["Vorgang"] == "Naht "]["time_iso"].values[0]
    #patient_id_T6_ts = stress_subset[stress_subset["Vorgang"] == "Entfernen der Abdeckung"]["time_iso"].values[0]


