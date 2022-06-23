import os
os.chdir('D:\\Users\\postvi\\Documents\\github\\wadi')
print(os.getcwd())

import wadi as wd

header_map = wd.Mapper(map={'Value': 'Concentration', 'Unit': 'unit'})
# wi = wd.Importer(format='stacked',
#                  header_map=header_map)

#wi.read_data(format='wide', 
#             file_path='examples\\example1.xlsx',
#             sheet_name='sample_data')
#print(wi.df.head())


# wi.read_data(format='stacked', 
#              header=None,
#              file_path='examples\\example2.xlsx',
#              sheet_name='wide')
# tst = wi._get_slice([[3, slice(2, 5, 1)], [2, slice(5, 10)]])
#print(tst)


#header_map = DEFAULT_COLUMN_MAP_S
#header_map['SampleId'] = 'sample'

# wi.read_data(file_path='examples\\example2.xlsx',
#              sheet_name='stacked')
#wi.map_headers()
#for key, val in wi.series_dict.items():
#    print(key, val)
# wi.read_data(file_path='examples\\example2.xlsx',
#              format='stacked',
#              sheet_name='stacked',
#              units_row=1)

header_map = wd.Mapper(map={'Value': 'Concentration', 'Unit': 'unit'})
# wi = wd.Importer(format='wide', 
#                  header_map=header_map)
# df0_kwargs = {'sheet_name': 'wide', 'skiprows': 3, 'usecols': "C,D,E", 'datatype': 'header'}
# df1_kwargs = {'sheet_name': 'wide', 'skiprows': [0, 1, 3], 'usecols': "F:J", 'units_row': 3}
# wi.read_data(file_path='examples\\example2.xlsx',
#              format='wide',
#              panes=[df0_kwargs, df1_kwargs])
#wi.map_headers()
#for key, val in wi.series_dict.items():
#    print(key, val)

# print(wi.df.head(10))

# df0_kwargs = {'skiprows': [1], 'usecols': "A:E"}
# df1_kwargs = {'skiprows': [1], 'usecols': "F:O", 'units_row': 1}
# wi.read_data(file_path='examples\\dataset_basic.xlsx',
#              format='wide',
#              panes=[df0_kwargs, df1_kwargs])

# print(wi.df.head(10))
# print(wi.units)

# df0_kwargs = {'skiprows': [1], 'usecols': range(5)}
# df1_kwargs = {'skiprows': [1], 'usecols': range(5, 30), 'units_row': 1}
# wi.read_data(file_path='examples\\dataset_basic.csv',
#              pd_reader='read_csv',
#              format='wide',
#              panes=[df0_kwargs, df1_kwargs])

# print(wi.df.head(10))
# print(wi.units)

# df0_kwargs = {'skiprows': [1], 'usecols': range(5)}
# df1_kwargs = {'skiprows': [1], 'usecols': range(5, 10), 'units_row': 1}
# wi.read_data(file_path='examples\\dataset_invalid_columns.csv',
#              pd_reader='read_csv',
#              format='wide',
#              panes=[df0_kwargs, df1_kwargs])

# print(wi.df.head(10))
# print(wi.units)

# df0_kwargs = {'skiprows': [1], 'usecols': range(5)}
# df1_kwargs = {'skiprows': [1], 'usecols': range(5, 10), 'units_row': 1}
# wi.read_data(file_path='examples\\dataset_with_detection_limits.csv',
#              pd_reader='read_csv',
#              format='wide',
#              panes=[df0_kwargs, df1_kwargs])

# print(wi.df.head())
# print(wi.units)

header_map = wd.Mapper(map={'Phosphate': 'PO4', 'Nitraat': 'NO3', 'Sulphate': 'SO4', 'ATPinhibition': 'TEST'},
                       replace_strings={'wrong_feature': 'it worked!'},
                       remove_strings=['Unnamed'],
                       )

# wi = wd.Importer(format='wide',
#                  header_map=header_map)
# rows2skip = list(range(9)) + [22, 23] + list(range(25, 35))
# df0_kwargs = {'skiprows': rows2skip, 'usecols': "C:E"}
# rows2skip = list(range(3)) + list(range(4, 10)) + [22, 23] + list(range(25, 35))
# df1_kwargs = {'skiprows': rows2skip, 'usecols': "F:AF", 'units_row': 4}
# rows2skip = list(range(8)) + [9, 22, 23] + list(range(25, 35))
# df2_kwargs = {'skiprows': rows2skip, 'usecols': "AG"}
# wi.read_data(file_path='examples\\testfile1_io.xlsx',
#              panes=[df0_kwargs, df1_kwargs, df2_kwargs])

header_map = wd.Mapper(map={'Sulfaat': 'SO4'},
                       replace_strings={'wrong_feature': 'it worked!'},
                       remove_strings=['Unnamed'],
                       )
unit_map = wd.Mapper(map={'mg/l SO4': 'dit_was_sulfaat'},
                     remove_strings=['Unnamed'],
                    )
wi = wd.Importer(format='stacked',
                 header_map=header_map,
                 unit_map=unit_map)
wi.read_data(file_path='examples\\realworlddata_subset.xlsx',
             format='stacked',
             column_map={'Parameter omschrijving': 'Feature', 'Gerapporteerde waarde': 'Value', 'Eenheid omschrijving': 'Unit'})


#print(wi.df.head(100))
#print(wi.units)

#wi.map_headers()

# wi.read_data(file_path='examples\\KIWK KOW Grubbenvorst  WP PP ruw rein 20210608.xlsx',
#              format='stacked',
#              column_map={'Feature': 'Analyse', 'Value': 'Gerapporteerde waarde', 'Unit': 'Eenheid omschrijving'})