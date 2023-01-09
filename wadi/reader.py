import copy
import pandas as pd

from wadi.base import WadiChildClass
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


class Reader(WadiChildClass):
    """
    WaDI class for reading files.
    """

    def __init__(
        self,
        converter,
    ):
        """
        Class initialization method. Calls the ancestor init method
        to set the converter attribute.
        """

        super().__init__(converter)

    def __call__(
        self,
        file_path,
        format="stacked",  # str, immutable
        c_dict=None,
        mask=None,  # Only for stacked data, column name with T/F data
        pd_reader="read_excel",
        **kwargs,  # kwargs for the pandas reader function
    ):

        """
        Parameters
        ----------
        file_path : str
            The file to be read.
        format : str, optional
            Specifies if the data in the file are in 'stacked' or 'wide'
            format. Permissible formats are defined in VALID_FORMATS.
            The 'gef' format is not implemented (yet). Default is 'stacked'
        c_dict : dict
            Only used when the format is 'stacked'. This dictionary maps
            column names in the file to the compulsory column names defined
            in REQUIRED_COLUMNS_S. Default is DEFAULT_C_DICT
        mask : str
            Name of the column that contains True/False labels, sometimes
            used to indicate if a reported value is below or above the
            detection limit. Only used when the format is 'stacked'.
        pd_reader : str
            Name of the Pandas function to read the file. Must be a valid
            function name. While all functions implemented in Pandas could
            be used in principle, the design of WaDI has not been tested
            for functions other than read_excel and read_csv. Default is
            'read_excel'.
        """

        self.file_path = file_path
        self.pd_reader = pd_reader

        # Check if user provided a valid format specifier
        format = check_arg(format, VALID_FORMATS)
        # Raise error if the format is not yet implemented
        if format in ["gef"]:
            raise NotImplementedError(f"Format option {format} not implemented yet")
        self.format = format  # for use in read_data

        # Use c_dict to look up the names of the columns with the compulsory
        # names for stacked data.
        c_dict = c_dict or DEFAULT_C_DICT

        # Read the file and return a DataFrame with the data,
        # and lists with the (concentration) units and the
        # datatype. The keyword arguments can contain any valid
        # kwarg that is accepted by the pd_reader function.
        # They are passed verbatim to the _read_data function
        # and are checked for consistency there.
        df, units, datatypes = self._read_data(**kwargs)

        # Use the values in the column with name 'mask' to
        # hide the values below the detection limit from view.
        # Still to implement: Convert them to a lower than format.
        if mask is not None:
            df = df.loc[df[mask]]

        # Store the data that were read in the Converters DataFrame
        # attribute
        self.converter.df = df

        # Create the InfoTable dictionary that stores views to the data
        # read as well as additional information (units, data type)
        self.converter._infotable = InfoTable(df, format, c_dict, units, datatypes)
        # Write the InfoTable to the log file (based on the __str__
        # function in InfoTable)
        self._log(self.converter._infotable)

    def _read_data(self, **kwargs):
        """
        Function that imports the data from a file format readable by
        Pandas. The **kwargs can contain any of the keyword arguments
        passed to the __call__ function and can be a mix of WaDI
        specific keywords and valid keyword arguments for the Pandas
        reader function (pd_read).
        """

        # Before calling the Pandas reader function, do some error
        # checking/tweaking of the kwargs
        pd_kwargs = copy.deepcopy(vars()["kwargs"])  # deepcopy just to be sure

        # Use the defaults for na_values if the user did not specify their own
        if "na_values" not in pd_kwargs:
            pd_kwargs["na_values"] = DEFAULT_NA_VALUES

        # Check if the user specified the 'blocks' kwarg, which
        # means that multiple dataframes must be read and joined
        if "blocks" not in kwargs:
            # If blocks is not in kwargs then store the kwargs in a
            # one-element list
            blocks = [kwargs]
        else:
            # If blocks is in kwargs then check if it's a sequence
            # before continuing
            blocks = kwargs["blocks"]
            if not isinstance(blocks, (list, tuple)):
                raise ValueError("Argument 'blocks' must be a list or a tuple")

        # Loop over the blocks to perform some checks for inconsistent kwargs
        for pd_kwargs in blocks:
            # For stacked data the units and datatype are inferred
            # from c_dict when the InfoTable is created
            if (self.format == "stacked") & ("units_row" in pd_kwargs):
                pd_kwargs.pop("units_row")
                self._warn(
                    "Argument 'units_row' can not be used in combination with stacked format and will be ignored."
                )
            if (self.format == "stacked") & ("datatype" in pd_kwargs):
                pd_kwargs.pop("datatype")
                self._warn("Argument 'datatype' is ignored when format is 'stacked'.")

        # Call _read_file to import the data into a single DataFrame
        df, units, datatypes = self._read_file(self.file_path, self.pd_reader, blocks)

        # Write the log string to the log file
        self.update_log_file()

        return df, units, datatypes

    def _read_file(
        self,
        file_path,
        pd_reader_name,
        blocks,
    ):
        """
        Function that calls the specified Pandas reader function to
        perform the actual data import from file_path.

        Parameters
        ----------
        file_path : str
            The file to be read.
        pd_reader_name : str
            Name of the Pandas function to read the file.
        blocks : list
            List with keyword arguments that specify (i) the number
            of the row with the units, (ii) the datatpe and (iii) any
            kwargs for the pd_reader function.

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
        InfoTable is created for wide-format data. They are not
        used when the data format is stacked.
        """

        # Inform user with message on screen that reading has started (may
        # take a long time for large files)
        self._msg(f"Reading data", header=True)
        self._log(f"* Reading file {file_path} with the following Pandas call(s):")

        # Get reference to pandas reader function and determine its valid
        # keyword arguments
        pd_reader = getattr(pd, pd_reader_name)

        # Start with an empty DataFrame and empty lists for units and datatype
        df = pd.DataFrame()
        units = []
        datatypes = []
        # Loop over the sets of kwargs in the pane(s)
        for pd_kwargs in blocks:
            # Set values for unit_row and datatype, these may be 
            # overridden if the user specified a kwarg for any 
            # of them
            units_row = -1
            datatype = DEFAULT_DATATYPE
            # Loop over the user-specified kwargs
            for kwarg in pd_kwargs.copy():  # copy() is needed to avoid RuntimeError
                if kwarg == "units_row":
                    units_row = pd_kwargs[kwarg]
                    if not (pd_reader.__name__ in ["read_excel", "read_csv"]):
                        self._warn(
                            f"Argument {kwarg} may not work as expected with reader {pd_reader}."
                        )
                # Check if a valid datatype was passed and convert to
                # one of the standard formats contained in VALID_DATAYPES
                if kwarg == "datatype":
                    datatype = check_arg(pd_kwargs[kwarg], VALID_DATATYPES)
                # Index columns are not supported to avoid duplicate
                # index errors etc.
                if kwarg == "index_col":
                    raise ValueError("Argument 'index_col' not allowed in WADI")

            # Create a verbose message for the log file
            kws = ", ".join(f"{k}={v}" for k, v in pd_kwargs.items())
            self._log(f" - pandas.{pd_reader_name}('{file_path}', {kws})")

            # Call the requested Pandas reader function to import the data
            df_r = pd_reader(file_path, **valid_kwargs(pd_reader, **pd_kwargs))

            # Use the pd.concat function to join the return values from the
            # pandas reader function (i.e. the DataFrames read from the file)
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

            # Make sure that the datatype for this pane is copied as many
            # times as there are columns in the DataFrame that was read
            datatypes += [datatype] * df_r.shape[1]

        return df, units, datatypes

    def _read_single_row_as_list(
        self,
        file_path,
        pd_reader,
        pd_kwargs,
        units_row,
    ):
        """
        Function that calls the specified Pandas reader function to
        read a single line from file_path.

        Parameters
        ----------
        file_path : str
            The file to be read.
        pd_reader_name : str
            Name of the Pandas function to read the file.
        pd_kwargs : dict
            Keyword arguments for the pd_reader function.
        units_row : int
            Number of the row with the units.

        Returns
        ----------
        result : list
            List with the values read.
        """
        # Assemble the appropriate kwargs to read a single line,
        # this may include the user-specified keywords sheet_name
        # and usecols.
        units_kwargs = {}
        units_kwargs["header"] = None
        # Note that header=None does not seem to work in conjuction with skiprows!
        # Therefore, read the data up until row units_row + 1, the units will be
        # in the last row of the dataframe returned by the reader
        units_kwargs["nrows"] = units_row + 1
        if "sheet_name" in pd_kwargs:
            units_kwargs["sheet_name"] = pd_kwargs["sheet_name"]
        if "usecols" in pd_kwargs:
            units_kwargs["usecols"] = pd_kwargs["usecols"]

        # Read the data, fill the NaNs and return the last row of
        # the DataFrame as a list
        return pd_reader(file_path, **units_kwargs).fillna("").values[-1].tolist()
