import json
import numpy as np
import pickle

# Step 0
# Open the pickle file created by Martin van der Schans
df = pickle.load(open('feature_map.pkl', "rb"))
# The index of the loaded DataFrame has duplicate entries
# (integers) so replace it with a monotonically increasing 
# range of integers
df = df.set_index(np.arange(len(df), dtype=int))

# Only store these columns in the json file
cols = ['Feature', 
        'HGC', 
        'MicrobialParameters', 
        'OtherEnglishAlias', 
        'OtherDutchAlias', 
        'SIKB', 
        'NVWA', 
        'REWAB', 
        'ValidCas', 
        'ValidCid',
       ]

# Step 1
# Convert the DataFrame to a json file that will be used in WADI
# Start with an empty dict, this will become a nested dict with
# the column names as keys and a dict of row values as value
dicts = {}
# Loop over the desired columns
for col in cols:
    # Find which elements in the column are not an empty list
    idx = df[col].astype(bool) # Trick: returns False for elements with empty list
    # Keep only the elements with a non-empty list and convert to dict
    # Store the dict in the nested dict with the column name as the key    
    dicts[col] = df.loc[idx, col].to_dict()

# Save the nested dict to default_feature_map.json 
with open('default_feature_map.json', 'w') as file:
    json.dump(dicts, file)

file.close()