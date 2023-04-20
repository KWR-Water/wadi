import pandas as pd
import re
from wadi.base import WadiBaseClass
from wadi.mapper import MapperDict
from wadi.utils import check_if_nested_list
from wadi.unitconverter import UnitConverter

# Suppress performance warnings for that occur during harmonize because
# DataFrame can contain lots of NaNs
import warnings

warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

# BD_FACTORS = {"delete": 0, "halve": 0.5}
# VALID_DUPLICATE_COLS_OPTIONS = ['keep_first', 'keep_all']


class Harmonizer(WadiBaseClass):
    """
    WaDI class for transforming the data to a harmonized format.
    """

    def __init__(
        self,
    ):
        """
        Class initialization method.
        """
        # Call the ancestor's initialization method to define the 
        # generic class attributes and methods.
        super().__init__()

        self._convert_units = False
        self._target_units = "mg/l"
        self._override_units = {}
        self._drop_columns = []
        self._merge_columns = []

        # self._bd_factor = BD_FACTORS[check_arg(convert_bds, BD_FACTORS.keys())]
        # Define the regular expression that searches for values below 
        # or above the detection limit.
        self._bd_RE = rf"(^\s*[<>]\s*)"
        # Define decimal separator symbol that deviates from a dot.
        self._decimal_str = ","

        # Initialize a UnitConverter object that will be used to 
        # determine the unit conversion factor.
        self._unit_converter = UnitConverter()

    def __call__(
        self,
        convert_units=False,
        target_units="mg/l",  # str, immutable
        override_units=None,
        drop_columns=None,
        merge_columns=None,
        detection_limit_symbols="<>",  # str, immutable
        decimal_str=",",  # str, immutable
    ):
        """
        This method provides an interface for the user to set the
        attributes that determine the Harmonizer object behavior.

        Parameters
        ----------
        convert_units : bool, optional
            When True, the units will be converted to the specified
            target units. Default: False
        target_units : str, optional
            The desired target units. Must be a string in a format
            that Pint can parse. Default: mg/l
        override_units : dict, optional
            A dictionary which specifies the column names for which
            'target_units' must be ignored and replaced with the
            units specified as the values of the dictionary.
        drop_columns : list, optional
            A list of columns that should not appear in the
            harmonized DataFrame.
        merge_columns : list, optional
            A nested list of columns names that will be merged into
            a single column. Each list element can contain any number
            of column names. The first element in each of the list
            elements is the column to keep. Any NaN values that
            appear in this column will be replaced by non-NaN values
            from the subsequent columns in the list element.
        detection_limit_symbols : str, optional
            A string that contains the symbols that are used for
            measurement values beyond (below or above) the detection
            limit. Default: '<>' (both values below the detection
            limit, e.g. < 0.1, and above the detection limit, e.g.
            > 0.1 will be identified this way).
        decimal_str : str, optional
            The character used as the decimal separator when a number
            is represented as a string in the original data,
            typically when it is below the detection limit, for
            example '< 0,5'. Default: ','.

        Returns
        ----------
        result : DataFrame
            A DataFrame with the transformed data.
        """
        self._convert_units = convert_units
        self._target_units = target_units
        self._override_units = override_units or {}
        self._drop_columns = drop_columns or []
        self._merge_columns = merge_columns or []
        self._decimal_str = decimal_str
        check_if_nested_list(self._merge_columns)

        self._bd_RE = rf"(^\s*[{detection_limit_symbols}]\s*)"

    def _convert_values(self, v, conversion_factor):
        """
        Convert cell values using the unit conversion factor. This
        function is used in _execute with the Pandas 'apply' function
        and is needed because (i) values with a detection limit symbol
        cannot be converted simply by multiplying and (ii) some cell
        values are imported as strings even though they are numbers.

        Parameters
        ----------
        v : float or str
            The value to be converted.
        conversion_factor : float
            The unit conversion factor.

        Returns
        ----------
        result : float
            The converted value.
        """
        # If the cell value is not a string, it is (always?) a float
        # so the function can directly return the cell value times the
        # unit conversion factor.
        if not isinstance(v, str):
            return v * conversion_factor

        # Use the regex split function to split the string. A cell value
        # like <0.5 will be parsed into the following list ['', '<', '0.5'].
        substrings = re.split(self._bd_RE, v)
        # Check if there are three substrings
        if len(substrings) == 3:
            # Convert the third substring to a float and apply the uc_factor.
            rv = float(substrings[2].replace(self._decimal_str, ".")) * conversion_factor
            # Prefix the smaller-than symbol without any leading and
            # only a single trailing space and return as a string.
            return f"{substrings[1].strip()} {rv}"
        # If the split function returned only one value it can be a number.
        # In that case try to convert the substring to a float and return
        # it after applying the conversion factor.
        elif len(substrings) == 1:
            try:
                return float(substrings[0]) * conversion_factor
            # If a value error occurs the substring was not a number and
            # the input value is simply returned.
            except ValueError:
                return v
        else:
            # If all of the above fails, simply return the input value.
            return v

    def _execute(
        self,
        infotable,
    ):
        """
        This function performs the harmonize operations, that is it
        converts the units to the target units, it deletes any 
        undesired columns and merges columns.

        Parameters
        ----------
        infotable : InfoTable
            The DataObject's InfoTable. 

        Returns
        -------
        df : DataFrame
            DataFrame with the transformed data.
        """
        self._msg("Harmonizing", header=True)

        if (self._target_units == "hgc"):
               hgc_units_dict = MapperDict._create_hgc_units_dict()

        # Initialize the DataFrame to be created. Uses the target_index
        # in the InfoTable that ensures that the sampleids for
        # stacked data are uniquely defined. For wide data the
        # target_index is None, and the DataFrame will have an
        # ordinary RangeIndex.
        df = pd.DataFrame(index=infotable.target_index)

        # Create empty dictionaries that will be filled with values
        # of alias_n and alias_u, respectively, to be able to assign
        # the right values to the DataFrame columns at the end.
        column_header_dict = {}
        units_header_dict = {}

        # Iterate over items in the InfoTable. Recall that InfoTable
        # is a nested dict and key_0 is used to indicate the level-0
        # keys and dict_1 (their corresponding values) are the
        # level-1 dictionaries. This terminology is used here as well
        # for consistency with the code in infotable.py.
        for key_0, dict_1 in infotable.items():
            # Do not process items that the user has indicated
            # should be skipped.
            if key_0 in self._drop_columns:
                self._log(f"* Dropping column: {key_0}")
                continue

            # Get the datatype ('sampleinfo' or 'feature').
            datatype = dict_1["datatype"]

            self._msg(f"* Processing {key_0} ({datatype}).")

            # The actual data are Pandas Series that are a view
            # to the DataFrame created in read_data().
            values = dict_1["values"]

            # For 'wide' data, the index is a default RangeIndex
            # but for 'stacked' data a new index must be created
            # to be able to match the feature data to the samples.
            # Stacked data are identifiable from the InfoTable's
            # dict_1 keys because, unlike wide data, it will have a
            # 'sampleids' key.
            if "sampleids" in dict_1:
                # If the user specified multiple columns as the
                # sampleid (for example a sample location + a sample
                # date), the the value for 'sampleids' will be a
                # DataFrame and the new index will be a MultiIndex...
                if isinstance(dict_1["sampleids"], pd.DataFrame):
                    values = values.set_axis(
                        pd.MultiIndex.from_frame(dict_1["sampleids"])
                    )
                # ... but if only a single column identifies the
                # sampleids, then the value for 'sampleids' will be
                # a Series.
                else:
                    values = values.set_axis(dict_1["sampleids"])

                # Even if multiple columns identify the sampleids,
                # duplicate entries can still occur in the index,
                # for example when multiple measurement methods
                # have been used for a single parameter but were
                # given the same name in the original file.
                # In that case, the duplicated values are simply
                # discarded, effectively keeping only the first
                # sample.
                if any(values.index.duplicated()):
                    values = values.loc[~values.index.duplicated()]
                    # Warn the user, this is a crude approach and
                    # the user may wish to adjust the original file.
                    self._warn(
                        f"Duplicate sampleids found for {key_0}. Keeping only first occurrence."
                    )

            # Rows with NaNs can be dropped for faster processing,
            # since all Series share a common index, they are easily
            # pieced together at the end into a new DataFrame.
            values = values.dropna()

            # The column name in the new DataFrame will be the item's
            # alias...
            alias_n = dict_1["alias_n"]
            self._msg(f" - Alias: {alias_n}")
            # ... and the units will be the item's unit alias. Note 
            # that alias_u will be replaced by Pint's pretty format
            # if the units could be successfully parsed. The value
            # here is the value from the imported data file, which
            # will be used in case Pint fails to parse the units 
            # string.
            alias_u = dict_1["alias_u"]

            # Process the data depending on the datatype
            # For features, convert units and handle values
            # below the detection limit
            if datatype == "feature":
                # Define a unit conversion factor that will be used
                # if unit parsing fails.
                uc_factor = 1.0

                # Try to parse the input unit string with _str2pint. 
                # Returns a Pint Quantity objects qs (for the units) 
                # and mw (for the molar mass).
                u_str = dict_1["u_str"]
                qs, mw_formula, msg = self._unit_converter._str2pint(alias_n, u_str)
                self._log(msg)
                
                # Infer the unit alias from the short pretty
                # format string representation of qs. qs may be None
                # if the units were not properly identified by Pint.
                if (qs is not None):
                    alias_u = f"{qs.units:~P}"

                if self._convert_units:
                    # The user may wish to override the general
                    # target units, in which case the desired
                    # units were passed in the dict override_units.
                    if (self._target_units == "hgc"):
                        target_units = hgc_units_dict.get(alias_n)
                    elif key_0 in self._override_units:
                        target_units = self._override_units[key_0]
                    else:
                        target_units = self._target_units

                    # Call the UnitConverter object's get_uc method,
                    # which returns the target units as qt and the 
                    # unit conversion factor as uc. Both are Pint
                    # Quantity objects.
                    qt, uc = self._unit_converter.get_uc(qs, target_units, mw_formula)

                    if uc is not None:
                        # Only the magnitude attribute of uc is needed.
                        uc_factor = uc.magnitude
                        # qt's units attribute becomes the unit alias. 
                        # The formatted string with the ~P format specifier
                        # returns the units in Pint's "short pretty format".
                        alias_u = f"{qt.units:~P}"

                        # Update the log file
                        self._log(
                            f" - Converting units for {alias_n} from {dict_1['unit']} to {alias_u}."
                        )
                        self._log(f" - Unit conversion factor: {uc:~P}.")
                    else:
                        # Write a message to the log file about the failed unit
                        # conversion attempt.
                        self._log(
                            f" - Could not convert from {u_str} to {target_units} for {alias_n}."
                        )

                # Convert the measurement values using _convert_values.
                values = pd.to_numeric(values, errors="ignore")
                values = values.apply(self._convert_values, conversion_factor=uc_factor)

            # Add the values Series as a column to the new DataFrame.
            df[key_0] = values

            # Replace the original name and units by their aliases.
            column_header_dict[key_0] = alias_n
            units_header_dict[key_0] = alias_u

        # Check for any columns to be merged. Iterates over the lists in
        # _merge_columns. The first list element is the column of which the
        # NaN values must be replaced by the non-NaN values in the subsequent
        # columns in the list. Merging is skipped when the units of the source
        # column is not compatible with the target column
        if len(self._merge_columns):
            self._log("* Merging columns")
        for c_list in self._merge_columns:
            if not set(c_list).issubset(units_header_dict):
                self._log(f" - Merge failed for [{', '.join(c_list)}]")
                continue
            # The target column name is the first element of the list
            target_col = c_list[0]
            # Get the units string of the target column.
            target_col_units = units_header_dict[target_col]
            # Iterate over the source columns.
            for source_col in c_list[1:]:
                # Get the source column's units string.
                source_col_units = units_header_dict[source_col]
                # Check if target and source column units are compatible.
                if target_col_units == source_col_units:
                    # Replace the NaNs in the target column with values
                    # from the source column.
                    df[target_col].fillna(df[source_col], inplace=True)
                    # Write a message to the log file
                    self._log(
                        f" - NaN values in column {target_col} will be replaced with values from column {source_col}."
                    )
                    # Delete the source column from df...
                    df.drop(source_col, axis=1, inplace=True)
                    # ... and its name and units from the dicts
                    # that will be used to create df's columns.
                    column_header_dict.pop(source_col)
                    units_header_dict.pop(source_col)
                else:
                    # Log a message about the failed merged attempt.
                    self._log(
                        f" - Merge failed: Units of column {target_col} ({target_col_units}) incompatible with column {source_col} ({source_col_units})."
                    )

        # Write the logged messages to the log file
        self.update_log_file()
        
        # Assign a nested list to df.columns. This way the column
        # headings become a MultiIndex, so that both the column names
        # and the units appear above the columns in the DataFrame
        df.columns = [
            [column_header_dict[c] for c in df.columns],
            [units_header_dict[c] for c in df.columns],
        ]

        # Return the DataFrame
        return df
