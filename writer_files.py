import datetime
from collections import defaultdict

import pandas as pd

def write_to_csv(data, table_const_name, dates):
    early_date, lates_date = map(lambda d: datetime.datetime.strptime(d, "%m.%Y"), dates[:2])
    file_table_stations = pd.read_excel(table_const_name)
    file_table_stations = file_table_stations.set_index('Horizon')
    data_from_write = defaultdict(lambda : ())
    list_regions = []
    list_dataframes = []
    for region in data.mean_result_data[early_date.year][early_date.month]:
        data_from_write['T1'] = data.mean_result_data[early_date.year][early_date.month][region]
        data_from_write['T2'] = data.mean_result_data[lates_date.year][lates_date.month][region]
        data_from_write['Tср'] = data.delta_t[region]
        data_from_write['V'] = file_table_stations[f'V, {region}']
        data_from_write['S'] = file_table_stations[f'S, {region}']
        data_from_write['Q'] = data.q_count_termal[region]
        data_from_write['Qsum'] = data.q_sum_down[region]
        data_from_write['Q/S'] = data.q_per_s[region]
        data_from_write['T1_gradients'] = data.t_gradients[early_date.year][early_date.month][region]
        data_from_write['T2_gradients'] = data.t_gradients[lates_date.year][lates_date.month][region]
        data_from_write['T_gradients_ср'] = data.t_gradients[lates_date.year][lates_date.month][region]
        data_from_write['Kz'] = data.k_z[region]
        dataframe = pd.DataFrame(data_from_write)
        list_regions.append(region)
        list_dataframes.append(dataframe)
    with pd.ExcelWriter(f'result\\{early_date.year}_{early_date.month}-{lates_date.year}_{lates_date.month}.xlsx', engine='openpyxl') as writer:
        for region, dataframe in zip(list_regions, list_dataframes):
            dataframe.to_excel(writer, sheet_name = region, index = True)