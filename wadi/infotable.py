from collections import UserDict
import pandas as pd
import re

DICT_KEYS = ['name', 
             'unit', 
             'values',
             'sampleids', # Only for stacked 
             'datatype',
             'alias_n',
             'alias_u',
             'u_str',
            ]

class InfoTable(UserDict):
    """
    Nested dictionary that stores information about the imported data.
    Note that the keys of the level-0 dictionary are referred to as
    key_0. The level-1 dictionaries is referred to as dict_1 and 
    their keys as key_1.
    
    Each dict in the InfoTable will contain the following items:
     * name: the name of the feature
     * unit: the feature's units
     * sampleids (only for stacked data): the sample identifiers
     * values: a view to the (concentration) values in self.df
     * datatype: to indicate if the data are for a feature or sampleinfo
     * alias_n: the name alias
     * alias_u: the unit alias
     * u_str: the string parsed by str2pint in the UnitConverter
    """

    def __init__(self,
        df,
        format,
        c_dict,
        units, 
        datatypes,
        ):
        """
        Initialization method. Creates a nested dict with information
        about the imported data.

        Parameters
        ----------
        df : DataFrame
            The DataFrame of the DataObject class instance
        format : str
            The format of the data. Must be in VALID_FORMATS defined
            in reader.py.
        c_dict : dict
            Dictionary that maps the column names of a stacked-format
            data file to the compulsory column names in WaDI as defined
            in REQUIRED_COLUMNS_S in reader.py.
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

        # Use the c_dict to identify the names of the columns with
        # the sampleids, the features (either sample information 
        # like location or the name of a chemical substance), the
        # units and the measurement values.
        if (format == 'stacked'):
            col_s = c_dict['SampleId']
            col_f = c_dict['Features']
            col_u = c_dict['Units']
            col_v = c_dict['Values']

            # _col_s must be a list otherwise the creation
            # of a MultiIndex DataFrame in Harmonizer.harmonize
            # will fail.
            if not isinstance(col_s, list):
                col_s = [col_s]

        # Populate the InfoTable depending on the data format
        dict_0 = {}
        if (format == 'stacked'):
            # Find the unique combinations of features + units in the DataFrame
            ufus = (df[col_f] + df[col_u].fillna('')).dropna().unique()
            for fu in ufus:
                # Select a unique feature + unit combination
                idx = (df[col_f] + df[col_u].fillna('') == fu)
                # Set the key in the infotable to the first element in the
                # feature name column (all values in the column will be equal)
                key_0 = df.loc[idx, col_f].iloc[0]
                # Define the dictionary with the required data
                dict_1 = {'name': key_0,
                          'unit': df.loc[idx, col_u].iloc[0], 
                          'sampleids': df.loc[idx, col_s],
                          'values': df.loc[idx, col_v],
                          'datatype': 'feature'}
                # Add dict_1 to the info_table
                dict_0[key_0] = dict_1
        elif (format == 'wide'):
            # Iterate over the columns in the DataFrame
            for i, key_0 in enumerate(df.columns):
                # Pandas adds a dot followed by a number for duplicate columns
                # so to get the real feature name, it must be removed
                col_name = key_0
                duplicate_nr = re.search('\.\d+$', col_name)
                if duplicate_nr:
                    col_name = col_name.removesuffix(duplicate_nr.group()) # Requires Python 3.9 or later
                # Define the dictionary with the required data
                dict_1 = {'name': col_name,
                          'unit': units[i], 
                          'values': df[key_0],
                          'datatype': datatypes[i]}
                # Add dict_1 to the info_table
                dict_0[key_0] = dict_1

        # Add aliases to ensure an alias is always defined, 
        # even if mapping does not result in any match.
        for key_0 in dict_0.copy(): # Iterate over copy to be sure
            dict_1 = dict_0[key_0]
            dict_1['alias_n'] = dict_1['name']
            dict_1['alias_u'] = dict_1['unit']
            dict_1['u_str'] = None
            dict_0[key_0] = dict_1   
        
        # The harmonize method of Harmonizer needs target_index for
        # the DataFrame it will create.
        if (format == 'stacked'):
            sampleids = df[col_s].copy()
            self.target_index = pd.MultiIndex.from_frame(sampleids).unique()
        elif (format == 'wide'):
            self.target_index = None

        # Call the ancestor init method to initiliaze the class with
        # the dictionary just created.
        super().__init__(dict_0)

    def __setitem__(self, key, value):
        """
        Setter method for items in the dictionary. The value passed
        is a dictionary and the method checks if its keys are all
        valid. It also adds two elements ('alias_n' and 'alias_u')
        so that a name or unit alias is always defined.

        Parameters
        ----------
        key : str
            The name of the key in the dictionary to assign 'value' to.
        value : dict
            The dictionary to assign to element 'key'.

        Raises
        ----------
        TypeError
            When the keys in 'value' are not in DICT_KEYS.

        """
        # Check if all keys in 'value' are valid.
        if not all([k in DICT_KEYS for k in value]):
            raise TypeError("Invalid dict")

        # Assign 'value' to element 'key'.
        self.data[key] = value

    def list_dict1_item(self, item):
        """
        This function iterates over all the (sub-)dictionaries in
        the InfoTable and retrieves the value of element 'item'. All
        items are collected in a list using list comprehension.

        Parameters
        ----------
        item : str
            The name of the key in the dictionary to be retrieved.

        Returns
        ----------
        result : list
            List of the values stored in element 'item' in the 
            (sub-)dictionaries of the InfoTable.
        """
        return [i[item] for i in self.data.values()]

    def list_keys(self):
        """
        This function returns the level-0 keys (key0) as a list.

        Returns
        ----------
        result : list
            List of the level-0 keys of the InfoTable.
        """
        return list(self.data.keys())

    def __str__(self):
        """
        This method provides the string representation of the
        InfoTable that is printed to the WaDI log file.

        Returns
        ----------
        result : str
            String that describes the contents of the InfoTable.
        """
        rv = ""
        for datatype in ['sampleinfo', 'feature']:
            s = ""
            rv += f"\n* The following {datatype} data were imported:\n"
            for key_0, dict_1 in self.data.items():
                if dict_1['datatype'] == datatype:
                    s += f" - name: {key_0}, unit: {dict_1['unit']}\n"
            if len(s):
                rv += s
            else:
                rv += " - None\n"
        
        return rv[:-1] # Remove trailing carriage return

    def update_items(self, a_dict):
        """
        This method iterates over the level-0 items of the dictionary
        and updates the level-1 dictionaries with the items in a_dict.

        Parameters
        ----------
        a_dict : dict
            Nested dictionary of which they keys correspond to the 
            level-0 keys of the current dictionary. Its values are
            level-1 dictionaries. The level-1 items of the current
            dictionary will be updated with those from a_dict. The
            item values of the current dictionary are not overwritten
            if an item_value in a_dict is None.
        """
        for key_0, dict_1 in a_dict.items():
            for key_1, value in dict_1.items():
                if value is not None:
                    self.data[key_0][key_1] = value
                        

