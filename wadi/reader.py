import copy
import pandas as pd

from wadi.base import WadiChildClass
from wadi.infotable import InfoTable
from wadi.utils import check_arg, valid_kwargs

# Valid values for the 'format' kwarg
VALID_FORMATS = ['stacked', 'wide', 'gef']

# Required column headers for 'stacked' format
REQUIRED_COLUMNS_S = ['SampleId', 'Features', 'Values', 'Units']
DEFAULT_C_DICT = {s: s for s in REQUIRED_COLUMNS_S}

# Valid values for the 'datatype' kwarg for 'wide' format
VALID_DATATYPES = ['sampleinfo', 'feature']
# Select one of the VALID_DATATYPES as the default datatype
DEFAULT_DATATYPE = VALID_DATATYPES[1]

# Default NaN values, used if user does not specify a value for the na_values
# kwarg for read_excel or read_csv
# Copied from https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
DEFAULT_NA_VALUES = ['', 
                    '-1.#IND', 
                    '1.#QNAN', 
                    '1.#IND', 
                    '-1.#QNAN', 
                    '#N/A',
                    'N/A', 
                    #'NA', # Commented to avoid ambiguity with Na (Sodium) 
                    '#NA', 
                    'NULL', 
                    'NaN', 
                    '-NaN', 
                    'nan', 
                    '-nan']

class Reader(WadiChildClass):
    """
    Class for reading files for WADI.

    Examples
    --------

    TBC::
    """

    def __init__(self,
                 converter,
                ):
        """
        """

        super().__init__(converter)

    def __call__(self,
                 file_path,
                 format='stacked', # str, immutable
                 c_dict=None,
                 mask=None, # Only for stacked data, column name with T/F data
                 pd_reader='read_excel',
                 **kwargs, # kwargs for the pandas reader function
                ):

        """
        Parameters
        ----------
        format : str, default 'stacked'.
            Specifies if the data in the file are in 'stacked' or 'wide' 
            format. Permissible formats are defined in VALID_FORMATS. 
            The 'gef' format is not implemented (yet).
        c_dict : dict, default is DEFAULT_C_DICT
            Only used when the format is 'stacked'. This dictionary maps
            column names in the file to the compulsory column names defined
            in REQUIRED_COLUMNS_S.
        """

        self.file_path = file_path
        self.pd_reader = pd_reader

        # Check if user provided a valid format specifier
        format = check_arg(format, VALID_FORMATS) 
        # Raise error if the format is not yet implemented
        if (format in ['gef']):
            raise NotImplementedError(f'Format option {format} not implemented yet')
        self.format = format # for use in read_data

        # Use c_dict to look up the names of the columns with the compulsory
        # names for stacked data.
        c_dict = c_dict or DEFAULT_C_DICT

        df, units, datatypes = self._read_data(**kwargs)
        if (mask is not None):
            df = df.loc[df[mask]]

        # Create the dictionary that stores views to the data read as well as
        # additional information (units, data type)
        self.converter.df = df
        self.converter._infotable = InfoTable(df, format, c_dict, units, datatypes)
        self._log(self.converter._infotable)

    def _read_data(self,
                  **kwargs):

        # Before calling the Pandas reader function, do some error 
        # checking/tweaking of the kwargs
        pd_kwargs = copy.deepcopy(vars()['kwargs']) # deepcopy just to be sure

        # Use the defaults for na_values if the user did not specify their own 
        if ('na_values' not in pd_kwargs):
            pd_kwargs['na_values'] = DEFAULT_NA_VALUES
        
        # Check if the user specified the 'panes' kwarg, which
        # means that multiple dataframes must be read and joined
        if ('panes' not in kwargs):
            # If panes is not in kwargs then store the kwargs in a 
            # one-element list
            panes = [kwargs]
        else:
            # If panes is in kwargs then check if it's a sequence
            # before continuing
            panes = kwargs['panes']
            if not isinstance(panes, (list, tuple)):
                raise ValueError("Argument 'panes' must be a list or a tuple")

        # Loop over the panes
        for pd_kwargs in panes:
            # Perform some checks for inconsistent kwargs
            if ((self.format == 'stacked') & ('units_row' in pd_kwargs)):
                pd_kwargs.pop('units_row')
                self._warn("Argument 'units_row' can not be used in combination with wide format and will be ignored.")
            if ((self.format == 'stacked') & ('datatype' in pd_kwargs)):
                pd_kwargs.pop('datatype')
                self._warn("Argument 'datatype' is ignored when format is 'stacked'.")
        
        # Call read file to import the data into a single DataFrame
        df, units, datatypes = self._read_file(self.file_path,
                                               self.pd_reader,
                                               panes)

        # Write the log string to the log file (note that mode is 'w',
        # because at this point the log file is created for the first time)
        self.update_log_file()

        return df, units, datatypes

    def _read_file(self,
                  file_path,
                  pd_reader_name,   
                  panes):

        # Inform user with message on screen that reading has started (may
        # take a long time for large files)
        self._msg(f"Reading ...")
        
        # Get reference to pandas reader function and determine its valid
        # keyword arguments
        pd_reader = getattr(pd, pd_reader_name)
        
        # Start with an empty DataFrame and empty lists for units and datatype
        df = pd.DataFrame()
        units = []
        datatypes = []
        # Loop over the sets of kwargs
        for pd_kwargs in panes:
            units_row = -1
            datatype = DEFAULT_DATATYPE
            for kwarg in pd_kwargs.copy(): # copy() is needed to avoid RuntimeError
                if (kwarg == 'units_row'):
                    units_row = pd_kwargs[kwarg]
                if (kwarg == 'datatype'):
                    datatype = check_arg(pd_kwargs[kwarg], 
                                         VALID_DATATYPES)
                if (kwarg == 'index_col'):
                    raise ValueError("Argument 'index_col' not allowed in WADI")
            
            # Create a verbose message for the log file
            kws = ", ".join(f"{k}={v}" for k,v in pd_kwargs.items())
            self._log(f" * pandas.{pd_reader_name}('{file_path}', {kws})")
            
            # Call the requested Pandas reader function to import the data
            df_r = pd_reader(file_path, 
                             **valid_kwargs(pd_reader, **pd_kwargs))
                        
            # Use the pd.concat function to join the return values from the 
            # pandas reader function (i.e. the DataFrames read from the file)
            df = pd.concat([df, df_r], axis=1)

            # Read the units if the user specified a valid row number, else...
            if units_row > -1:
                units += self._read_single_row_as_list(file_path, pd_reader, pd_kwargs, units_row)
            # ... create a list of empty strings with the same length as the
            # number of columns read
            else:
                units += ([''] * df_r.shape[1])
            
            # Make sure that the datatype for this pane is copied as many 
            # times as there are columns in the DataFrame that was read
            datatypes += ([datatype] * df_r.shape[1])

        return df, units, datatypes

    def _read_single_row_as_list(self, file_path, pd_reader, pd_kwargs, units_row):
        units_kwargs = {}
        if (pd_reader.__name__ in ['read_excel', 'read_csv']):
            # Note that header=None does not seem to work in conjuction with skiprows!
            # Therefore, read the data up until row units_row + 1, the units will be 
            # in the last row of the dataframe returned by the reader
            units_kwargs['header'] = None 
            units_kwargs['nrows'] = units_row + 1
        else:
            self._warn(f"argument 'units_row' may not work as expected with reader {pd_reader}")
        if ('sheet_name' in pd_kwargs):
            units_kwargs['sheet_name'] = pd_kwargs['sheet_name']
        if ('usecols' in pd_kwargs):
            units_kwargs['usecols'] = pd_kwargs['usecols']

        return pd_reader(file_path, **units_kwargs).fillna('').values[-1].tolist()