import os
os.chdir('D:\\Users\\postvi\\Documents\\github\\wadi')

import wadi as wd

wdo = wd.DataObject(log_fname='wadi_tutorial.log')

wdo.read_data('docs/tutorial_data.xlsx',
    format='stacked',
    c_dict={'SampleId': 'Sample number',
            'Features': 'Parameter description',
            'Units': 'Unit description',
            'Values': 'Reported value',
    },
)

wdo.df.head(9)

name_mapper = {'Chloride': 'Cl',
    'Calcium': 'Ca',
    'Sulpate': 'SO4',
}

wdo.map_names(m_dict=name_mapper,
    remove_strings=['(ICP-AES)'], 
)
wdo.map_units()

df = wdo.harmonize(convert_units=True,
    target_units='mmol/l',
)

print(df.head())
