import copy
import inspect
import os
import pandas as pd
import re
from wadi.base import WadiBaseClass
from wadi.harmonize import Harmonizer
from wadi.infotable import InfoTable
from wadi.mapping import Mapper, MapperDict
from wadi.utils import check_arg

REQUIRED_COLUMNS_S = ['SampleId', 'Features', 'Values', 'Units']
DEFAULT_C_DICT = {s: s for s in REQUIRED_COLUMNS_S}
#REQUIRED_HEADERS_W = []

VALID_FORMATS = ['stacked', 'wide', 'gef']
VALID_DATATYPES = ['sampleinfo', 'feature']
DEFAULT_DATATYPE = VALID_DATATYPES[1]

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

class Importer(WadiBaseClass):
    """
    Class for importing hydrochemical data in a variety of formats

    Examples
    --------

    TBC::
    """

    def __init__(self,
                 format='stacked', # str, immutable
                 c_dict=None,
                ):

        WadiBaseClass.__init__(self)
        self._log_fname = ''

        # Check if user provided a valid format specifier
        self.format = check_arg(format, VALID_FORMATS) 

        if (format in ['gef']):
            raise NotImplementedError(f'Format option {format} not implemented yet')

        if (format == 'stacked'):
            self.c_dict = c_dict or DEFAULT_C_DICT
            self._col_s = self.c_dict['SampleId']
            self._col_f = self.c_dict['Features']
            self._col_u = self.c_dict['Units']
            self._col_v = self.c_dict['Values']

        self.df = None
        self._infotable = InfoTable()

        try:
            os.remove("mapping_summary.xlsx")
        except OSError:
            pass

    def _create_infotable(self, units, datatypes):
        self._infotable = InfoTable() # Reset to be sure
        if (self.format == 'stacked'):
            ufus = (self.df[self._col_f] + self.df[self._col_u]).dropna().unique()
            for fu in ufus:
                idx = (self.df[self._col_f] + self.df[self._col_u] == fu)
                key = self.df[self._col_f].loc[idx].iloc[0]
                i_dict = {'name': key,
                          'unit': self.df.loc[idx, self._col_u].iloc[0], 
                          'sampleids': self.df.loc[idx, self._col_s],
                          'values': self.df.loc[idx, self._col_v],
                          'datatype': 'feature'}
                self._infotable[key] = i_dict
        elif (self.format == 'wide'):
            for i, key in enumerate(self.df.columns):
                col_name = key
                duplicate_nr = re.search('\.\d+$', col_name)
                if duplicate_nr:
                    col_name = col_name.removesuffix(duplicate_nr.group()) # Requires Python 3.9 or later
                i_dict = {'name': col_name,
                          'unit': units[i], 
                          'values': self.df[key],
                          'datatype': datatypes[i]}
                self._infotable[key] = i_dict
        
        self._log(self._infotable)

    def harmonize(self,
                  **kwargs  
                 ):
        
        valid_kwargs = inspect.signature(Harmonizer).parameters
        for kw in kwargs.copy(): # copy() is needed to avoid RuntimeError
            if kw not in valid_kwargs:
                self._warn(f"Ignoring invalid keyword argument '{kw}' in call to harmonizer.")
                kwargs.pop(kw)        
         
        h = Harmonizer(**kwargs)
        if (self.format == 'stacked'):
            rv = h.harmonize(self._infotable, self.df[self._col_s].unique())
        elif (self.format == 'wide'):
            rv = h.harmonize(self._infotable)
        
        h.update_log_file(f"{self._log_fname}.log")
    
        return rv

    def _map(self,
             s,
             **kwargs
            ):

        valid_kwargs = inspect.signature(Mapper).parameters
        for kw in kwargs.copy(): # copy() is needed to avoid RuntimeError
            if kw not in valid_kwargs:
                self._warn(f"Ignoring invalid keyword argument '{kw}' in call to mapper.")
                kwargs.pop(kw)        
         
        m = Mapper(**kwargs)

        m.match(self._infotable.keys(), 
                self._infotable.list(s),
                s,
               )
        
        m.update_log_file(f"{self._log_fname}.log")
        m.df2excel(f"{s}_mapping_results_{self._log_fname}.xlsx",
                   f"{s.capitalize()}s")
                   
        i_key = f"alias_{s[0]}"
        a_dict = m.df.set_index('header').dropna()['alias'].to_dict()
        for key, value in a_dict.items():
            self._infotable[key][i_key] = value

    def map_data(self,
                  **kwargs,
                 ):
        self._map('name', **kwargs)

    def map_units(self,
                  **kwargs,
                 ):
        if ('match_method' not in kwargs):
            kwargs['match_method'] = 'regex'
        self._map('unit', **kwargs)

    def read_data(self,
                  file_path,
                  pd_reader='read_excel',
                  **kwargs):

        # Infer log file name from file_path
        self._log_fname = os.path.splitext(file_path)[0]
        self._log("WADI log file", timestamp=True)

        pd_kwargs = copy.deepcopy(vars()['kwargs']) # deepcopy just to be sure
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
        self.df, units, datatypes = self._read_file(file_path,
                                                    pd_reader,
                                                    panes)

        #self._check_df_requirements()

        # Create the dictionary that stores views to the data read as well as
        # additional information (units, data type)
        self._create_infotable(units, datatypes)

        # Write the log string to the log file (note that mode is 'w',
        # because at this point the log file is created for the first time)
        self.update_log_file(f"{self._log_fname}.log", 'w')
    
    # @staticmethod
    # def _s_dict2df(s_dict):
    #     data = {k0: [v0.get(k1) for k1 in v0 if k1 != 'values'] for k0, v0 in s_dict.items()}
    #     return pd.DataFrame.from_dict(data, orient='index')

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
        valid_kwargs = inspect.signature(pd_reader).parameters
        
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
                # Drop any kwarg passed to read_file that is not a valid
                # keyword argument for the requested Pandas reader function
                if kwarg not in valid_kwargs:
                    pd_kwargs.pop(kwarg)
            
            # Create a verbose message for the log file
            kws = ", ".join(f"{k}={v}" for k,v in pd_kwargs.items())
            self._log(f" * pandas.{pd_reader_name}('{file_path}', {kws})")
            
            # Call the requested Pandas reader function to import the data
            df_r = pd_reader(file_path, **pd_kwargs)
                        
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

    def save_mapping_summary(self, 
                             xl_fname='mapping_summary.xlsx'):
        writer = pd.ExcelWriter(xl_fname)

        for s, m in self.mappers.items():
            if m is None:
                continue
            self._log(f"Saving {s} mapping results to {xl_fname}.")
            m.df.to_excel(writer, 
                          sheet_name=f"{s.capitalize()}s")
        
        writer.save()

        self.update_log_file(self._log_fname, 'a')

    # def _get_slice(self, slicer):
    #     """
    #     Get DataFrame values by slicing.
    #     """
    #     try:
    #         # Check if slicer argument is of type list or tuple
    #         if not isinstance(slicer, (list, tuple)):
    #             raise TypeError
            
    #         # First, convert the slicer argument into a uniform format (a 
    #         # nested list)
            
    #         # Check if slicer contains any elements, if not raise a ValueError
    #         if (len(slicer) == 0):
    #             raise ValueError
    #         else:
    #             # Check if slicer is a nested sequence by checking if its 
    #             # elements are a list or a tuple themselves
    #             if (any(isinstance(s, (list, tuple)) for s in slicer)):
    #                 # Extra check to see if all elements are lists or 
    #                 # tuples (can't have mixed types)
    #                 if not (all(isinstance(s, (list, tuple)) for s in slicer)):
    #                     raise ValueError

    #                 # Create a copy of the nested sequence
    #                 ns = slicer.copy()
    #             else:
    #                 # Convert the slicer argument to a nested sequence
    #                 ns = [slicer.copy()]

    #         # Second, loop over the elements in the nested list and make sure 
    #         # each contains two elements (one for the rows and one for the 
    #         # columns)  
    #         for i, s in enumerate(ns):
    #             if (len(s) == 1):
    #                 ns[i] = [s[0], slice(0, None, 1)]

    #             # Perform additional check to make sure all nested
    #             # elements have a valid data type
    #             for e in s:
    #                 if not isinstance(e, (int, slice)):
    #                     raise ValueError

    #     except TypeError:
    #         raise TypeError('slicer must be an iterable object like a list or a tuple')
    #     except ValueError:
    #         raise ValueError('invalid or no entry in slicer')
    #     else: 
    #         # For the case that valid (a) slice(s) has/have been provided,
    #         # loop over the slices and add the cell values to a list
    #         rv = []
    #         for s in ns:
    #             # Grab the data from the DataFrame (self.df), this either
    #             # returns an ndarray or a single value (for the case where
    #             # the requested slice is only one row and one column)
    #             vals = self.df.values[s[0], s[1]]

    #             # Check: if it is a single value then tolist() will fail
    #             if (hasattr(vals, '__iter__')):
    #                 # Convert the array to a list if not a single value
    #                 rv += vals.tolist()
    #             else:
    #                 # If just a single value, add it to the list
    #                 rv += [vals]

    #         return rv
