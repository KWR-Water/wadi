import os
os.chdir('D:\\Users\\postvi\\Documents\\github\\wadi')

import wadi as wd

wdo = wd.DataObject(log_fname='wadi_tutorial.log')

wdo.file_reader('docs/tutorial_data.xlsx',
    format='stacked',
    c_dict={'SampleId': 'Sample number',
            'Features': 'Parameter description',
            'Units': 'Unit description',
            'Values': 'Reported value',
    },
)

name_mapper = {'Chloride': 'Cl',
    'Calcium': 'Ca',
    'Sulphate': 'SO4',
}
# wdo.name_map(m_dict=name_mapper,
#     match_method=['exact', 'fuzzy'],
#     remove_strings=['(ICP-AES)'], 
# )
#wdo.map_units()

# wdo.harmonizer(convert_units=True,
#     target_units='mmol/l',
# )

df = wdo.get_frame()

print(df.head())
