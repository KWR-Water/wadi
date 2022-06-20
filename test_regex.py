import pandas as pd
import re

tst = ['Central Park\u202c', 'Top of the Rock', 'Statue of Liberty\u202c', 'Brooklyn Bridge']
print(tst)
print([s.encode('ascii', 'ignore') for s in tst])
print([s.encode('ascii', 'ignore').decode('ascii') for s in tst])

s = "Chemi(cal) compound"
print(re.sub('\(.*\)', '', s))
# df = pd.DataFrame({'Feature': range(0, 10), 'Value': range(20, 30), 'V.1alue': range(50, 60), 'Value.1': range(50, 60)})

# print(df.columns.str.findall('.\d+$'))

# for c in df.columns:
#     print(re.search('.\d+$', c).span)