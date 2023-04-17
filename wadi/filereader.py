import copy
import pandas as pd

from wadi.base import WadiBaseClass
from wadi.infotable import InfoTable
from wadi.utils import check_arg, valid_kwargs

# Valid values for the 'format' kwarg
VALID_FORMATS = ["stacked", "wide", "gef"]

# Required column headers for 'stacked' format
REQUIRED_COLUMNS_S = ["SampleId", "Features", "Values", "Units"]
DEFAULT_C_DICT = {s: s for s in REQUIRED_COLUMNS_S}

# Valid values for the 'datatype' kwarg for 'wide' format
VALID_DATATYPES = ["sampleinfo", "feature"]
# Select one of the VALID_DATATYPES as the default datatype
DEFAULT_DATATYPE = VALID_DATATYPES[1]

# Default NaN values, used if user does not specify a value for the na_values
# kwarg for read_excel or read_csv
# Copied from https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
DEFAULT_NA_VALUES = [
    "",
    "-1.#IND",
    "1.#QNAN",
    "1.#IND",
    "-1.#QNAN",
    "#N/A",
    "N/A",
    #'NA', # Commented to avoid ambiguity with Na (Sodium)
    "#NA",
    "NULL",
    "NaN",
    "-NaN",
    "nan",
    "-nan",
]


class FileReader(WadiBaseClass):
    """
    WaDI class for importing data files.
    """

    def __call__(
        self,
        file_path,
        format="stacked",  # str, immutable
        c_dict=None,
        mask=None,
        lod_column=None,
        pd_reader="read_excel",  # str, immutable
        **kwargs,
    ):

        """
        This method provides an interface for the user to set the
        attributes that determine the FileReader object behavior.

        Parameters
        ----------
        file_path : str
            The file to be read.
        format : str, optional
            Specifies if the data in the file are in 'stacked' or 'wide'
            format. Permissible formats are defined in VALID_FORMATS.
            The 'gef' format is not implemented (yet). Default: 'stacked'
        c_dict : dict, optional
            Only used when the format is 'stacked'. This dictionary maps
            column names in the file to the compulsory column names defined
            in REQUIRED_COLUMNS_S. Default: DEFAULT_C_DICT
        mask : str, optional
            Name of the column that contains True/False labels. These sometimes
            occur in stacked data files to indicate if a reported value is 
            below or above the detection limit. If a valid column name is 
            specified, the values marked with `False` are filtered out from 
            the converted DataFrame. Only used when the format is 'stacked'.
            Default: None
        lod_column : str, optional
            Name of the column that contains information about whether the 
            reported measurement value is below or above the limit of 
            detection (LOD). If a valid column name is specified, the
            symbol is prefixed to the measurement value.
            Only used when the format is 'stacked'. Default: None
        pd_reader : str, optional
            Name of the Pandas function to read the file. Must be a valid
            function name. While all functions implemented in Pandas could
            be used in principle, the design of WaDI has not been tested
            for functions other than read_excel and read_csv. Default:
            'read_excel'.
        **kwargs: dict, optionalt
            Dictionary with kwargs for the 'pdt_retader' function. The
            kwargs can be a mix of WaDI specific keywords and valid
            keyword arguments for the 'pd_reader' function.
        """

        self._file_path = file_path
        self._pd_reader = pd_reader

        # Check if user provided a valid format specifier
        format = check_arg(format, VALID_FORMATS)
        # Raise error if the format is not yet implemented
        if format in ["gef"]:
            raise NotImplementedError(f"Format option {format} not implemented yet")
        self._format = format  # for use in read_data

        # Use c_dict to look up the names of the columns with the compulsory
        # names for stacked data.
        self._c_dict = c_dict or DEFAULT_C_DICT

        self._mask = mask
        self._lod_column = lod_column

        self._kwargs = copy.deepcopy(vars()["kwargs"])  # deepcopy just to be sure

    def _execute(self):
        """
        This method imports the data from a file format readable by
        Pandas. Before calling the Pandas reader function, it checks
        the kwargs specified by the user when the class object was 
        initialized. 
        """

        # Use the defaults for na_values if the user did not specify their own
        if "na_values" not in self._kwargs:
            self._kwargs["na_values"] = DEFAULT_NA_VALUES

        # Check if the user specified the 'blocks' kwarg, which
        # means that multiple dataframes must be read and joined
        if "blocks" not in self._kwargs:
            # If blocks is not in kwargs then store the kwargs in a
            # one-element list
            blocks = [self._kwargs]
        else:
            # If blocks is in kwargs then check if it's a sequence
            # before continuing
            blocks = self._kwargs["blocks"]
            if not isinstance(blocks, (list, tuple)):
                raise ValueError("Argument 'blocks' must be a list or a tuple")

        # Loop over the blocks to perform some checks for inconsistent kwargs
        for kwargs in blocks:
            # For stacked data the units and datatype are inferred
            # from c_dict when the InfoTable is created
            if (self._format == "stacked") & ("units_row" in kwargs):
                kwargs.pop("units_row")
                self._warn(
                    "Argument 'units_row' can not be used in combination with stacked format and will be ignored."
                )
            if (self._format == "stacked") & ("datatype" in kwargs):
                kwargs.pop("datatype")
                self._warn("Argument 'datatype' is ignored when format is 'stacked'.")

        # Call _read_file to import the (blocks of) data into a single 
        # DataFrame.
        df, units, datatypes = self._read_file(self._file_path, self._pd_reader, blocks)

        if self._format == "stacked":
            # Use the values in the column with name 'mask' to
            # hide the values labelled as False from view.
            if self._mask is not None:
                df = df.loc[df[self._mask]]

            if self._lod_column is not None:
                df[self._c_dict["Values"]] = df[self._lod_column] + df[self._c_dict["Values"]].astype(str)

        # Create the InfoTable dictionary that stores views to the
        # imported data as well as additional information (units,
        # data type)
        infotable = InfoTable(
            df,
            self._format,
            self._c_dict,
            units,
            datatypes,
        )

        # Write the __str__ representation of the InfoTable to the
        # log file.
        self._log(infotable)

        # Write the log string to the log file
        self.update_log_file()

        return df, infotable

    def _read_file(
        self,
        file_path,
        pd_reader_name,
        blocks,
    ):
        """
        This method calls the specified Pandas reader function to
        perform the actual data import from file_path. It imports
        a DataFrame with the data as well as lists with the
        measurement units and the datatypes (the latter two are 
        not used when the data are in 'stacked' format).

        Parameters
        ----------
        file_path : str
            The file to be read.
        pd_reader_name : str
            Name of the Pandas function to read the file.
        blocks : list
            List with keyword arguments that specify (i) the number
            of the row with the units, (ii) the datatpe and (iii) any
            kwargs for the pd_reader function. Note that (i) and (ii)
            do not apply to 'stacked' data.

        Returns
        ----------
        df : DataFrame
            Pandas DataFrame with the imported data
        units : list
            List with the units for each column read.
        datatypes: list
            List with the datatypes for each column read.

        Raises
        ------
        ValueError
            When index_col is a kwarg in one of the blocks.

        Notes
        ----------
        The return values units and datatypes are used when the
        InfoTable is created for 'wide' format data. They are not
        used when the data format is 'stacked'.
        """

        # Inform user with message on screen that reading has started (may
        # take a long time for large files)
        self._msg(f"Reading data", header=True)
        self._log(f"* Reading file {file_path} with the following Pandas call(s):")

        # Get reference to pandas reader function and determine its valid
        # keyword arguments
        pd_reader = getattr(pd, pd_reader_name)
        if not (pd_reader.__name__ in ["read_excel", "read_csv"]):
            self._warn(
                f"WaDI has not been designed to work with reader {pd_reader}. Proceed with caution."
            )

        # Start with an empty DataFrame...
        df = pd.DataFrame()
        # ... and empty lists for units and datatype.
        units = []
        datatypes = []
        # Loop over the sets of kwargs in the block(s).
        for pd_kwargs in blocks:
            # Set values for unit_row and datatype, these may be
            # overridden if the user specified a kwarg for any
            # of them.
            units_row = -1
            datatype = DEFAULT_DATATYPE
            # Loop over the user-specified kwargs.
            for kwarg in pd_kwargs.copy():  # copy() is needed to avoid a RuntimeError
                if kwarg == "units_row":
                    units_row = pd_kwargs[kwarg]
                # Check if a valid datatype was passed and convert to
                # one of the standard formats contained in VALID_DATAYPES.
                if kwarg == "datatype":
                    datatype = check_arg(pd_kwargs[kwarg], VALID_DATATYPES)
                # Index columns are not supported to avoid duplicate.
                # index errors etc.
                if kwarg == "index_col":
                    raise ValueError("Argument 'index_col' not allowed in WADI")

            # Create a verbose message for the log file.
            kws = ", ".join(f"{k}={v}" for k, v in pd_kwargs.items())
            self._log(f" - pandas.{pd_reader_name}('{file_path}', {kws})")

            # Call the requested Pandas reader function to import the data.
            df_r = pd_reader(file_path, **valid_kwargs(pd_reader, **pd_kwargs))

            # Use the pd.concat function to join the return values from the
            # pandas reader function (i.e. the DataFrames read from the file).
            df = pd.concat([df, df_r], axis=1)

            # Read the units if the user specified a valid row number, else...
            if units_row > -1:
                units += self._read_single_row_as_list(
                    file_path, pd_reader, pd_kwargs, units_row
                )
            # ... create a list of empty strings with the same length as the
            # number of columns read
            else:
                units += [""] * df_r.shape[1]

            # Make sure that the datatype for this block is copied as many
            # times as there are columns in the DataFrame that was read
            datatypes += [datatype] * df_r.shape[1]

        return df, units, datatypes

    def _read_single_row_as_list(
        self,
        file_path,
        pd_reader,
        pd_kwargs,
        row_number,
    ):
        """
        This method calls the specified Pandas reader function to
        read a single row from file_path.

        Parameters
        ----------
        file_path : str
            The file to be read.
        pd_reader_name : str
            Name of the Pandas function to read the file.
        pd_kwargs : dict
            Keyword arguments for the pd_reader function.
        row_number : int
            The (zero-based) number of the row to read.

        Returns
        ----------
        result : list
            List with the values read.
        """
        # Assemble the appropriate kwargs to read a single row,
        # this may include the user-specified keywords sheet_name
        # and usecols.
        sr_kwargs = {} # sr is shorthand for single row
        if "sheet_name" in pd_kwargs:
            sr_kwargs["sheet_name"] = pd_kwargs["sheet_name"]
        if "usecols" in pd_kwargs:
            sr_kwargs["usecols"] = pd_kwargs["usecols"]
        sr_kwargs["header"] = None
        # Note that header=None does not seem to work in conjuction
        # with skiprows! Therefore, read the data up until row 
        # row_number + 1, the units will be in the last row of the
        # dataframe returned by the reader.
        sr_kwargs["nrows"] = row_number + 1

        # Read the data, replace any NaNs with empty strings and 
        # return the last row of the DataFrame as a list
        return pd_reader(file_path, **sr_kwargs).fillna("").values[-1].tolist()
