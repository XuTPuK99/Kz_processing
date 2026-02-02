import os
import datetime
import matplotlib.pyplot as plt

from logger import logger
from filter_data import filter_data_by_limit

def savefig_safe(path, *args, **kwargs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, *args, **kwargs)

def visialization_profile(order_data, dates):
    early_date, lates_date = map(lambda d: datetime.datetime.strptime(d, "%m.%Y"), dates[:2])

    year = early_date.year
    begin_month = early_date.month
    end_month = lates_date.month

    year_data = order_data.get(year)
    if not year_data:
        logger.error("%s, not year", year)
        return None

    begin_month_data = year_data.get(begin_month)
    end_month_data = year_data.get(end_month)
    if not begin_month_data or not end_month_data:
        logger.error("%s, %s, %s, not month", year, begin_month, end_month)
        return None

    for region, begin_data in begin_month_data.items():
        end_data = end_month_data.get(region)
        if not end_data:
            logger.error("%s, %s, %s, not end_data", year, begin_month, end_month)
            continue

        begin_end_data = [begin_data, end_data]

        for data in begin_end_data:
            for measurement in data:
                if filter_data_by_limit(measurement) is not None:
                    plt.figure(figsize=(9, 5))

                    station = measurement.station.name
                    region = measurement.station.region
                    date = measurement.date.date()
                    month = measurement.date.month
                    temperatures = measurement.temperatures
                    depths = measurement.depths

                    plt.plot(temperatures, depths, linestyle='-', color='b')

                    plt.title(f"Профиль станции {station}, {region}, {date}")
                    plt.xlabel("Температура (°C)")
                    plt.ylabel("Глубина (м)")

                    plt.gca().invert_yaxis()

                    plt.grid(True)

                    savefig_safe(rf"plots(station)/{year}/{month}/Profile_{station}_{region}_{date}.png",  dpi=300,
                                 bbox_inches='tight', format='png')

                    plt.close()
