from collections import UserDict
import pandas as pd
import re

DICT_KEYS = ['name', 
             'unit', 
             'values',
             'sampleids', # Only for stacked 
             'datatype'
            ]

class InfoTable(UserDict):
    """
    Class for importing hydrochemical data in a variety of formats

    Examples
    --------

    TBC::
    """
    def __init__(self,
        df,
        format,
        c_dict,
        units, 
        datatypes,
        ):
        """
        Creates a nested dict with information about the imported data.
        Each dict in the infotable will contain the following items:
        - 'name': the name of the feature
        - 'unit': the feature's units
        - 'sampleids' (only for stacked data): the sample identifiers
        - 'values': a view to the (concentration) values in self.df
        - 'datatype': to indicate if the data are for a feature or sampleinfo

        Parameters
        ----------
        units : list of strings
            List with the units for each feature (or sampleinfo data). This
            list is created by the '_read_file' function based on the unit_row
            kwarg passed by the user to read_data.
        datatypes : list of strings
            List with the datatype for each feature (or sampleinfo data). This
            list is created by the '_read_file' function based on the datatype
            kwarg passed by the user to read_data. Datatypes must all 
            be in VALID_DATATYPES.
        """

        if (format == 'stacked'):
            # _col_s must be a list otherwise the creation
            # of a MultiIndex DataFrame in Harmonizer.harmonize
            # will fail
            if isinstance(c_dict['SampleId'], list):
                col_s = c_dict['SampleId']
            else:
                col_s = [c_dict['SampleId']]
            col_f = c_dict['Features']
            col_u = c_dict['Units']
            col_v = c_dict['Values']

        # Populate the infotable depending on the data format
        j_dict = {}
        if (format == 'stacked'):
            # Find the unique cominations of features + units in the DataFrame
            ufus = (df[col_f] + df[col_u]).dropna().unique()
            for fu in ufus:
                # Select a unique feature + unit combination
                idx = (df[col_f] + df[col_u] == fu)
                # Set the key in the infotable to the first element in the
                # feature name column (all values in the column will be equal)
                key = df.loc[idx, col_f].iloc[0]
                # Define the dictionary with the required data
                i_dict = {'name': key,
                          'unit': df.loc[idx, col_u].iloc[0], 
                          'sampleids': df.loc[idx, col_s],
                          'values': df.loc[idx, col_v],
                          'datatype': 'feature'}
                # Add i_dict to the info_table
                j_dict[key] = i_dict
        elif (format == 'wide'):
            # Iterate over the columns in the DataFrame
            for i, key in enumerate(df.columns):
                # Pandas adds a dot followed by a number for duplicate columns
                # so to get the real feature name, it must be removed
                col_name = key
                duplicate_nr = re.search('\.\d+$', col_name)
                if duplicate_nr:
                    col_name = col_name.removesuffix(duplicate_nr.group()) # Requires Python 3.9 or later
                # Define the dictionary with the required data
                i_dict = {'name': col_name,
                          'unit': units[i], 
                          'values': df[key],
                          'datatype': datatypes[i]}
                # Add i_dict to the info_table
                j_dict[key] = i_dict

        # Harmonize method of Harmonizer needs target_index
        if (format == 'stacked'):
            sampleids = df[col_s].copy()
            self.target_index = pd.MultiIndex.from_frame(sampleids).unique()
        elif (format == 'wide'):
            self.target_index = None

        super().__init__(j_dict)

    def __setitem__(self, key, value):
        if not all([k in DICT_KEYS for k in value]):
            raise TypeError("Invalid dict")
        # Add aliases to ensure an alias is always defined, 
        # even if mapping does not result in any match
        value['alias_n'] = value['name']
        value['alias_u'] = value['unit']
        self.data[key] = value

    def list(self, item):
        return [i[item] for i in self.data.values()]

    def __str__(self):
        rv = ""
        for datatype in ['sampleinfo', 'feature']:
            s = ""
            rv += f"The following {datatype} data were imported:\n"
            for key, value in self.data.items():
                if value['datatype'] == datatype:
                    s += f"  * name: {key}, unit: {value['unit']}\n"
            if len(s):
                rv += s
            else:
                rv += "None\n"
        
        return rv[:-1] # Remove trailing carriage return