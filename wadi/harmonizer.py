import pandas as pd
import re

from wadi.base import WadiBaseClass
from wadi.utils import check_if_nested_list
from wadi.unitconverter import UnitConverter

# Suppress performance warnings for that occur during harmonize because
# DataFrame can contain lots of NaNs
import warnings

warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

BD_FACTORS = {"delete": 0, "halve": 0.5}
# VALID_DUPLICATE_COLS_OPTIONS = ['keep_first', 'keep_all']


class Harmonizer(WadiBaseClass):
    """
    WaDI class for transforming the data to a harmonized format.
    """

    def __init__(
        self,
    ):
        """
        Class initialization method. Calls the ancestor init method
        to set the converter attribute.
        """

        super().__init__()

        self.convert_units = False
        self.target_units = "mg/l"
        self.override_units = {}
        self.drop_columns = []
        self.merge_columns = []

        # self._bd_factor = BD_FACTORS[check_arg(convert_bds, BD_FACTORS.keys())]
        self._bd_RE = rf"(^\s*<\s*)"
        self.decimal_str = ","

    # Defining __call__ method
    def __call__(
        self,
        convert_units=False,
        target_units="mg/l",  # str, immutable
        override_units=None,
        drop_columns=None,
        merge_columns=None,
        lt_symbol="<",  # str, immutable
        decimal_str=",",  # str, immutable
    ):
        """
        This method transforms the original data and places the
        result in a new DataFrame with the features as columns.

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
        lt_symbol : str, optional
            A string that represents the symbol that is used for
            measurement values below the detection limit. Default:
            '<'.
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
        self.convert_units = convert_units
        self.target_units = target_units
        self.override_units = override_units or {}
        self.drop_columns = drop_columns or []
        self.merge_columns = merge_columns or []
        self.decimal_str = decimal_str
        check_if_nested_list(self.merge_columns)

        self._bd_RE = rf"(^\s*{lt_symbol}\s*)"

        # return self.harmonize()

    def _convert_values(self, v, conversion_factor):
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
            rv = float(substrings[2].replace(self.decimal_str, ".")) * conversion_factor
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

    def harmonize(self, 
        infotable,
    ):
        """
        This function performs the harmonize operation, that is it
        convert the units to the target units desired by the user,
        it deletes any undesired columns and merges columns,
        depending on the kwargs specified by the user.

        Returns
        ----------
        df : DataFrame
            DataFrame with the transformed data.
        """
        self._log("Harmonizing", header=True)

        # Initialize the DataFrame to be created. Uses the target_index
        # by the InfoTable that ensures that the sampleids for
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
        # for consistency.
        for key_0, dict_1 in infotable.items():

            self._log(f"Processing {key_0}.")

            # Do not process items that the user has indicated
            # should be skipped.
            if key_0 in self.drop_columns:
                self._log(f" - Dropping column: {dict_1['name']}")
                continue

            # The actual data are Pandas Series that are a view
            # to the DataFrame created in read_data().
            values = dict_1["values"]

            # For wide-format data, the index is a default RangeIndex
            # but for stacked-format data a new index must be created
            # to be able to match the feature data to the samples.
            # Stacked data are identifiable from the InfoTable's
            # dict_1 entry because, unlike wide data, it will have a
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
                # have been used for a single parameter without
                # properly documenting this in the original file.
                # In that case, the duplicate values are simply
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
            values = pd.to_numeric(values.dropna(), errors="ignore")

            # Get the datatype ('sampleinfo' or 'feature')
            datatype = dict_1["datatype"]

            # The column name in the new DataFrame will be the item's
            # alias...
            alias_n = dict_1["alias_n"]
            # ... and the units will be the item's unit alias.
            alias_u = dict_1["alias_u"]

            u_str = dict_1["u_str"]
 
            # Try to parse the unit string with Pint. Returns the
            # Pint Quantity objects q (for the units) and mw (for
            # the molar mass) to be used for unit conversion.
            unit_converter = UnitConverter()
            q, mw, msg = unit_converter._str2pint(alias_n, u_str)
            self._log(msg)

            # Process the data depending on the datatype
            # For features, convert units and handle values
            # below the detection limit
            if self.convert_units and (datatype == "feature"):
                # Define a unit conversion factor that will be used
                # if the unit parsing code below does not yield a
                # valid conversion factor (e.g., in case unit parsing
                # by Pint fails).
                uc_factor = 1.0
 
                # q may be None if the units were not properly
                # identified by Pint
                if q is not None:
                    # The user may wish to override the general
                    # target units, in which case the desired
                    # units were passed in the dict override_units.
                    if key_0 in self.override_units:
                        target_units = self.override_units[key_0]
                    else:
                        target_units = self.target_units

                    uc = unit_converter.get_uc(q, target_units, mw)

                    if uc is not None:
                        # uc is a Quantity object, for converting the
                        # measurements, only the magnitude attribute
                        # is needed...
                        uc_factor = uc.magnitude
                        # ... and the units attribute becomes the unit
                        # alias. The formatted string with the ~P 
                        # format specifier returns the units in 
                        # Pint's "short pretty format".
                        alias_u = f"{uc.units:~P}"
                        self._log(f" - Converting units for {key_0} from {dict_1['unit']} to {alias_u}.")
                        self._log(f" - Unit conversion factor: {uc:~P}")
                    else:
                        self._log(f" - Could not convert from {q.units} to {target_units} for {key_0}.")
                        # Infer the unit alias from the short pretty
                        # format string representation of q (an
                        # exception was caught so uc does not exist).
                        alias_u = f"{q.units:~P}"

                # Convert the measurement values using _convert_values.
                values = values.apply(self._convert_values, conversion_factor=uc_factor)

            # Add the values Series as a column to the new DataFrame
            df[key_0] = values

            # Replace the original name and units by their aliases
            column_header_dict[key_0] = alias_n
            units_header_dict[key_0] = alias_u

        # Check for any columns to be merged. Iterates through the lists in
        # merge_columns. The first list element is the column of which the
        # NaN values must be replaced by the non-NaN values in the subsequent
        # columns in the list.
        for l in self.merge_columns:
            self._log(
                f" - NaN values in {l[0]} will be replaced with values from {', '.join(c for c in l[1:])}"
            )
            for c in l[1:]:
                df[l[0]].fillna(df[c], inplace=True)
                column_header_dict.pop(c)
                units_header_dict.pop(c)
            df.drop(l[1:], axis=1, inplace=True)

        # Assign a nested list to df.columns. This way the column
        # headings become a MultiIndex, so that both the column names
        # and the units appear above the columns in the DataFrame
        df.columns = [
            [column_header_dict[c] for c in df.columns],
            [units_header_dict[c] for c in df.columns],
        ]

        # Write the logged messages to the log file
        self.update_log_file()

        # Return the DataFrame
        return df
