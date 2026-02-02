from logger import logger
from data_preparation import Measurement


def filter_data_by_limit(data):
    list_result = []
    if isinstance(data, list):
        for measurement in data:
            if measurement.station.region == "MalMor":
                continue
            if not min(measurement.depths) < 10 or not 600 <= max(measurement.depths):
                continue
            if measurement.station.region == "north" and not max(measurement.depths) > 600:
                continue
            if ((measurement.station.region == "middle" or measurement.station.region == "south") and
                    not max(measurement.depths) > 1000):
                continue
            list_result.append(measurement)
        if not list_result:
            return None
        return list_result
    if isinstance(data, Measurement):
        if data.station.region == "MalMor":
            return None
        if not min(data.depths) < 10 or not 600 <= max(data.depths):
            return None
        if data.station.region == "north" and not max(data.depths) > 600:
            return None
        if ((data.station.region == "middle" or data.station.region == "south") and
             not max(data.depths) > 1000):
            return None
        return data

def filter_data_by_temperature(mean_value, year, month, region):
    status = False
    if month in (6, 7, 11) and (mean_value is None or mean_value < 4):
        logger.error("error temperature %s, %s, %s, %s", mean_value, region, year, month)
        status = True
    return status
