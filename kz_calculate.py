import datetime

import pandas as pd
import numpy as np

from collections import defaultdict
from dataclasses import dataclass

from data_preparation import Measurement
from writer_files import write_statistic_station, write_to_excel_row_station
from filter_data import filter_data_by_limit, filter_data_by_temperature

@dataclass
class ListKzCoef:
    mean_early_date: str
    mean_lates_date: str
    delta_date: datetime.timedelta()
    mean_result_data_begin: {}
    mean_result_data_end: {}
    delta_t: {}
    mean_delta_t: {}
    q_count_termal: {}
    q_sum_down: {}
    q_per_s: {}
    t_gradients_1: {}
    t_gradients_2: {}
    t_gradients_mean: {}
    k_z: {}

def sort_data(data):
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

def calculate_delta_time(order_data, early_date, lates_date):
    list_early_date = []
    for region in order_data[early_date.year][early_date.month]:
        for measurement in order_data[early_date.year][early_date.month][region]:
            list_early_date.append(measurement.date)
    if not list_early_date:
        return None, None, None
    mean_early_date = pd.to_datetime(list_early_date).mean()

    list_lates_date = []
    for region in order_data[lates_date.year][lates_date.month]:
        for measurement in order_data[lates_date.year][lates_date.month][region]:
            list_lates_date.append(measurement.date)
    if not list_lates_date:
        return None, None, None
    mean_lates_date = pd.to_datetime(list_lates_date).mean()

    delta_date = mean_lates_date - mean_early_date

    mean_early_date = mean_early_date.strftime("%Y-%m-%d")
    mean_lates_date = mean_lates_date.strftime("%Y-%m-%d")

    return delta_date.days, mean_early_date, mean_lates_date

def average_region_measurements(year, month, region_data: list[Measurement], horizons: list[float]) -> dict[float,
list[float]]:
    horizon_intervals = pd.IntervalIndex.from_breaks(horizons, closed='left')
    # average_region_mean_data - словарь, где ключ - горизонт,
    # а значение - список средних значений для каждого измерения по интервалу
    average_region_mean_data = dict()
    list_path=[]
    for measurement in region_data:
        number_bad_data = 0

        pd_data = pd.Series(measurement.temperatures, index=measurement.depths).sort_index()
        if pd_data[pd_data.index > 500].empty:
           continue
        list_path.append(measurement.path)
        # находим среднее для каждого интервала
        for interval in horizon_intervals:
            begin = interval.left
            mask = (pd_data.index >= begin) & (pd_data.index < interval.right)
            segment = pd_data[mask]
            if segment.empty:
                mean_value = None
            else:
                mean_value = calculate_mean_value(segment.index.values, segment.values)

            if begin in [0, 2]:
                status_except = filter_data_by_temperature(mean_value, year, month, measurement.station.region)
                if status_except:
                    number_bad_data += 1
                if number_bad_data == 2:
                    list_path = list_path[:-1]
                    average_region_mean_data[0] = average_region_mean_data[0][:-1]
                    break

            interval_average_data = average_region_mean_data.get(begin, list())
            interval_average_data.append(mean_value)
            average_region_mean_data[begin] = interval_average_data

    return list_path, average_region_mean_data

def calculate_mean_value(depths, temps) -> float:
    numerator = sum(map(lambda x: x[0] * x[1], zip(temps, depths)))
    denominator = sum(depths)
    return numerator / denominator

def max_not_null_values(data: list[float]) -> int:
    for i in range(len(data) - 1, -1, -1):
        if data[i]:
            return i
    return 0

def return_list_path(data):
    result =[]
    for meusurement in data:
        result.append(meusurement.path)
    return result

def calculate_mean_data(data: list[float]) -> float | None:
    # подсчёт не нулевых значений
    non_zero_list = [x for x in data if x]
    if len(non_zero_list) == 0:
        return 0

    return sum(non_zero_list) / len(non_zero_list)

def calculate_mean_delta_t(data: list[float]) -> list[float]:
    result = []
    for i in range(len(data) - 1):
        if data[i] and not data[i+1]:
            value = data[i]
        elif not data[i] and data[i+1]:
            value = 0
        else:
            value = (data[i] + data[i+1])/2
        result.append(value)
    return result

def calculate_Q_sum(data: list[float]) -> list[float]:
    result = []
    q_sum = 0
    for i in range(len(data) - 1, -1, -1):
        q_sum += data[i]
        result.append(q_sum)
    return result

def calculate_gradient_T(data: list[float], horizons: list[int]) -> list[float]:
    result = []
    if len(data) == 0:
        return result
    if len(horizons) < len(data):
        data = data[:len(horizons)]
    result.append(0) # необходимо так как невозможно посчитать первое значения
    for i in range(1, len(data) - 1):
        previous_temp = data[i-1]
        second_temp = data[i+1]

        previous_horizon = horizons[i-1]
        second_horizon = horizons[i+1]

        if previous_temp:
            value = (second_temp-previous_temp)/(second_horizon-previous_horizon)
        else:
            value = 0
        result.append(value)
    return result

def calculate_gradient_T_mean(gradient_1: list[float], gradient_2: list[float]) ->list[float]:
    result = []
    if len(gradient_2) >= len(gradient_1):
        data1 = gradient_1
        data2 = gradient_2
    else:
        data1 = gradient_2
        data2 = gradient_1
    for index, value2 in enumerate(data1):
        if index == len(data2):
            break
        value1 = data2[index]
        result.append((value2 + value1)/2)
    return result

def calculate_Kz(gradients: list[float], Q_per_S: list[float], delta_date: int) -> list[float]:
    result=[]
    for index, gradient in enumerate(gradients):
        if index == len(Q_per_S):
            break
        Q = Q_per_S[index]
        if gradient == 0:
            Kz = 0
        else:
            Kz = abs(-Q/(gradient * 86400 * delta_date)) * 10000
        result.append(Kz)
    return result

def calculate_kz_coef(order_data, table_const, dates, horizons):
    list_data = ListKzCoef(mean_early_date='', mean_lates_date='', delta_date = '',
                           mean_result_data_begin=defaultdict(lambda: defaultdict(float)),
                           mean_result_data_end=defaultdict(lambda: defaultdict(float)), delta_t=defaultdict(lambda: defaultdict(float)), mean_delta_t=defaultdict(lambda: defaultdict(float)),
                           q_count_termal=defaultdict(lambda: defaultdict(float)), q_sum_down= defaultdict(lambda: defaultdict(float)),
                           q_per_s= defaultdict(lambda: defaultdict(float)), t_gradients_1=defaultdict(lambda: defaultdict(float)),
                           t_gradients_2=defaultdict(lambda: defaultdict(float)), t_gradients_mean=defaultdict(lambda: defaultdict(float)), k_z=defaultdict(lambda: defaultdict(float)))

    early_date, lates_date = map(lambda d: datetime.datetime.strptime(d, "%m.%Y"), dates[:2])
    delta_date, mean_early_date, mean_lates_date = calculate_delta_time(order_data, early_date, lates_date)

    list_data.mean_early_date = mean_early_date
    list_data.mean_lates_date = mean_lates_date
    list_data.delta_date = delta_date

    year = early_date.year
    begin_month = early_date.month
    end_month = lates_date.month

    year_data = order_data.get(year)
    if not year_data:
        return None

    begin_month_data = year_data.get(begin_month)
    end_month_data = year_data.get(end_month)
    if not begin_month_data or not end_month_data:
        return  None

    for region, begin_data in begin_month_data.items():
        end_data = end_month_data.get(region)
        if not end_data:
            continue
        if f'V, {region}' not in table_const.columns:
            continue

        begin_data = filter_data_by_limit(begin_data)
        end_data = filter_data_by_limit(end_data)

        if begin_data is None or end_data is None:
            continue

        list_path_begin, mean_begin_dict = average_region_measurements(year, begin_month, begin_data, horizons)
        list_path_end, mean_end_dict = average_region_measurements(year, end_month, end_data, horizons)

        write_statistic_station(year, begin_month, region, list_path_begin, 'begin')
        write_statistic_station(year, end_month, region, list_path_end, 'end')

        write_to_excel_row_station(year, begin_month, region, mean_begin_dict, list_path_begin)
        write_to_excel_row_station(year, end_month, region, mean_end_dict, list_path_end)

        list_delta_t = []
        list_mean_begin = []
        list_mean_end = []

        for horizon in mean_begin_dict:
            mean_data_begin = calculate_mean_data(mean_begin_dict.get(horizon, []))
            mean_data_end = calculate_mean_data(mean_end_dict.get(horizon, []))

            list_mean_begin.append(mean_data_begin)
            list_mean_end.append(mean_data_end)

            list_data.mean_result_data_begin[region][horizon] = mean_data_begin
            list_data.mean_result_data_end[region][horizon] = mean_data_end

            if not mean_data_end or not mean_data_begin:
                delta_t = 0
            else:
                delta_t = mean_data_end - mean_data_begin
            list_delta_t.append(delta_t)

            list_data.delta_t[region][horizon] = delta_t

        min_index_value = min(max_not_null_values(list_mean_begin),max_not_null_values(list_mean_end))
        list_mean_begin = list_mean_begin[:min_index_value + 1]
        list_mean_end = list_mean_end[:min_index_value + 1]

        # mean_delta_t на одну короче чем list_delta_t
        list_mean_delta_t = calculate_mean_delta_t(list_delta_t)
        list_q = []
        for index, value in enumerate(list_mean_delta_t):

            horizon = horizons[index]
            list_data.mean_delta_t[region][horizon] = value

            v_const = table_const[table_const['Horizon'] == horizon][f'V, {region}'].values[0]

            if np.isnan(v_const):
                v_const = 0

            Q = value * v_const
            list_q.append(Q)

            list_data.q_count_termal[region][horizon] = Q

        list_Q_sum = calculate_Q_sum(list_q)
        list_Q_per_S = []
        for index, Qsum in enumerate(reversed(list_Q_sum)):

            horizon = horizons[index]
            list_data.q_sum_down[region][horizon] = Qsum

            s_const = table_const[table_const['Horizon'] == horizon][f'S, {region}'].values[0]

            if np.isnan(s_const):
                Qsum_per_S = 0
            else:
                Qsum_per_S = Qsum / s_const * 1000
            list_Q_per_S.append(Qsum_per_S)

            list_data.q_per_s[region][horizon] = Qsum_per_S

        list_gradient_begin = calculate_gradient_T(list_mean_begin, horizons)
        list_gradient_end = calculate_gradient_T(list_mean_end, horizons)
        for index, value in enumerate(list_gradient_begin):
            horizon = horizons[index]
            list_data.t_gradients_1[region][horizon]  = value
        for index, value in enumerate(list_gradient_end):
            horizon = horizons[index]
            list_data.t_gradients_2[region][horizon] = value


        list_gradient_mean = calculate_gradient_T_mean(list_gradient_begin, list_gradient_end)
        for index, value in enumerate(list_gradient_mean):
            horizon = horizons[index]
            list_data.t_gradients_mean[region][horizon]  = value


        list_Kz = calculate_Kz(list_gradient_mean, list_Q_per_S, delta_date)
        for index, value in enumerate(list_Kz):
            horizon = horizons[index]
            list_data.k_z[region][horizon] = value

    return list_data
