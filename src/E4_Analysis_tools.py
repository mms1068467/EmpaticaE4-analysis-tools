import math
import os

import numpy as np
import pandas as pd

import plotly.graph_objects as go
from scipy import signal
from sklearn.preprocessing import StandardScaler, MinMaxScaler


def merge_data(signal_path: str, labels_path: str, signal: str = "HR") -> pd.DataFrame:

    Zeitenauswertung = pd.read_excel(labels_path)

    if signal == "HR":
        HR_prepared = HR_processing(signal_path)
        HR_labeled = pd.merge(HR_prepared, Zeitenauswertung, left_on = "time", right_on = "Uhrzeit", how = "left")
        return HR_labeled

    if signal == "IBI":
        IBI_prepared = IBI_processing(signal_path)
        IBI_labeled = pd.merge(IBI_prepared, Zeitenauswertung, left_on = "time", right_on = "Uhrzeit", how = "left")
        return IBI_labeled

    if signal == "EDA":
        EDA_prepared = EDA_processing(signal_path)
        EDA_labeled = pd.merge(EDA_prepared, Zeitenauswertung, left_on = "time", right_on = "Uhrzeit", how = "left")
        return EDA_labeled

    if signal == "ST":
        ST_prepared = ST_processing(signal_path)
        ST_labeled = pd.merge(ST_prepared, Zeitenauswertung, left_on = "time", right_on = "Uhrzeit", how = "left")
        return ST_labeled

    if signal == "BVP":
        BVP_prepared = BVP_processing(signal_path)
        BVP_labeled = pd.merge(BVP_prepared, Zeitenauswertung, left_on = "time", right_on = "Uhrzeit", how = "left")
        return BVP_labeled

    if signal == "ACC":
        ACC_prepared = ACC_processing(signal_path)
        ACC_labeled = pd.merge(ACC_prepared, Zeitenauswertung, left_on="time", right_on="Uhrzeit", how = "left")
        return ACC_labeled

def preprocess_for_MOS_Detection(data, signal: str):
    if signal == "EDA":
        pass
    if signal == "ST":
        pass
    if signal == "IBI":
        pass
    if signal == "BVP":
        pass

############### Heart Rate (HR) - 1 Hz Sampling Frequency ###############

def HR_processing(path):
    HR = pd.read_csv(path)
    start_time_col = HR.columns[0]
    #print(f"Starting time is {start_time_col}")
    start_time = pd.to_datetime(start_time_col, unit="s") + pd.to_timedelta(2, unit = "h")
    #print(f"Adjusted Starting time is {start_time}")
    HR = HR[1:].reset_index()
    end_time = start_time + pd.to_timedelta(len(HR), unit = 's') + pd.to_timedelta(2, unit = "h")
    oneHz_ts = pd.date_range(start=start_time, end = end_time, freq="s")
    length_difference = len(oneHz_ts) - len(HR)
    HR['datetime'] = oneHz_ts[:-length_difference]
    HR = HR.rename(columns = {start_time_col: "HR"})
    HR["date"] = HR.datetime.dt.date
    HR["time"] = HR.datetime.dt.time
    HR = HR[["datetime", "date", "time", "HR"]]
    HR.to_csv(path.split(".csv")[0] + "_prepared.csv", index_label=False)

    return HR

def plot_HR(HR_labeled, add_tags: bool = False, tags_path: str = None):
    dmin = HR_labeled['HR'].min()
    dmax = HR_labeled['HR'].max()

    figHR = go.Figure(data = go.Scatter(x = HR_labeled['datetime'], y = HR_labeled["HR"], line = dict(color = "red"), name = "Heart Rate (HR) in BPM"))

    figHR.update_xaxes(title_text='Time')
    figHR.update_yaxes(title_text='Heart Rate (BPM)')

    labels = HR_labeled[~HR_labeled["Vorgang"].isna()]

    for index in labels.index:
        figHR.add_trace(go.Scatter(x = [HR_labeled['datetime'][index], HR_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {HR_labeled['Vorgang'][index]}"))

    if add_tags:
        tag_counter = 1
        tags = TAGS_processing(tags_path)
        for index in tags.index:
            figHR.add_trace(go.Scatter(x = [ tags['tag'][index], tags['tag'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'green'), name = f"Tag Number {tag_counter}"))
            tag_counter += 1

    #figHR.show()
    return figHR
############### Interbeat Interval (IBI) – TODO - check recordings ###############

def IBI_processing(path):
    IBI = pd.read_csv(path)
    start_time_col = IBI.columns[0]
    #print(f"Starting time is {start_time_col}")
    start_time = pd.to_datetime(start_time_col, unit="s") + pd.to_timedelta(2, unit = "h")
    #print(f"Adjusted Starting time is {start_time}")
    IBI = IBI[1:].reset_index()
    end_time = start_time + pd.to_timedelta(len(IBI), unit = 's') + pd.to_timedelta(2, unit = "h")
    oneHz_ts = pd.date_range(start=start_time, end = end_time, freq="s")
    length_difference = len(oneHz_ts) - len(IBI)
    IBI['datetime'] = oneHz_ts[:-length_difference]
    IBI = IBI.rename(columns = {start_time_col: "IBI"})
    IBI["date"] = IBI.datetime.dt.date
    IBI["time"] = IBI.datetime.dt.time
    IBI["IBI"] = np.abs(IBI.IBI.diff(1).fillna(0))

    IBI = IBI[["datetime", "date", "time", "IBI"]]
    IBI.to_csv(path.split(".csv")[0] + "_prepared.csv", index_label=False)

    return IBI

def plot_IBI(IBI_labeled, add_tags: bool = False, tags_path: str = None):
    dmin = IBI_labeled['IBI'].min()
    dmax = IBI_labeled['IBI'].max()

    figIBI = go.Figure(data = go.Scatter(x = IBI_labeled['datetime'], y = IBI_labeled["IBI"], line = dict(color = "green"), name = "Interbeat Interval (IBI) in Seconds"))

    figIBI.update_xaxes(title_text='Time')
    figIBI.update_yaxes(title_text='IBI (s)')

    labels = IBI_labeled[~IBI_labeled["Vorgang"].isna()]

    for index in labels.index:
        figIBI.add_trace(go.Scatter(x = [IBI_labeled['datetime'][index], IBI_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {IBI_labeled['Vorgang'][index]}"))

    if add_tags:
        tag_counter = 1
        tags = TAGS_processing(tags_path)
        for index in tags.index:
            figIBI.add_trace(go.Scatter(x = [ tags['tag'][index], tags['tag'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'green'), name = f"Tag Number {tag_counter}"))
            tag_counter += 1

    #figIBI.show()
    return figIBI
    
############### ### Heart Rate Variability (HRV) - derived from IBI values ###############

def get_HRV_from_IBI(IBI_data):

    HRV_data = IBI_data.copy()
    HRV_data["HRV"] = np.abs(HRV_data.IBI.diff(1).fillna(0))

    return HRV_data[["datetime", "date", "time", "HRV", "Vorgang", "Uhrzeit", "Anmerkung"]]



def plot_HRV(HRV_labeled, add_tags: bool = False, tags_path: str = None):
    dmin = HRV_labeled['HRV'].min()
    dmax = HRV_labeled['HRV'].max()

    figHRV = go.Figure(data = go.Scatter(x = HRV_labeled['datetime'], y = HRV_labeled["HRV"], line = dict(color = "red"), name = "Heart Rate Variability (HRV) in Seconds"))

    figHRV.update_xaxes(title_text='Time')
    figHRV.update_yaxes(title_text='HRV (s)')

    labels = HRV_labeled[~HRV_labeled["Vorgang"].isna()]

    for index in labels.index:
        figHRV.add_trace(go.Scatter(x = [HRV_labeled['datetime'][index], HRV_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {HRV_labeled['Vorgang'][index]}"))

    if add_tags:
        tag_counter = 1
        tags = TAGS_processing(tags_path)
        for index in tags.index:
            figHRV.add_trace(go.Scatter(x = [ tags['tag'][index], tags['tag'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'green'), name = f"Tag Number {tag_counter}"))
            tag_counter += 1

    #figHRV.show()
    return figHRV

############### ### Electrodermal Activity (EDA) - 4 Hz Sampling Frequency ###############

def EDA_processing(path):
    EDA = pd.read_csv(path)
    start_time_col = EDA.columns[0]
    start_time = pd.to_datetime(start_time_col, unit="s") + pd.to_timedelta(2, unit = "h")
    EDA = EDA[1:].reset_index()
    length_EDA = math.ceil(len(EDA) / 4)
    end_time = start_time + pd.to_timedelta(length_EDA, unit = 's') + pd.to_timedelta(2, unit = "h")
    fourHz_ts = pd.date_range(start=start_time, end = end_time, freq="250ms")
    length_difference = len(fourHz_ts) - len(EDA)
    EDA['datetime'] = fourHz_ts[:-length_difference]
    EDA = EDA.rename(columns = {start_time_col: "EDA"})
    EDA["date"] = EDA.datetime.dt.date
    EDA["time"] = EDA.datetime.dt.time
    EDA = EDA[["datetime", "date", "time", "EDA"]]

    return EDA

def plot_EDA(EDA_labeled, raw = True, add_tags: bool = False, tags_path: str = None):


    if raw:
        dmin = EDA_labeled['EDA'].min()
        dmax = EDA_labeled['EDA'].max()
        figEDA = go.Figure(data = go.Scatter(x = EDA_labeled['datetime'], y = EDA_labeled["EDA"], line = dict(color = "blue"), name = "Raw Electrodermal Activity (EDA) in mircoSiemens"))

        figEDA.update_xaxes(title_text='Time')
        figEDA.update_yaxes(title_text='Raw EDA (uS)')

    else:
        dmin = EDA_labeled['EDA_filtered'].min()
        dmax = EDA_labeled['EDA_filtered'].max()
        figEDA = go.Figure(data = go.Scatter(x = EDA_labeled['datetime'], y = EDA_labeled["EDA_filtered"], line = dict(color = "blue"), name = "Filtered Electrodermal Activity (EDA) in mircoSiemens"))

        figEDA.update_xaxes(title_text='Time')
        figEDA.update_yaxes(title_text='Filtered EDA (uS)')

    labels = EDA_labeled[~EDA_labeled["Vorgang"].isna()]

    for index in labels.index:
        figEDA.add_trace(go.Scatter(x = [EDA_labeled['datetime'][index], EDA_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {EDA_labeled['Vorgang'][index]}"))

    if add_tags:
        tag_counter = 1
        tags = TAGS_processing(tags_path)
        for index in tags.index:
            figEDA.add_trace(go.Scatter(x = [ tags['tag'][index], tags['tag'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'green'), name = f"Tag Number {tag_counter}"))
            tag_counter += 1

    #figEDA.show()
    return figEDA

def preprocess_EDA(data, order: int = 1,
                   lowpass_cutoff_frequency: float = 1 / (4 / 2),
                   highpass_cutoff_frequency: float = 0.05 / (4 / 2)):

    data = data.copy()

    b, a = signal.butter(order, lowpass_cutoff_frequency, 'low', analog = False)
    c, d = signal.butter(order, highpass_cutoff_frequency, 'high', analog = False)

    z = signal.lfilter(b, a, data.EDA)
    filteredEDA = signal.lfilter(c, d, z)

    data['EDA_filtered'] = filteredEDA

    return data

############### Skin Temperature (ST / TEMP) - 4 Hz Sampling Frequency ###############

def ST_processing(path):
    ST = pd.read_csv(path)
    start_time_col = ST.columns[0]
    start_time = pd.to_datetime(start_time_col, unit="s") + pd.to_timedelta(2, unit = "h")
    ST = ST[1:].reset_index()
    length_ST = math.ceil(len(ST) / 4)
    end_time = start_time + pd.to_timedelta(length_ST, unit = 's') + pd.to_timedelta(2, unit = "h")
    fourHz_ts = pd.date_range(start=start_time, end = end_time, freq="250ms")
    length_difference = len(fourHz_ts) - len(ST)
    ST['datetime'] = fourHz_ts[:-length_difference]
    ST = ST.rename(columns = {start_time_col: "ST"})
    ST["date"] = ST.datetime.dt.date
    ST["time"] = ST.datetime.dt.time
    ST = ST[["datetime", "date", "time", "ST"]]

    return ST

def plot_ST(ST_labeled, raw = True, add_tags: bool = False, tags_path: str = None):

    if raw:
        dmin = ST_labeled['ST'].min()
        dmax = ST_labeled['ST'].max()

        figST = go.Figure(data = go.Scatter(x = ST_labeled['datetime'], y = ST_labeled["ST"], line = dict(color = "red"), name = "Raw Skin Temperature (ST) in ° C"))

        figST.update_xaxes(title_text='Time')
        figST.update_yaxes(title_text='Raw ST (° C)')

    else:

        #### Trim first 3 minutes -- filtered ST signal looks odd
        starttime = ST_labeled["datetime"].min()
        endtime = ST_labeled["datetime"].max()

        ST_labeled.set_index("datetime", inplace=True)

        trimtime = pd.to_timedelta(3, unit="m")
        new_starttime = starttime + trimtime
        ST_labeled = ST_labeled[new_starttime:endtime]

        ST_labeled.reset_index(inplace = True)

        #### plot with trimmed signal
        dmin = ST_labeled['ST_filtered'].min()
        dmax = ST_labeled['ST_filtered'].max()


        figST = go.Figure(data = go.Scatter(x = ST_labeled['datetime'], y = ST_labeled["ST_filtered"], line = dict(color = "red"), name = "Filtered Skin Temperature (ST) in ° C"))

        figST.update_xaxes(title_text='Time')
        figST.update_yaxes(title_text='Filtered ST (° C)')


    labels = ST_labeled[~ST_labeled["Vorgang"].isna()]

    for index in labels.index:
        figST.add_trace(go.Scatter(x = [ST_labeled['datetime'][index], ST_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {ST_labeled['Vorgang'][index]}"))

    if add_tags:
        tag_counter = 1
        tags = TAGS_processing(tags_path)
        for index in tags.index:
            figST.add_trace(go.Scatter(x = [ tags['tag'][index], tags['tag'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'green'), name = f"Tag Number {tag_counter}"))
            tag_counter += 1

    #figST.show()
    return figST

def preprocess_ST(data, order: int = 2,
                   lowpass_cutoff_frequency: float = 0.1 / (4 / 2),  # 0.07 was before
                   highpass_cutoff_frequency: float = 0.01 / (4 / 2)): # 0.005 was before

    data = data.copy()

    b, a = signal.butter(order, lowpass_cutoff_frequency, 'low', analog = False)
    c, d = signal.butter(order, highpass_cutoff_frequency, 'high', analog = False)

    z = signal.lfilter(b, a, data.ST)
    filteredST = signal.lfilter(c, d, z)

    data['ST_filtered'] = filteredST

    return data

############### Blood Volume Pressure (BVP) - 64 Hz Sampling Frequency ###############

def BVP_processing(path):
    BVP = pd.read_csv(path)
    start_time_col = BVP.columns[0]
    start_time = pd.to_datetime(start_time_col, unit="s") + pd.to_timedelta(2, unit = "h")
    BVP = BVP[1:].reset_index()
    length_BVP = math.ceil(len(BVP) / 64)
    end_time = start_time + pd.to_timedelta(length_BVP, unit = 's') + pd.to_timedelta(2, unit = "h")
    sixtyfourHz_ts = pd.date_range(start=start_time, end = end_time, freq="15.625ms")
    length_difference = len(sixtyfourHz_ts) - len(BVP)
    BVP['datetime'] = sixtyfourHz_ts[:-length_difference]
    BVP = BVP.rename(columns = {start_time_col: "BVP"})
    BVP["date"] = BVP.datetime.dt.date
    BVP["time"] = BVP.datetime.dt.time
    BVP = BVP[["datetime", "date", "time", "BVP"]]

    return BVP

def plot_BVP(BVP_labeled, raw = True, add_tags: bool = False, tags_path: str = None):

    if raw:
        dmin = BVP_labeled['BVP'].min()
        dmax = BVP_labeled['BVP'].max()

        figBVP = go.Figure(data = go.Scatter(x = BVP_labeled['datetime'], y = BVP_labeled["BVP"], line = dict(color = "purple"), name = "Raw Blood Volume Pressure (BVP)"))

        figBVP.update_xaxes(title_text='Time')
        figBVP.update_yaxes(title_text='Raw BVP')

    else:
        dmin = BVP_labeled['BVP_filtered'].min()
        dmax = BVP_labeled['BVP_filtered'].max()

        figBVP = go.Figure(data = go.Scatter(x = BVP_labeled['datetime'], y = BVP_labeled["BVP_filtered"], line = dict(color = "purple"), name = "Filtered Blood Volume Pressure (BVP)"))

        figBVP.update_xaxes(title_text='Time')
        figBVP.update_yaxes(title_text='Filtered BVP')

    labels = BVP_labeled[~BVP_labeled["Vorgang"].isna()]

    for index in labels.index:
        figBVP.add_trace(go.Scatter(x = [BVP_labeled['datetime'][index], BVP_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {BVP_labeled['Vorgang'][index]}"))

    if add_tags:
        tag_counter = 1
        tags = TAGS_processing(tags_path)
        for index in tags.index:
            figBVP.add_trace(go.Scatter(x = [ tags['tag'][index], tags['tag'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'green'), name = f"Tag Number {tag_counter}"))
            tag_counter += 1

    #figBVP.show()
    return figBVP
def preprocess_BVP(data, low_order: int = 4, high_order: int = 1,
                   lowpass_cutoff_frequency: float =  0.72 / (4 / 2),   # 0.72 should be 7.2Hz lowpass filter
                   highpass_cutoff_frequency: float = 0.2 / (4 / 2)):   # 0.2Hz for highpass filter
    # filters chosen according to paper: "Towards maximizing the sensing accuracy of an cuffless, optical blood pressure sensor
    # using a highßorder front-end filter" by Kao et al. (2018)

    data = data.copy()

    b, a = signal.butter(low_order, lowpass_cutoff_frequency, 'low', analog = False)
    c, d = signal.butter(high_order, highpass_cutoff_frequency, 'high', analog = False)

    z = signal.lfilter(b, a, data.BVP)
    filteredBVP = signal.lfilter(c, d, z)

    data['BVP_filtered'] = filteredBVP

    return data


############### Accelerometer - 3-axes acceleration signal (ACC) - 32 Hz Sampling Frequency ###############

def ACC_processing(path):
    ACC = pd.read_csv(path)
    start_time_col = ACC.columns[0]
    start_time = pd.to_datetime(start_time_col, unit="s") + pd.to_timedelta(2, unit = "h")
    ACC = ACC[1:].reset_index()
    length_ACC = math.ceil(len(ACC) / 32)
    end_time = start_time + pd.to_timedelta(length_ACC, unit = 's') + pd.to_timedelta(2, unit = "h")
    thirtytwoHz_ts = pd.date_range(start=start_time, end = end_time, freq="31.25ms")
    length_difference = len(thirtytwoHz_ts) - len(ACC)
    ACC['datetime'] = thirtytwoHz_ts[:-length_difference]
    ACC = ACC.rename(columns = {ACC.columns[1]: "X-axis", ACC.columns[2]: "Y-axis", ACC.columns[3]: "Z-axis"})
    ACC["date"] = ACC.datetime.dt.date
    ACC["time"] = ACC.datetime.dt.time
    ACC = ACC[["datetime", "date", "time", "X-axis", "Y-axis", "Z-axis"]]

    return ACC

def plot_ACC(ACC_labeled, add_tags: bool = False, tags_path: str = None):

    figACC = go.Figure(data = go.Scatter(x = ACC_labeled["datetime"], y = ACC_labeled["X-axis"], line=dict(color="red"),
                                      name = 'X-Axis Acceleration in g')) # blue
    figACC.add_trace(go.Scatter(x = ACC_labeled['datetime'], y = ACC_labeled['Y-axis'], line = dict(color = 'green'),
                             name = 'X-Axis Acceleration in g'))
    figACC.add_trace(go.Scatter(x = ACC_labeled['datetime'], y = ACC_labeled['Z-axis'], line = dict(color = 'blue'),
                             name = 'Z-Axis Acceleration in g'))

    figACC.update_xaxes(title_text = "Time")
    figACC.update_yaxes(title_text = "ACC (g)")

    dminX = ACC_labeled['X-axis'].min()
    dmaxX = ACC_labeled['X-axis'].max()
    dminY = ACC_labeled['Y-axis'].min()
    dmaxY = ACC_labeled['Y-axis'].max()
    dminZ = ACC_labeled['Z-axis'].min()
    dmaxZ = ACC_labeled['Z-axis'].max()

    dmin = min([dminX, dminY, dminZ])
    dmax = max([dmaxX, dmaxY, dmaxZ])

    labels = ACC_labeled[~ACC_labeled["Vorgang"].isna()]

    for index in labels.index:
        figACC.add_trace(go.Scatter(x = [ACC_labeled['datetime'][index], ACC_labeled['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {ACC_labeled['Vorgang'][index]}"))

    if add_tags:
        tag_counter = 1
        tags = TAGS_processing(tags_path)
        for index in tags.index:
            figACC.add_trace(go.Scatter(x = [ tags['tag'][index], tags['tag'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'green'), name = f"Tag Number {tag_counter}"))
            tag_counter += 1

    #figACC.show()
    return figACC




############### Tags based on manual clicks ###############

def TAGS_processing(path):
    tags = pd.read_csv(path)

    times = []
    first_timestamp = tags.columns[0]
    first_time = pd.to_datetime(first_timestamp, unit = "s") + pd.to_timedelta(2, unit = "h")
    #print(first_time)
    times.append(first_time)
    for index in tags.index:
        time = pd.to_datetime(tags.loc[index, tags.columns[0]], unit = "s") + pd.to_timedelta(2, unit = "h")
        #print(time)
        times.append(time)

    df = pd.DataFrame({"tag": times})
    df['tag'] = df['tag'].dt.round("1s")

    return df


def downsample_signal(data: pd.DataFrame,
                      frequency: str = "1s", interpolationMethod = "linear", order = 1) -> pd.DataFrame:

    data_1Hz = data.copy()
    if "datetime" in data_1Hz.columns:
        data_1Hz = data_1Hz.set_index("datetime")

    data_1Hz_downsampled = data_1Hz.resample(frequency).mean()
    data_1Hz_interpolated = data_1Hz_downsampled.interpolate(method = interpolationMethod, order = order)
    data_1Hz_ready = data_1Hz_interpolated.reset_index()

    return data_1Hz_ready

def merge_signals_1Hz(HR_df, EDA_df, ST_df):

    data = pd.merge(EDA_df, HR_df, on = "datetime", how = "left")
    data_n = pd.merge(data, ST_df, on="datetime", how="left")
    return data_n




def standardize_signals(data: pd.DataFrame) -> pd.DataFrame:

    EDA_values = data['EDA_filtered'].values
    EDA_values = EDA_values.reshape((len(EDA_values), 1))
    # train the standardization
    scaler = StandardScaler()
    scaler = scaler.fit(EDA_values)
    #print('Mean: %f, StandardDeviation: %f' % (scaler.mean_, sqrt(scaler.var_)))
    EDA_standardized = scaler.transform(EDA_values)

    ST_values = data['ST_filtered'].values
    ST_values = ST_values.reshape((len(ST_values), 1))
    # train the standardization
    scaler = StandardScaler()
    scaler = scaler.fit(ST_values)
    ST_standardized = scaler.transform(ST_values)

    HR_values = data['HR'].values
    HR_values = HR_values.reshape((len(HR_values), 1))
    # train the standardization
    scaler = StandardScaler()
    scaler = scaler.fit(HR_values)
    HR_standardized = scaler.transform(HR_values)

    # inverse transform and print the first 5 rows
    #inversed = scaler.inverse_transform(HR_normalized)

    print(f"Standardized EDA: {len(EDA_standardized)}, ST: {len(ST_standardized)}, HR: {len(HR_standardized)}")

    data['EDA_standardized'] = EDA_standardized
    data['ST_standardized'] = ST_standardized
    data['HR_standardized'] = HR_standardized

    return data

def normalize_signals(data: pd.DataFrame) -> pd.DataFrame:
    EDA_values = data['EDA_filtered'].values
    EDA_values = EDA_values.reshape((len(EDA_values), 1))
    # train the standardization
    scaler = MinMaxScaler()
    scaler = scaler.fit(EDA_values)
    #print('Mean: %f, StandardDeviation: %f' % (scaler.mean_, sqrt(scaler.var_)))
    EDA_normalized = scaler.transform(EDA_values)

    ST_values = data['ST_filtered'].values
    ST_values = ST_values.reshape((len(ST_values), 1))
    # train the standardization
    scaler = MinMaxScaler()
    scaler = scaler.fit(ST_values)
    ST_normalized = scaler.transform(ST_values)

    HR_values = data['HR'].values
    HR_values = HR_values.reshape((len(HR_values), 1))
    # train the standardization
    scaler = MinMaxScaler()
    scaler = scaler.fit(HR_values)
    HR_normalized = scaler.transform(HR_values)

    # inverse transform and print the first 5 rows
    #inversed = scaler.inverse_transform(HR_normalized)

    #print(f"Normalized EDA: {len(EDA_normalized)}, ST: {len(ST_normalized)}, HR: {len(HR_normalized)}")

    data['EDA_normalized'] = EDA_normalized
    data['ST_normalized'] = ST_normalized
    data['HR_normalized'] = HR_normalized

    return data

def plot_standardized_signals(data):
    fig = go.Figure(data = go.Scatter(x = data["datetime"], y = data["EDA_standardized"], line = dict(color = "blue"), name = "Galvanic Skin Response (GSR) in uS"))

    fig.add_trace(go.Scatter(x = data["datetime"], y = data["ST_standardized"], line = dict(color = "orange"), name = "Skin Temperature (ST) in Celsius" ))

    fig.add_trace(go.Scatter(x = data["datetime"], y = data["HR_standardized"], line = dict(color = "red"), name = "Heart Rate (HR) in BPM" ))

    fig.update_xaxes(title_text = "Time")
    fig.update_yaxes(title_text = "Value")

    fig.show()

def plot_normalized_signals(data):
    fig = go.Figure(data = go.Scatter(x = data["datetime"], y = data["EDA_normalized"], line = dict(color = "blue"), name = "Galvanic Skin Response (GSR) in uS"))

    fig.add_trace(go.Scatter(x = data["datetime"], y = data["ST_normalized"], line = dict(color = "orange"), name = "Skin Temperature (ST) in Celsius" ))

    fig.add_trace(go.Scatter(x = data["datetime"], y = data["HR_normalized"], line = dict(color = "red"), name = "Heart Rate (HR) in BPM" ))

    fig.update_xaxes(title_text = "Time")
    fig.update_yaxes(title_text = "Value")

    fig.show()

############### Plot MOS ###############


def plot_EDA_ST_and_MOS(data, add_MOS = True, add_tags = False, tags_path = None):

    dmin = data['EDA_filtered'].min()
    dmax = data['EDA_filtered'].max()

    fig = go.Figure(data = go.Scatter(x = data['datetime'], y = data['EDA_filtered'], line = dict(color = "blue"), name = "Electrodermal Activity (EDA) in uS"))

    fig.add_trace(go.Scatter(x = data["datetime"], y = data["ST_filtered"], line = dict(color = "orange"), name = "Skin Temperature (ST) in Celsius"))

    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='Value', range = [dmin, dmax])

    labels = data[~data["Vorgang"].isna()]

    for index in labels.index:
        fig.add_trace(go.Scatter(x = [data['datetime'][index], data['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {data['Vorgang'][index]}"))

    if add_MOS:
        MOS_counter = 1
        for index in data.index:
            if data["MOS_score"][index] >= 75:
                fig.add_trace(go.Scatter(x = [data["datetime"][index], data["datetime"][index]], y = [dmin, dmax], mode = "lines",
                                         line = dict(color = "yellow"), name = f"Stress Detected - stress # {MOS_counter}"))
                MOS_counter += 1


    if add_tags:
        tag_counter = 1
        tags = TAGS_processing(tags_path)
        for index in tags.index:
            fig.add_trace(go.Scatter(x = [ tags['tag'][index], tags['tag'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'green'), name = f"Tag Number {tag_counter}"))
            tag_counter += 1

    fig.show()


def plot_HR_and_MOS(data, add_MOS = True, add_tags = False, tags_path = None):

    dmin = data['HR'].min()
    dmax = data['HR'].max()

    fig = go.Figure(data = go.Scatter(x = data['datetime'], y = data["HR"], line = dict(color = "red"), name = "Heart Rate (HR) in BPM"))

    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='Value')

    labels = data[~data["Vorgang"].isna()]

    for index in labels.index:
        fig.add_trace(go.Scatter(x = [data['datetime'][index], data['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {data['Vorgang'][index]}"))

    if add_MOS:
        MOS_counter = 1
        for index in data.index:
            if data["MOS_score"][index] >= 75:
                fig.add_trace(go.Scatter(x = [data["datetime"][index], data["datetime"][index]], y = [dmin, dmax], mode = "lines",
                                         line = dict(color = "yellow"), name = f"Stress Detected - stress # {MOS_counter}"))
                MOS_counter += 1


    if add_tags:
        tag_counter = 1
        tags = TAGS_processing(tags_path)
        for index in tags.index:
            fig.add_trace(go.Scatter(x = [ tags['tag'][index], tags['tag'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'green'), name = f"Tag Number {tag_counter}"))
            tag_counter += 1

    fig.show()


def plot_IBI_and_MOS(data, add_MOS = True, add_tags = False, tags_path = None):

    dmin = data['IBI'].min()
    dmax = data['IBI'].max()

    fig = go.Figure(data = go.Scatter(x = data['datetime'], y = data["IBI"], line = dict(color = "green"), name = "Interbeat Interval (s)"))

    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='Value')

    labels = data[~data["Vorgang"].isna()]

    for index in labels.index:
        fig.add_trace(go.Scatter(x = [data['datetime'][index], data['datetime'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'black'), name = f"Stress section {data['Vorgang'][index]}"))

    if add_MOS:
        MOS_counter = 1
        for index in data.index:
            if data["MOS_score"][index] >= 75:
                fig.add_trace(go.Scatter(x = [data["datetime"][index], data["datetime"][index]], y = [dmin, dmax], mode = "lines",
                                         line = dict(color = "yellow"), name = f"Stress Detected - stress # {MOS_counter}"))
                MOS_counter += 1


    if add_tags:
        tag_counter = 1
        tags = TAGS_processing(tags_path)
        for index in tags.index:
            fig.add_trace(go.Scatter(x = [ tags['tag'][index], tags['tag'][index] ], y = [dmin, dmax], mode = "lines", line = dict(color = 'green'), name = f"Tag Number {tag_counter}"))
            tag_counter += 1

    fig.show()
