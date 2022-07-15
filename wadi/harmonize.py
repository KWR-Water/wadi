import molmass as mm
from molmass.molmass import FormulaError
import pandas as pd
from pint import UnitRegistry
from pint.errors import DimensionalityError, UndefinedUnitError
import re
from wadi.base import WadiBaseClass
from wadi.utils import check_arg, check_if_nested_list

BD_FACTORS = {'delete': 0, 'halve': 0.5}
# VALID_DUPLICATE_COLS_OPTIONS = ['keep_first', 'keep_all']

class Harmonizer(WadiBaseClass):
    """
    Class for harmonizing 

    Examples
    --------

    TBC::
    """

    def __init__(self,
                 target_units='mg/l', # str, immutable
                 override_units=None,
                 convert_bds='halve', # str, immutable
                 lt_symbol='<', # str, immutable
                 drop_columns=None,
                 merge_columns=None,
                ):
        """
        Parameters
        ----------
        """

        WadiBaseClass.__init__(self)

        self.target_units = target_units
        self.override_units = override_units or {}
        self.drop_columns = drop_columns or []
        self.merge_columns = merge_columns or []
        check_if_nested_list(self.merge_columns)

        self.ureg = UnitRegistry()
        self.ureg.default_format = "~"

        self._bd_factor = BD_FACTORS[check_arg(convert_bds, BD_FACTORS.keys())]   
        self._bd_RE = rf"^\s*{lt_symbol}\s*"

    def _convert_bd(self, v):
        """
        Checks for values below the detection limit (bd)
        """

        if not isinstance(v, str):
            return v

        rv = re.split(self._bd_RE, v)
        if (len(rv) == 2):
            return float(rv[1]) * self._bd_factor
        else:
            return None
    
    def _get_mw(self,
                s,
               ):
        try:
            return mm.Formula(s).mass * self.ureg('g/mol')
        except FormulaError:
            # self._warn(f"Could not determine molar mass for {s}.")
            return 1
         
    def _str2pint(self,
                  col,
                  s,
                 ):
        try:
            s_parts = s.partition('|') # split into three parts
            mw_formula = s_parts[2]
            if not len(mw_formula):
                mw_formula = col
            mw = self._get_mw(mw_formula)
            self._log(f" * Successfully parsed unit '{s}' with pint for {col}")
            return self.ureg.Quantity(s_parts[0]), mw
        except (AttributeError, TypeError, UndefinedUnitError, ValueError):
            self._log(f" * Failed to parse unit '{s}' with pint for {col}")
            return None, ''

    def harmonize(self,
                  infotable,
                  index=None,
                 ):
        
        self._log("Harmonizing...")

        df = pd.DataFrame(index=index)

        column_header_dict = {}
        units_header_dict = {}
        # Iterate over items in infotable
        for key, i_dict in infotable.items():
            # Do not process items that the user has indicated 
            # should be skipped
            if key in self.drop_columns:
                self._log(f" * Dropping column: {i_dict['name']}")
                continue
                    
            # The actual data are Pandas Series that are a view
            # to the DataFrame created in read_data(). Rows with
            # nans can be dropped for faster processing, since all
            # Series share a common index, they are easily pieced
            # together at the end into a new DataFrame
            values = i_dict['values']
            if ('sampleids' in i_dict): # For stacked data
                values = values.set_axis(i_dict['sampleids'])
            values = values.dropna()

            # The column name in the new DataFrame will be the item's alias
            alias_n = i_dict['alias_n']
            alias_u = i_dict['alias_u']

            # Check the datatype ('sampleinfo' or 'feature')
            datatype = i_dict['datatype']

            # Process the data depending on the datatype
            # For features, convert units and handle values
            # below the detection limit
            if (datatype == 'feature'):
                # Try to parse the unit string with pint. Returns a pint
                # Quantity object q and the molecular weight to be used for
                # unit conversion
                q, mw = self._str2pint(alias_n, alias_u)
                uc_factor = 1
                if q is not None:
                    try:
                        if (key in self.override_units):
                            target_units = self.override_units[key]
                        else:
                            target_units = self.target_units
                        uc = q.to(target_units, 'chemistry', mw=mw)
                        uc_factor = uc.magnitude
                        alias_u = uc.units
                    except DimensionalityError:
                        pass
                values = values.apply(self._convert_bd).multiply(uc_factor)
            
            df[key] = values
            
            column_header_dict[key] = alias_n
            units_header_dict[key] = alias_u
      
        # Check for any columns to be merged. Iterates through the lists in 
        # merge_columns. The first list element is the column of which the
        # NaN values must be replaced by the non-NaN values in the subsequent 
        # columns in the list.
        for l in self.merge_columns:
            self._log(f" * NaN values in {l[0]} will be replaced with values from {', '.join(c for c in l[1:])}")
            for c in l[1:]:
                df[l[0]].fillna(df[c], inplace=True)
                column_header_dict.pop(c)
                units_header_dict.pop(c)
            df.drop(l[1:], axis=1, inplace=True)

        df.columns = [[column_header_dict[c] for c in df.columns],
                      [units_header_dict[c] for c in df.columns]]        

        return df