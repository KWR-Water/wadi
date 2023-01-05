import pandas as pd
import re

import molmass as mm
from molmass.molmass import FormulaError
from pint import UnitRegistry
from pint.errors import DimensionalityError, UndefinedUnitError
from wadi.base import WadiChildClass
from wadi.utils import check_if_nested_list

# Suppress performance warnings for that occur during harmonize because
# DataFrame can contain lots of NaNs
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

BD_FACTORS = {'delete': 0, 'halve': 0.5}
# VALID_DUPLICATE_COLS_OPTIONS = ['keep_first', 'keep_all']

class Harmonizer(WadiChildClass):
    """
    Class for harmonizing 

    Examples
    --------

    TBC::
    """

    def __init__(self,
                 converter,
                #  convert_units=False,
                #  target_units='mg/l', # str, immutable
                #  override_units=None,
                # #  convert_bds='halve', # str, immutable
                #  lt_symbol='<', # str, immutable
                #  drop_columns=None,
                #  merge_columns=None,
                ):
        """
        Function that ...

        Parameters
        ----------
        file_path : str
            The file to be read.

        Returns
        ----------
        result : list
            List with the values read.

        Raises
        ------
        ValueError
            When index_col is a kwarg in one of the panes.

        Notes
        ----------
        The return ...

        """

        super().__init__(converter)
        
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

        Parameters
        ----------
        v : float or str
            The value to be converted.
        uc_factor : float
            The unit conversion factor.

        Returns
        ----------
        result : float
            The converted value.

        Raises
        ------
        ValueError
            If the conversion fails for some reason.

        Notes
        ----------
        The return ...
        """
        # If the cell value is not a string, it is (always?) a float
        # so the function can directly return the cell value times the
        # unit conversion factor.
        if not isinstance(v, str):
            return v * uc_factor

        # Use the regex split function to split the string. A cell value
        # like <0.5 will be parsed into the following list ['', '<', '0.5'].
        substrings = re.split(self._bd_RE, v)
        # Check if there are three substrings
        if (len(substrings) == 3):
            # Convert the third substring to a float and apply the uc_factor.
            rv = float(substrings[2]) * uc_factor
            # Prefix the smaller-than symbol and return as a string.
            return f"{substrings[1]}{rv}"
        # If the split function returned only one value it can be a number.
        # In that case try to convert the substring to a float and return
        # it after applying the conversion factor.
        elif (len(substrings) == 1):
            try:
                return float(substrings[0]) * uc_factor
            # If a value error occurs the substring was not a number and
            # the input value is simply returned.
            except ValueError: 
                return v
        else:
            # If all of the above fails, simply return the input value.
            return v

    def _get_mw(self,
                s,
               ):
        """
        This function returns the molar mass of a substance. Uses
        the molmass library.

        Parameters
        ----------
        s : str
            Name of the substance.

        Returns
        ----------
        result : Pint Quantity object
            The molar mass in g/mole, or None if  a FormulaError 
            was raised from within the molmass library.
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
        This function parses the three-part string that is created by
        _match_regex when the units are mapped using a regular 
        expression.

        Parameters
        ----------
        col : str
            Column name.
        s : str
            String to be parsed.

        Returns
        ----------
        uq : Pint Quantity object
            The units represented as Pint Quantity object.
        mw : Pint Quantity object
            The molecular mass of the substance.

        Notes
        ----------
        The function uses the partition function to split the 
        string at the | symbol into a three-part tuple that
        contains (i) the part before the separator, (ii) the 
        separator itself (redundant, not used), and (iii) the 
        part after the separator. 
        The part after the | symbol may or may not contain the 
        formula for the molecular mass, depending on the format 
        for the units in the input file. In that case name of 
        the feature (passed to the function as 'col') is used 
        as the formula to determine the molecular mass.
        Both the units and the molecular mass are converted to a 
        Pint Quantity object (i.e., the product of a unit and 
        a magnitude).
        """
        try:
            # Use the partition to split the string at the | symbol.
            s_parts = s.partition('|')
            # Store the substance formula in mw_formula.
            mw_formula = s_parts[2]
            # If no formula was specified the length of  mw_formula
            # will be zero and in that case 'col' will be used instead
            # to look up the molecular mass.
            if not len(mw_formula):
                mw_formula = col
            # Get the molecular mass using _get_mw
            mw = self._get_mw(mw_formula)
            # Convert the units string to a Pint Quantity object
            uq = self.ureg.Quantity(s_parts[0])
            print(uq, type(uq), mw, type(mw))
            # Write a message to the log file
            self._log(f" * Successfully parsed unit '{s}' with pint for {col}")
            if (mw is not None): 
                self._log(f"   - molar mass: {mw}")

            return uq, mw
        except (AttributeError, TypeError, UndefinedUnitError, ValueError):
            # When an error occurs, write a message to the log file and 
            # return empty return values.
            self._log(f" * Failed to parse unit '{s}' with pint for {col}")
            return None, None

    def harmonize(self):
        """
        This function performs the harmonize operation, that is it
        convert the units to the target units desired by the user, it
        deletes any undesired columns and merges columns, when 
        specified by the user.

        Returns
        ----------
        df : DataFrame
            DataFrame with the converted values.
        """        
        self._log("Harmonizing...")

        # Initialize the DataFrame to be created. Uses the target_index 
        # by the InfoTable that ensures that the sampleids for
        # stacked data are uniquely defined. For wide data the 
        # target_index is None, and the DataFrame will have an 
        # ordinary RangeIndex.
        df = pd.DataFrame(index=self.converter._infotable.target_index)

        # Create empty dictionaries that will be filled with values
        # of alias_n and alias_u, respectively, to be able to assign
        # the right values to the DataFrame columns at the end.
        column_header_dict = {}
        units_header_dict = {}
        # Iterate over items in the InfoTable.
        for key, i_dict in self.converter._infotable.items():
            # Do not process items that the user has indicated 
            # should be skipped.
            if key in self.drop_columns:
                self._log(f" * Dropping column: {i_dict['name']}")
                continue
                    
            # The actual data are Pandas Series that are a view
            # to the DataFrame created in read_data().
            values = i_dict['values']
            
            # For wide-format data, the index is a default RangeIndex
            # but for stacked-format data a new index must be created 
            # to be able to match the feature data to the samples. 
            # Stacked data are identifiable from the InfoTable's 
            # i_dict entry because, unlike wide data, it will have a
            # 'sampleids' key.
            if ('sampleids' in i_dict):
                # If the user specified multiple columns as the
                # sampleid (for example a sample location + a sample
                # date), the the value for 'sampleids' will be a 
                # DataFrame and the new index will be a MultiIndex...
                if isinstance(i_dict['sampleids'], pd.DataFrame):
                    values = values.set_axis(pd.MultiIndex.from_frame(i_dict['sampleids']))
                # ... but if only a single column identifies the 
                # sampleids, then the value for 'sampleids' will be
                # a Series.
                else:
                    values = values.set_axis(i_dict['sampleids'])
                
                # Even if multiple columns identify the sampleids, 
                # duplicate entries can still occur in the index, 
                # for example when multiple measurement methods
                # have been used for a single parameter without
                # properly documenting this in the original file.
                # In that case, the duplicate values are simply 
                # discarded, effectively keeping only the first
                # sample. 
                if (any(values.index.duplicated())):
                    values = values.loc[~values.index.duplicated()]
                    # Warn the user, this is a crude approach and
                    # the user may wish to adjust the original file.
                    self._warn(f"Duplicate sampleids found for {key}. \
                        Keeping only first occurrence.")

            # Rows with NaNs can be dropped for faster processing, 
            # since all Series share a common index, they are easily 
            # pieced together at the end into a new DataFrame.        
            values = pd.to_numeric(values.dropna(), errors='ignore')

            # The column name in the new DataFrame will be the item's
            # alias...
            alias_n = i_dict['alias_n']
            # ... and the units will be the item's unit alias.
            alias_u = i_dict['alias_u']
            
            # Get the datatype ('sampleinfo' or 'feature')
            datatype = i_dict['datatype']

            # Process the data depending on the datatype
            # For features, convert units and handle values
            # below the detection limit
            if (self.convert_units and (datatype == 'feature')):
                # Define a unit conversion factor that will be used
                # if the unit parsing code below does not yield a 
                # valid conversion factor (e.g., in case unit parsing
                # by Pint fails).
                uc_factor = 1.0
                # Try to parse the unit string with Pint. Returns the 
                # Pint Quantity objects q (for the units) and mw (for
                # the molar mass) to be used for unit conversion.
                q, mw = self._str2pint(alias_n, alias_u)
                # q may be None if the units were not properly 
                # identified by Pint
                if q is not None:
                    try:
                        # The user may wish to override the general
                        # target units, in which case the desired
                        # units were passed in the dict override_units.
                        if (key in self.override_units):
                            target_units = self.override_units[key]
                        else:
                            target_units = self.target_units
                        # Use Pint to determine the value of the unit
                        # conversion factor.
                        if (mw is None): 
                            uc = q.to(target_units)
                        # If the molar mass has been determined in
                        # _str2pint then use Pint's 'chemistry' 
                        # context to determine the conversion factor.
                        else:
                            uc = q.to(target_units, 'chemistry', mw=mw)
                        # uc is a Quantity object, for converting the 
                        # measurements, only the magnitude attribute
                        # is needed...
                        uc_factor = uc.magnitude
                        # ... and the units attribute becomes the unit 
                        # alias.
                        alias_u = uc.units
                    # Ignore any DimensionalityError raised by Pint (in
                    # that case the unit conversion factor stays 1.0).
                    except DimensionalityError:
                        pass
                
                # Convert the measurement values using _convert_values.
                values = values.apply(self._convert_values, 
                                      uc_factor=uc_factor)
            
            # Add the values Series as a column to the new DataFrame
            df[key] = values

            # Replace the original name and units by their aliases
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
        
        # Assign a nested list to df.columns. This way the column
        # headings become a MultiIndex, so that both the column names
        # and the units appear above the columns in the DataFrame
        df.columns = [[column_header_dict[c] for c in df.columns],
                      [units_header_dict[c] for c in df.columns]]        

        # Write the logged messages to the log file
        self.update_log_file()

        # Return the DataFrame
        return df