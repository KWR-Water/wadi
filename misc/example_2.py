import os
os.chdir('D:\\Users\\postvi\\Documents\\github\\wadi')

import wadi as wd

wi = wd.DataObject(format='wide',
                )

rows2skip = list(range(9)) + [22, 23] + list(range(25, 35))
df0_kwargs = {'skiprows': rows2skip, 'usecols': "C:E", 'datatype': 'sampleinfo'}

rows2skip = list(range(3)) + list(range(4, 10)) + [22, 23]
df1_kwargs = {'skiprows': rows2skip, 'usecols': "F:AF", 'units_row': 4, 'datatype': 'feature', 'na_values': [999]}

rows2skip = list(range(8)) + [9, 22, 23]
df2_kwargs = {'skiprows': rows2skip, 'usecols': "AG", 'datatype': 'sampleinfo'}

wi.read_data(file_path='example_2.xlsx',
            panes=[df0_kwargs, df1_kwargs, df2_kwargs])

print(wi.df.head())

feature_dict = wd.MapperDict({'Phosphate': 'PO4', 
                                'Nitrate': 'NO3', 
                                'Nitrite': 'NO2',
                                'Ammonium': 'NH4',
                                'Silica': 'SiO2',
                                'Sulphate': 'SO4', 
                                'Sodium': 'Na',
                                'Calcium': 'Ca',
                                'Arsenic': 'As',
                                })

wi.map_names(m_dict=feature_dict,
            match_method=['exact', 'fuzzy'],
            )

wi.map_units(match_method=['regex'],
                replace_strings={'μ': 'u', '-': ' ', '%': 'percent'},
            )

df = wi.harmonize(merge_columns=[['Phosphate', 'Phosphate.1'], 
                                    ['Nitraat', 'Nitrate'],
                                    ['Nitrite', 'Nitrite.1'],
                                    ['Ammonium', 'Ammonium.1'],
                                    ['Silica', 'Silica.1'],
                                    ['Sulphate', 'Sulphate.1'],
                                    ['Calcium', 'Calcium.1'],
                                    ['Arsenic', 'Arsenic.1'],
                                ], 
                    drop_columns=['Unnamed: 18'],
                    target_units = 'mmol/l',
                    override_units = {'Arsenic': 'umol/l'},
                    )

print(df.head())
print(df['As'].head())
