import os
os.chdir('D:\\Users\\postvi\\Documents\\github\\wadi')
print(os.getcwd())

import wadi as wd
#from wadi.io import DEFAULT_COLUMN_MAP_S

wi = wd.Importer()

wi.read_data(file_path='examples\\KIWK KOW Grubbenvorst  WP PP ruw rein 20210608.xlsx',
             format='stacked',
             column_map={'Feature': 'Parameter omschrijving', 'Value': 'Gerapporteerde waarde', 'Unit': 'Eenheid omschrijving'})

print(wi.df.head(100))
print(wi.units)
