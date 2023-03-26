import os
os.chdir('D:\\Users\\postvi\\Documents\\github\\wadi')

import wadi as wd

wdo = wd.DataObject(log_fname='mapping_example.log')

wdo.file_reader('docs/mapping_example.xlsx',
    format='stacked',
    c_dict={'SampleId': 'sample_code',
            'Features': 'parameter',
            'Units': 'dimensie',
            'Values': 'waarde',
    },
)

names = wdo.get_imported_dataframe()["parameter"]

names_dict = wd.mapper.MapperDict.default_dict('REWAB', 'SIKB')
# print(names_dict)
for name in names:
    print(name, "will be mapped to", names_dict.get(name))

# print("Pyrazool will be mapped to", names_dict.get("Pyrazool"))

# wdo.name_map(m_dict=names_dict, match_method=['exact', 'fuzzy'])
# df = wdo.get_converted_dataframe()
# print(df.head())

names_dict = wd.mapper.MapperDict.default_dict('REWAB', 'ValidCid')
wdo.name_map(m_dict=names_dict, match_method=['exact'])
df = wdo.get_converted_dataframe()
# print(df.head())

names_dict = wd.mapper.MapperDict.pubchem_cid_dict(names, src_lang="NL")
# names_dict.translate_keys(
#     src_lang="NL",
#     dst_lang="EN",
# )
print(names_dict)
wdo.name_map(m_dict=names_dict, match_method=['exact', 'fuzzy'])
df = wdo.get_converted_dataframe()
print(df.head())

names_dict = wd.mapper.MapperDict.pubchem_cas_dict(names, src_lang="NL")
# names_dict.translate_keys(
#     src_lang="NL",
#     dst_lang="EN",
# )
print(names_dict)
wdo.name_map(m_dict=names_dict, match_method=['exact', 'fuzzy'])
df = wdo.get_converted_dataframe()
print(df.head())

wdo = wd.DataObject(log_fname='mapping_example.log')

wdo.file_reader('docs/mapping_example.xlsx',
    format='stacked',
    c_dict={'SampleId': 'sample_code',
            'Features': 'parameter',
            'Units': 'dimensie',
            'Values': 'waarde',
    },
)

names = wdo.get_imported_dataframe()["parameter"]

names_dict = wd.mapper.MapperDict.translation_dict(names,
    src_lang="NL",
    dst_lang="EN",
)

print(names_dict)

