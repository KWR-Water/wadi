import molmass as mm
from molmass.molmass import FormulaError
import pandas as pd
from pint import UnitRegistry
from pint.errors import DimensionalityError, UndefinedUnitError
import re
from wadi.base import WadiBaseClass
from wadi.utils import check_if_nested_list

# Suppress performance warnings for that occur during harmonize because
# DataFrame can contain lots of NaNs
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

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
                 parent,
                #  convert_units=False,
                #  target_units='mg/l', # str, immutable
                #  override_units=None,
                # #  convert_bds='halve', # str, immutable
                #  lt_symbol='<', # str, immutable
                #  drop_columns=None,
                #  merge_columns=None,
                ):
        """
        Parameters
        ----------
        """

        WadiBaseClass.__init__(self)

        self.parent = parent
        
        self.convert_units = False
        self.target_units = 'mg/l'
        self.override_units = {}
        self.drop_columns = []
        self.merge_columns = []

        self.ureg = UnitRegistry()
        self.ureg.default_format = "~"

        # self._bd_factor = BD_FACTORS[check_arg(convert_bds, BD_FACTORS.keys())]   
        self._bd_RE = rf"(^\s*<\s*)"

    # Defining __call__ method
    def __call__(self,
                 convert_units=False,
                 target_units='mg/l', # str, immutable
                 override_units=None,
                 lt_symbol='<', # str, immutable
                 drop_columns=None,
                 merge_columns=None,
                ):

        self.convert_units = convert_units
        self.target_units = target_units
        self.override_units = override_units or {}
        self.drop_columns = drop_columns or []
        self.merge_columns = merge_columns or []
        check_if_nested_list(self.merge_columns)

        self._bd_RE = rf"(^\s*{lt_symbol}\s*)"    
        
        return self.harmonize()

    def _convert_values(self, v, uc_factor):
        """
        Convert cell values using the unit conversion factor. This
        function is used in harmonize with the Pandas 'apply' function
        and is needed because (i) values below a detection limit
        cannot be converted simply by multiplying and (ii) some cell
        values are imported as strings even though they are numbers
        """
        # If the cell value is not a string, it is (always?) a float
        # so the function can directly return the cell value times the
        # unit conversion factor
        if not isinstance(v, str):
            return v * uc_factor

        # Use the regex split function to split the string. A cell value
        # like <0.5 will be parsed into the following list ['', '<', '0.5']
        substrings = re.split(self._bd_RE, v)
        # Check if there are three substrings
        if (len(substrings) == 3):
            # Convert the third substring to a float and apply the uc_factor
            rv = float(substrings[2]) * uc_factor
            # Prefix the smaller-than symbol and return as a string
            return f"{substrings[1]}{rv}"
        # If the split function returned only one value it can be a number
        # In that case try to convert the substring to a float and return
        # it after applying the conversion factor
        elif (len(substrings) == 1):
            try:
                return float(substrings[0]) * uc_factor
            # If a value error occurs the substring was not a number and
            # the input value is simply returned
            except ValueError: 
                return v
        else:
            # If all of the above fails, simply return the input value
            return v

    def _get_mw(self,
                s,
               ):
        """
        """
        try:
            return mm.Formula(s).mass * self.ureg('g/mol')
        except FormulaError:
            return None

    def _str2pint(self,
                  col,
                  s,
                 ):
        """
        """
        try:
            s_parts = s.partition('|') # split into three parts
            mw_formula = s_parts[2]
            if not len(mw_formula):
                mw_formula = col
            mw = self._get_mw(mw_formula)
            self._log(f" * Successfully parsed unit '{s}' with pint for {col}")
            if (mw is not None): 
                self._log(f"   - molecular weight: {mw}")
            return self.ureg.Quantity(s_parts[0]), mw
        except (AttributeError, TypeError, UndefinedUnitError, ValueError):
            self._log(f" * Failed to parse unit '{s}' with pint for {col}")
            return None, ''

    def harmonize(self,
                 ):
        
        self._log("Harmonizing...")

        if (self.parent.format == 'stacked'):
            sampleids = self.parent.df[self.parent._col_s].copy()
            index = pd.MultiIndex.from_frame(sampleids).unique()
        elif (self.parent.format == 'wide'):
            index = None
        df = pd.DataFrame(index=index)

        column_header_dict = {}
        units_header_dict = {}
        # Iterate over items in infotable
        #for key, i_dict in infotable.items():
        for key, i_dict in self.parent._infotable.items():
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
                if isinstance(i_dict['sampleids'], pd.DataFrame):
                    values = values.set_axis(pd.MultiIndex.from_frame(i_dict['sampleids']))
                else:
                    values = values.set_axis(i_dict['sampleids'])

                if (any(values.index.duplicated())):
                    values = values.loc[~values.index.duplicated()]
                    self._warn(f"Duplicate sampleids found for {key}. Keeping only first occurrence.")
                    
            values = pd.to_numeric(values.dropna(), errors='ignore')

            # The column name in the new DataFrame will be the item's alias
            alias_n = i_dict['alias_n']
            alias_u = i_dict['alias_u']
            
            # Check the datatype ('sampleinfo' or 'feature')
            datatype = i_dict['datatype']

            # Process the data depending on the datatype
            # For features, convert units and handle values
            # below the detection limit
            if (self.convert_units and (datatype == 'feature')):
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
                        if (mw is None): 
                            uc = q.to(target_units)
                        else:
                            uc = q.to(target_units, 'chemistry', mw=mw)
                        uc_factor = uc.magnitude
                        alias_u = uc.units
                    except DimensionalityError:
                        pass
                
                values = values.apply(self._convert_values, 
                                      uc_factor=uc_factor)
            
            if any(values.index.duplicated()):
                for i in values.index:
                    print(i)

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

        # Write the logged messages to the log file
        self.update_log_file(f"{self.parent._log_fname}.log")

        return df