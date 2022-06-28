import pandas as pd
from pint import UnitRegistry
from pint.errors import UndefinedUnitError
import re
from wadi.utils import check_arg

VALID_CONVERT_NANS_OPTIONS = ['delete', 'halve']
VALID_DUPLICATE_COLS_OPTIONS = ['keep_first', 'keep_all']

class Harmonizer(object):
    """
    Class for harmonizing 

    Examples
    --------

    TBC::
    """

    def __init__(self,
                 target_units='mg/l', # str, immutable
                 convert_nans='halve', # str, immutable
                 drop_columns=None,
                ):
        """
        Parameters
        ----------
        """
        self.target_units = target_units
        self.convert_nans = check_arg(convert_nans, VALID_CONVERT_NANS_OPTIONS)
        self.drop_columns = drop_columns or []

        self.ureg = UnitRegistry()
        self.target_units = self.ureg(target_units)

        lt_symbol = '<'
        RE = rf"^\s*{lt_symbol}\s*"
        find_bds = re.compile(RE)


    def convert_data(self,):
        


df[col] = data.apply()        
    def str2pint(self,
                 s,
                ):
        try:
            return self.ureg.Quantity(s)
        except (UndefinedUnitError, ValueError):
            print(f"Package 'pint' could not identify unit '{s}'")
            return None

    def harmonize(self,
                  s_dict,
                 ):
        
        df = pd.DataFrame()

        for key, value in s_dict.items():
            if key in self.drop_columns:
                continue
            datatype = value['type']
            data = value['data'].dropna()
            if (datatype == 'feature'):
                col = value['header']['alias']
                u = value['unit']['alias']
                print(datatype, u)
                q = self.str2pint(u)
            # if q:
            #     q = q.to('moles/l', 'chemistry', mw = 5 * self.ureg('g/mol'))
            #     #print(pd.to_numeric(value['values'], errors='coerce') * q)
                df[col] = data.apply(self.convert_data)
            else:
                df[key] = data
              
                

        print(df)


