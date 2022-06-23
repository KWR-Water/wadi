import pandas as pd
import re

# tst = ['Central Park\u202c', 'Top of the Rock', 'Statue of Liberty\u202c', 'Brooklyn Bridge']
# print(tst)
# print([s.encode('ascii', 'ignore') for s in tst])
# print([s.encode('ascii', 'ignore').decode('ascii') for s in tst])

# s = "Chemi(cal) compound"
# print(re.sub('\(.*\)', '', s))
# df = pd.DataFrame({'Feature': range(0, 10), 'Value': range(20, 30), 'V.1alue': range(50, 60), 'Value.1': range(50, 60)})

# print(df.columns.str.findall('.\d+$'))

# for c in df.columns:
#     print(re.search('.\d+$', c).span)

#r"^\s+([a-zA-Z]*)\s*([a-zA-Z0-9]*)?\s*[/.,]\s*([a-zA-Z])\s*([a-zA-Z0-9]*)?\s+$"
# RE = r"^\s*([a-zA-Z]*)[/.,]([a-zA-Z])\s*$"

# res = re.match(RE, 'mg / l')
# for i in range(3):
#     print(res.group(i))

re_dict0 = {'num': ["[a-zA-Z]*", "\s*"],
            'gfw0': ["[a-zA-Z0-9]*", "?\s*"],
            'div': ["[/.,]", "\s*"],
            'den0': ["[0-9]*", "?"],
            'den1': ["[a-zA-Z]*", "\s*"],
            'gfw1': ["[a-zA-Z0-9]*", "?"],
           }
re_dict1 = {'txt': ["[a-zA-Z]*", ""],
           }

def build_default_regex(*args):
    rv = r""
    for i, re_dict in enumerate(args):
        if not isinstance(re_dict, dict):
            raise TypeError(f"argument {re_dict} must be of type dict")
        if (i == 0):
            rv += r"^\s*"
        else:
            rv += r"|^\s*"
        for key, value in re_dict.items():
            rv += rf"(?P<{key}>{value[0]}){value[1]}"
            #rv = r"\s*".join([rv, value[0] + rf"?P<{key}>" + value[1:]])
        rv += r"\s*$"

    return rv

tst = build_default_regex(re_dict0, re_dict1)    

RE0 = r"^\s*(?P<num>[a-zA-Z]*)\s*(?P<gfw0>[a-zA-Z0-9]*)?\s*(?P<div>[/.,])\s*(?P<den0>[0-9]*)?(?P<den1>[a-zA-Z]*)\s*(?P<gfw1>[a-zA-Z0-9]*)?\s*$"
RE1 = r"^\s*(?P<txt>[a-zA-Z]*)\s*$"
RE = '|'.join([RE0, RE1])

print(tst)
print(RE)
print(tst.find(RE))
df = pd.read_excel('../../wadi/examples/unit_map_before_import_20210317.xlsx')
res = []
for i, s in enumerate(df['Unit']):
    m = re.match(RE, s.replace('μ', 'u'))
    if m:
        pass
        #print(m.groupdict().keys())
    if m is not None:
        res.append(m.group(0))
    else:
        res.append('')

df = df['Unit'].to_frame()
df['Match'] = res
df.to_excel('test_regex.xlsx')