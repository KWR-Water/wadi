#import pandas as pd
from pint import UnitRegistry
from pint.errors import UndefinedUnitError
from wadi.utils import check_arg

VALID_CONVERT_NANS_OPTIONS = ['delete', 'halve']
VALID_DUPLICATE_COLS_OPTIONS = ['keep_first', 'keep_all']

class UnitConverter(object):
    """
    Class for harmonizing 

    Examples
    --------

    TBC::
    """

    def parse_units(self,
                   ):
        for m in matches:
            if m:
                columns = m.groupdict().keys()
                break
        ncol = len(columns)
        data = []
        for m in matches:
            if m:
                data.append([v for v in m.groupdict().values()])
            else:
                data.append(['' for n in range(ncol)])
        df = pd.DataFrame(data, columns=columns)
        self.df = self.df.join(df)

    def str2pint(self,
                ):
            try:
                Q_ = self.ureg.Quantity
                #print(s, Q_(s))
            except UndefinedUnitError:
                #print(s, "Could not idenify unit")
                pass

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
                 duplicate_cols='keep', # str immutable
                ):
        """
        Parameters
        ----------
        """
        self.target_units = target_units
        self.convert_nans = check_arg(convert_nans, VALID_CONVERT_NANS_OPTIONS)
        self.duplicate_cols = check_arg(duplicate_cols, VALID_DUPLICATE_COLS_OPTIONS)

        self.ureg = UnitRegistry()

    def harmonize(self,
                  s_dict,  
                 ):
        strings = [v['unit']['regex'] for v in s_dict.values()]
        #for s in strings:
        #    print(s)


