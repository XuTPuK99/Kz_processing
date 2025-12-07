import datetime

import pandas as pd
import numpy as np

from collections import defaultdict
from dataclasses import dataclass

@dataclass
class ListKzCoef:
    mean_result_data: {}
    delta_t: {}
    mean_delta_t: {}
    q_count_termal: {}
    q_sum_down: {}
    q_per_s: {}
    t_gradients: {}
    t_gradients_mean: {}
    k_z: {}


def sort(data):
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for path in data:
        if not data[path].depths:
            continue
        if data[path].date is None:
            continue
        year = data[path].date.year
        month = data[path].date.month
        region = data[path].station.region
        result[year][month][region].append(data[path])
    return result

def data_clipping(measurement_data):
    if measurement_data.depths:
        data_depths = pd.DataFrame(measurement_data.depths).loc[:, 0]
        data_temperatures = pd.DataFrame(measurement_data.temperatures).loc[:, 0]

        dive_begin_index = 0
        lift_begin_index = len(measurement_data.depths)

        for number, item in enumerate(data_depths):
            if item > 0:
                dive_begin_index = number
                break

        measurement_data.depths = data_depths.loc[range(dive_begin_index, lift_begin_index)].to_list()
        measurement_data.temperatures = data_temperatures.loc[range(dive_begin_index, lift_begin_index)].to_list()

    return measurement_data

def average_data(order_data, table_const, dates):
    early_date, lates_date = map(lambda d: datetime.datetime.strptime(d, "%m.%Y"), dates[:2])
    delta_date = (lates_date - early_date).days

    mean_result_data_by_depth = average_by_depth(order_data, table_const, early_date, lates_date)
    mean_result_data = average_result_data(mean_result_data_by_depth)

    return early_date, lates_date, delta_date, mean_result_data

def average_by_depth(order_data, table_const, early_date, lates_date):
    for region in order_data[early_date.year][early_date.month]:
        for station in order_data[early_date.year][early_date.month][region]:
            if not station.depths:
                continue
            station = data_clipping(station)
            old_horizon = 0
            id_old_horizon = 0
            for horizon in table_const['Horizon']:
                if horizon == 0:
                    continue
                id_horizon_data = np.argmin(np.abs(np.array(station.depths) - horizon))
                values_before = np.array(station.temperatures)[id_old_horizon:id_horizon_data]
                mean_value = np.mean(values_before)
                if (horizon == 2 and (station.date.month == 6 or station.date.month == 7)
                        and region == 'north' and mean_value < 4):
                    print(station.date, station.mean_data)
                    break
                if horizon == 2 and mean_value < 4 and station.date.month == 11:
                    break
                station.mean_data[old_horizon] = mean_value
                old_horizon = horizon
                id_old_horizon = id_horizon_data

    for region in order_data[lates_date.year][lates_date.month]:
        for station in order_data[lates_date.year][lates_date.month][region]:
            if not station.depths:
                continue
            station = data_clipping(station)
            old_horizon = 0
            id_old_horizon = 0
            for horizon in table_const['Horizon']:
                if horizon == 0:
                    continue
                id_horizon_data = np.argmin(np.abs(np.array(station.depths) - horizon))
                values_before = np.array(station.temperatures)[id_old_horizon:id_horizon_data]
                mean_value = np.mean(values_before)
                if (horizon == 2 and (station.date.month == 6 or station.date.month == 7)
                        and region == 'north' and mean_value < 4):
                    break
                if horizon == 2 and mean_value < 4 and station.date.month == 11:
                    break
                station.mean_data[old_horizon] = mean_value
                old_horizon = horizon
                id_old_horizon = id_horizon_data

    return order_data

def average_result_data(order_data):
    mean_result_data = defaultdict(lambda: defaultdict(lambda: (defaultdict())))

    for year in order_data:
        for month in order_data[year]:
            for region in order_data[year][month]:
                mean_datas = []
                for mesurment in order_data[year][month][region]:
                    if mesurment.mean_data:
                       mean_datas.append(mesurment.mean_data)
                if not mean_datas:
                    continue
                d = pd.DataFrame(mean_datas).T
                d['row.mean'] = d.mean(axis=1)
                mean_result_data[year][month][region] = dict(zip(d.index, d['row.mean']))

    return mean_result_data

def calculate_kz_coef(order_data, path_to_const_table, dates):
    list_data = ListKzCoef
    table_const = pd.read_excel(path_to_const_table)
    early_date, lates_date, delta_date, mean_result_data = average_data(order_data, table_const, dates)

    list_data.mean_result_data = mean_result_data

    delta_t = defaultdict(lambda: {})
    mean_delta_t = defaultdict(lambda: {})

    for year in mean_result_data:
        for month in mean_result_data[year]:
            for region in mean_result_data[year][month]:
                if (region in mean_result_data.get(early_date.year, {}).get(early_date.month, {}) and region in
                    mean_result_data.get(lates_date.year, {}).get(lates_date.month, {})):
                    for layer in mean_result_data[year][month][region]:
                        delta_t[region][layer] = np.nansum([mean_result_data[lates_date.year][lates_date.month][
                        region][layer], -mean_result_data[early_date.year][early_date.month][region][layer]])

    list_data.delta_t = delta_t

    for region in delta_t:
        previos_layer = None
        for layer in delta_t[region]:
            if layer == 0:
                previos_layer = layer
                continue
            if delta_t[region][layer] == 0:
                mean_delta_t[region][previos_layer] = delta_t[region][previos_layer]
            mean_delta_t[region][previos_layer] = (np.nansum([delta_t[region][previos_layer],
                                                              delta_t[region][layer]]) / 2)
            previos_layer = layer

    list_data.mean_delta_t = mean_delta_t

    q_count_termal = defaultdict(lambda: {})
    for region in mean_delta_t:
        for layer in reversed(mean_delta_t[region]):
            if not table_const[table_const['Horizon'] == layer][f'V, {region}'].empty:
                q = mean_delta_t[region][layer] * float(table_const[table_const['Horizon'] == layer][f'V, {region}'])
                q_count_termal[region][layer] = q

    list_data.q_count_termal = q_count_termal

    old_q_count_termal = np.float64()
    q_sum_down = defaultdict(lambda: {})
    for region in q_count_termal:
        for number, layer in enumerate(q_count_termal[region]):
            if number == 0:
                q_sum_down[region][layer] = q_count_termal[region][layer]
                old_q_count_termal = q_count_termal[region][layer]
                continue
            q_sum_down[region][layer] = np.nansum([old_q_count_termal, q_count_termal[region][layer]])
            old_q_count_termal = q_sum_down[region][layer]

    list_data.q_sum_down = q_sum_down

    q_per_s = defaultdict(lambda: {})
    for region in q_sum_down:
        for layer in reversed(q_sum_down[region]):
            if np.isnan(q_sum_down[region][layer]):
                continue
            q_per_s[region][layer] = ((q_sum_down[region][layer] / float(table_const[table_const['Horizon'] ==
                                                                                layer][f'S, {region}'])) * 1000)

    list_data.q_per_s = q_per_s

    t_gradients = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {})))
    for year, months in mean_result_data.items():
        for month, regions in months.items():
            for region, values in regions.items():
                if (region in mean_result_data.get(early_date.year,{}).get(early_date.month, {}) and region in
                        mean_result_data.get(lates_date.year, {}).get(lates_date.month, {})):
                    keys = list(values.keys())
                    for index in range(2, len(values)):
                        t_gradients[year][month][region][keys[index-1]] = (np.nansum([mean_result_data[year][month]
                                                                                      [region][keys[index]],
                                                                                      -mean_result_data[year][month]
                                                                                      [region][keys[index-2]]])
                                                                    /np.nansum([keys[index],-keys[index-2]]))

    list_data.t_gradients = t_gradients

    old_t_gradients = defaultdict(lambda: ())
    t_gradients_mean = defaultdict(lambda: {})
    for year in t_gradients:
        for month in t_gradients[year]:
            for region in t_gradients[year][month]:
                if not old_t_gradients:
                    old_t_gradients = t_gradients[year][month][region]
                    continue
                for layer in t_gradients[year][month][region]:
                    t_gradients_mean[region][layer] = (np.nansum([t_gradients[year][month][region][layer],
                                                                 old_t_gradients[layer]]) / 2)

    list_data.t_gradients_mean = t_gradients_mean

    k_z = defaultdict(lambda: {})
    for region in t_gradients_mean:
        for layer in t_gradients_mean[region]:
            x = q_per_s[region].get(layer, None)
            if x is None:
                continue
            y = t_gradients_mean[region][layer] * 86400 * delta_date
            k_z[region][layer] = abs((-x / y) * 10000)

    list_data.k_z = k_z

    return list_data
