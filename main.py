import time
import pandas as pd
from logger import logger


from data_preparation import data_preparation
from kz_calculate import sort_data, calculate_kz_coef
from visualization_profile import visialization_profile
from writer_files import write_to_excel, write_to_excel_all_kz


def main() -> None:
    start = time.time()
    logger.info("Start program")

    station_list_name = 'StsList_myl.xlsx'
    table_const_name = 'old_Table_const_S_V.xlsx'

    data = data_preparation(station_list_name, '!data.csv', '!result.csv')
                           #'file_from_processing\\data_2025.csv',
                            #'file_from_processing\\result_2025.csv')

    order_data = sort_data(data)

    years = order_data.keys()

    #months = [[7, 9], [9, 11], [7, 11], [11, 12]]  #[5,7] - тестовый набор
    months = [[7, 9]]

    table_const = pd.read_excel(table_const_name,)
    horizons = sorted(table_const['Horizon'].unique())
    for year in years:
        for index in range(len(months)):

            dates = (f'{months[index][0]}.{year}', f'{months[index][1]}.{year}')  # обязательный формат str(month.year)

            #visialization_profile(order_data, dates)

            kz_coef_list = calculate_kz_coef(order_data, table_const, dates, horizons)
            if kz_coef_list is None:
                 continue

            write_to_excel(kz_coef_list, table_const, dates)
            #write_to_excel_all_kz(kz_coef_list, table_const, dates)

    end = time.time() - start

    logger.info("Program running time: %s", end)

if __name__ == "__main__":
    main()
