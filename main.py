from data_preparation import data_preparation
from kz_calculate import sort, calculate_kz_coef
from writer_files import write_to_csv

station_list_name = 'StsList_myl.xlsx'
table_const_name = 'Table_const_S_V.xlsx'

if __name__ == "__main__":
    data = data_preparation(station_list_name, 'data.csv',
                             '!result.csv', 'mid')
    order_data = sort(data)

    dates = [('05.2024', '07.2024')] # обязательный формат str(month.year)
    kz_coef_list = calculate_kz_coef(order_data, table_const_name, dates)

    write_to_csv(kz_coef_list, table_const_name, dates)
