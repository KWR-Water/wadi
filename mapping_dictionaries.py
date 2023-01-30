
import wadi as wd

# wdo = wd.DataObject(log_fname='wadi_tutorial.log')

# wdo.file_reader('docs/mixed_data.xlsx',
#     format='stacked',
#     c_dict={'SampleId': 'SampleID',
#             'Features': 'Component',
#             'Units': 'Units',
#             'Values': 'Reported_value',
#     },
# )
# df = wdo.get_imported_dataframe()

# name_mapper = wd.MapperDict.default_dict('SIKB', 'ValidCas')
# wdo.name_map(m_dict=name_mapper,
#     match_method=['exact', 'fuzzy'],
# )

# df = wdo.get_converted_dataframe()
# print(df.head())
wdo = wd.DataObject(log_fname='wadi_mapping_t.log')

wdo.file_reader('docs/mixed_data.xlsx',
    format='stacked',
    c_dict={'SampleId': 'SampleID',
            'Features': 'Component',
            'Units': 'Units',
            'Values': 'Reported_value',
    },
)
names = wdo.get_imported_names()
name_mapper = wd.MapperDict.translation_dict(names)
wdo.name_map(m_dict=name_mapper,
    match_method=['exact', 'fuzzy'],
)
wdo.harmonizer(target_units='mmol/l', convert_units=True)
df = wdo.get_converted_dataframe()
print(df.head())
# m_dict = wd.MapperDict.default_dict('OtherEnglishAlias', 'ValidCid')
# m_dict = {k: v for i, (k, v) in enumerate(m_dict.items()) if i < 5}
# for i, (key, value) in enumerate(m_dict.items()):
#     print(key, value)

# t_dict = wd.MapperDict(m_dict)#
# t_dict.translate_keys()
# print(list(t_dict.keys()))

# p_dict = wd.MapperDict.pubchem_cas_dict(list(t_dict.keys()))
# print(p_dict)

features = [
    'perfluoroctaanzuur (PFOA)',
    'perfluoroctaansulfonaat (PFOS)',
    'aspartaam',
    'saccharine',
    'ijzer',
    'waterstofcarbonaat',
    'aminomethylfosfonzuur',
]

p_dict = wd.MapperDict.translation_dict(features)
print(p_dict)






