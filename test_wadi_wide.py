import os
os.chdir('D:\\Users\\postvi\\Documents\\github\\wadi')
print(os.getcwd())

import wadi as wd

header_map = wd.Mapper(map={'Phosphate': 'PO4', 'Nitraat': 'NO3', 'Sulphate': 'SO4', 'ATPinhibition': 'TEST'},
                       replace_strings={'wrong_feature': 'it worked!'},
                       remove_strings=['Unnamed'],
                       )

unit_map = wd.Mapper(map={'mg/l': 'mg/L'},
                     match_method=['regex'],
                     replace_strings={'μ': 'u', '-': ' '},
                     remove_strings=['Unnamed'],
                    )

wi = wd.Importer(format='wide',
                  header_map=header_map,
                  unit_map=unit_map)

rows2skip = list(range(9)) + [22, 23] + list(range(25, 35))
df0_kwargs = {'skiprows': rows2skip, 'usecols': "C:E"}
rows2skip = list(range(3)) + list(range(4, 10)) + [22, 23] + list(range(25, 35))
df1_kwargs = {'skiprows': rows2skip, 'usecols': "F:AF", 'units_row': 4}
rows2skip = list(range(8)) + [9, 22, 23] + list(range(25, 35))
df2_kwargs = {'skiprows': rows2skip, 'usecols': "AG"}
wi.read_data(file_path='examples\\testfile1_io.xlsx',
             panes=[df0_kwargs, df1_kwargs, df2_kwargs])
wi.map_data()

#print(wi.df.head(100))
#print(wi.units)

#wi.map_headers()

# wi.read_data(file_path='examples\\KIWK KOW Grubbenvorst  WP PP ruw rein 20210608.xlsx',
#              format='stacked',
#              column_map={'Feature': 'Analyse', 'Value': 'Gerapporteerde waarde', 'Unit': 'Eenheid omschrijving'})