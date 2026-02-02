import csv
import datetime

from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

import pandas as pd
from logger import logger

from dataclasses import dataclass, field

@dataclass
class Station:
    name: str
    region: str
    mid: str
    latitude: float
    longitude: float

@dataclass
class Measurement:
    path: str = 'unknown'
    station: Station = 'unknown'
    latitude_mes: float = 0
    longitude_mes: float = 0
    date: datetime.datetime = 'unknown'
    depths: list[float] = field(default_factory=list)
    mean_depths: list[float] = field(default_factory=list)
    temperatures: list[float] = field(default_factory=list)
    mean_temperatures: list[float] = field(default_factory=list)
    weighted_mean_temperatures: list[float] = field(default_factory=list) #mean_depth: mean_temperatures средневзвешенная
    mean_data: dict[float] = field(default_factory=list) # mean_depth: mean_temperatures


class StationSelector:
    def __init__(self, stations: list[Station]) -> None:
        self._stations: list[Station] = stations
        self._station_names: list[tuple[str, int]] = []
        for i, station in enumerate(stations):
            self._station_names.append((station.name.lower(), i))
        self._station_names.sort(key=lambda e: len(e), reverse=True)

        self._cache: dict[str, Station] = {}

    def __call__(self, path: str, 
                 latitude_mes: float | None = None,
                 longitude_mes: float | None = None,
                 distance_max: float = 1,
        ) -> Station | None:
        file_name = Path(path).name.lower()

        station = self._cache.get(file_name, None)
        if station is not None:
            return station

        for station_name, index in self._station_names:
            if file_name.startswith(station_name):
                station = self._stations[index]
                self._cache[file_name] = station
                return station

        if latitude_mes and longitude_mes:
            for station in self._stations:
                distance = calculate_distance_by_coordinate(station.latitude,station.longitude,
                                                            latitude_mes, longitude_mes)
                if distance < distance_max:
                    self._cache[file_name] = station
                    return station

        return None

def calculate_distance_by_coordinate(latitude, longitude, latitude_mes, longitude_mes):
    R = 6371.0

    lat1, lon1 = radians(latitude), radians(longitude)
    lat2, lon2 = radians(latitude_mes), radians(longitude_mes)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    result = R * c

    return result

def is_valid_date_format(date_string):
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%d.%m.%Y %H:%M:%S',
        '%d.%m.%Y %H:%M'
         ]

    for fmt in formats:
        try:
            date_obj = datetime.datetime.strptime(date_string, fmt)
            return date_obj
        except ValueError:
            continue

def data_preparation(path_to_file_table_stations, path_to_file_data, path_to_file_info, mid=None):

    file_table_stations = pd.read_excel(path_to_file_table_stations, sheet_name="Лист1")
    #file_data = pd.read_csv(path_to_file_data, sep=';', header=None)
    file_info = pd.read_csv(path_to_file_info, sep=';')

    stations: list[Station] = []
    measurements: dict[str, Measurement] = {}

    for item in file_table_stations.iterrows():
        name = item[1]['Name']
        region = item[1]['Region']
        latitude = item[1]['Lat']
        longitude = item[1]['Lon']
        note = item[1]['Note']

        station = Station(name=name, region=region, mid=note, latitude=latitude, longitude=longitude)
        if mid is None:
            stations.append(station)
        else:
            if mid == note:
                stations.append(station)

    selector = StationSelector(stations)

    for item in file_info.iterrows():
        path = item[1]['Path']

        row_date = item[1]['System_Upload_Date']

        date = is_valid_date_format(row_date)

        latitude_mes = item[1]['Latitude']
        longitude_mes = item[1]['Longitude']
        station = selector(path , latitude_mes, longitude_mes)
        if station is None:
            logger.info("Нет станции для времени: %s", path)
            continue
        measurement = Measurement(path=path, station=station, date=date,
                                 latitude_mes=latitude_mes, longitude_mes=longitude_mes)
        measurements[path] = measurement

    with open(path_to_file_data, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file, delimiter='\t')
        for number, row in enumerate(csv_reader):
            path = row.pop(0)
            station = selector(path)
            if station is None:
                logger.info("Нет станции для измерений: %s", path)
                pass
            else:
                measurement = measurements.get(path)
                if measurement is None:
                    logger.info("Нет времени для измерения: %s", path)
                    pass
                else:
                    if len(row) >= 600:
                        if number % 2 == 0:
                            measurement.depths = [float(value) for value in row]
                        else:
                            measurement.temperatures = [float(value) for value in row]

    return measurements
