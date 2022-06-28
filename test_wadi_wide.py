import os
os.chdir('D:\\Users\\postvi\\Documents\\github\\wadi')
print(os.getcwd())

import wadi as wd

# header_dict = wd.MapperDict({'Phosphate': 'PO4', 
#                              'Nitraat': 'NO3', 
#                              'Nitrite': 'NO2',
#                              'Ammonium': 'NH4',
#                              'Silica': 'Si',
#                              'Sulphate': 'SO4', 
#                              'Sodium': 'Na',
#                              'Calcium': 'Ca',
#                              'Arsenic': 'As',
#                              })
# header_dict.to_file('header_dict_testfile1_io.json')
header_dict = wd.MapperDict.from_file('header_dict_testfile1_io.json')

#header_dict_en = header_dict.translate()

header_map = wd.Mapper(m_dict=header_dict,
                       match_method=['exact', 'ascii', 'fuzzy'], # pubchem],
                       replace_strings={'wrong_feature': 'it worked!'},
                       remove_strings=['Unnamed'],
                       )

unit_dict = wd.MapperDict({'mg/l': 'mg/L', '%': '1 / 100'})
unit_map = wd.Mapper(m_dict=unit_dict,
                     match_method=['regex'],
                     replace_strings={'μ': 'u', '-': ' '},
                     remove_strings=['Unnamed'],
                    )

wi = wd.Importer(format='wide',
                 header_map=header_map,
                 unit_map=unit_map)

rows2skip = list(range(9)) + [22, 23] + list(range(25, 35))
df0_kwargs = {'skiprows': rows2skip, 'usecols': "C:E", 'datatype': 'header'}
rows2skip = list(range(3)) + list(range(4, 10)) + [22, 23] + list(range(25, 35))
df1_kwargs = {'skiprows': rows2skip, 'usecols': "F:AF", 'units_row': 4, 'datatype': 'feature'}
rows2skip = list(range(8)) + [9, 22, 23] + list(range(25, 35))
df2_kwargs = {'skiprows': rows2skip, 'usecols': "AG", 'datatype': 'header'}

wi.read_data(file_path='examples\\testfile1_io.xlsx',
             panes=[df0_kwargs, df1_kwargs, df2_kwargs])

wi.map_data()

wi.harmonize(drop_columns=['Phosphate.1'])

wi.save_summary()