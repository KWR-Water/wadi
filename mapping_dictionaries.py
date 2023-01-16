
import wadi as wd

m_dict = wd.MapperDict.default_dict('OtherEnglishAlias', 'ValidCid')
m_dict = {k: v for i, (k, v) in enumerate(m_dict.items()) if i < 5}
for i, (key, value) in enumerate(m_dict.items()):
    print(key, value)

t_dict = wd.MapperDict(m_dict)#
t_dict.translate_keys()
print(list(t_dict.keys()))

p_dict = wd.MapperDict.pubchem_cas_dict(list(t_dict.keys()))
print(p_dict)
