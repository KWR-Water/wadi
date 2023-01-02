from collections import UserDict

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