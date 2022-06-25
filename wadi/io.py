# from argparse import ArgumentError
# from multiprocessing.sharedctypes import RawValue, Value
# from unittest.mock import DEFAULT
# from wsgiref import headers
import copy
import inspect
import numpy as np
import pandas as pd
import re
from wadi.harmonize import Harmonizer
from wadi.utils import check_arg
import warnings

REQUIRED_COLUMNS_S = ['Feature', 'Value', 'Unit'] #, 'SampleId']
DEFAULT_COLUMN_MAP_S = {s: s for s in REQUIRED_COLUMNS_S}
#REQUIRED_HEADERS_W = []

VALID_FORMATS = ['stacked', 'wide', 'gef']
VALID_DATATYPES = ['header', 'feature']
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

class Importer(object):
    """
    Class for importing hydrochemical data in a variety of formats

    Examples
    --------

    TBC::
    """

    def __init__(self,
                 format='stacked', # str, immutable
                 header_map=None,   
                 unit_map=None, 
                 harmonizer=None,       
                 ):
        
        self.df = None
        self.header_map = header_map
        self.unit_map = unit_map
        if (harmonizer):
            self.harmonizer = harmonizer
        else:
            self.harmonizer = Harmonizer()

        self.s_dict = {}

        # Check if user provided a valid format specifier and header_map
        self.format = check_arg(format, VALID_FORMATS) 
        print(self.format)   
        if (format in ['gef']):
            raise NotImplementedError(f'Format option {format} not implemented yet')
        self.header_map = self._check_header_map(header_map)

    def _check_df_requirements(self):
        """
        """
                    
        self.df.rename(columns={v: k for k, v in self.header_map.items()}, inplace=True)

        if (self.format == 'stacked'):
            missing_headers = [s for s in REQUIRED_COLUMNS_S if s.lower() not in self.df.columns.str.lower()]
            if len(missing_headers):
                raise ValueError(f'Required header(s) {missing_headers} missing from DataFrame')
        elif (self.format == 'wide'):
            pass
        else:
            raise ValueError(f'Format specifier {self.format} not recognized')

    def _check_header_map(self, header_map):
        
        # if not isinstance(header_map, dict):
        #     raise TypeError('header_map must be of type dictionary')

        # for key, value in header_map.items():
        #     if not isinstance(key, str):
        #         raise TypeError('header_map key {key} must be of type str')
        #     if not isinstance(value, str):
        #         raise TypeError('header_map value {value} must be of type str')
        
        # if self.format == 'stacked':
        #     default_headers = DEFAULT_HEADER_MAP_S
        # elif self.format == 'wide':
        #     default_headers = DEFAULT_HEADER_MAP_S
        # else:
        #     default_headers = []

        # for key, value in default_headers.items():
        #     if key not in header_map:
        #         header_map[key] = value

        return header_map

    def _create_s_dict(self, units, datatypes):
        self.s_dict = {} # Reset to be sure
        if (self.format == 'stacked'):
            ufus = (self.df['Feature'] + self.df['Unit']).dropna().unique()
            for fu in ufus:
                idx = (self.df['Feature'] + self.df['Unit'] == fu)
                key = self.df['Feature'].loc[idx].iloc[0]
                value = {'header': key,
                         'unit': self.df['Unit'].loc[idx].iloc[0], 
                         'values': self.df['Value'].loc[idx],
                         'type': 'feature'}
                self.s_dict[key] = value
        elif (self.format == 'wide'):
            for i, key in enumerate(self.df.columns):
                col_name = key
                duplicate_nr = re.search('\.\d+$', col_name)
                if duplicate_nr:
                    col_name = col_name.removesuffix(duplicate_nr.group())
                value = {'header': col_name,
                         'unit': units[i], 
                         'values': self.df[key],
                         'type': datatypes[i]}
                self.s_dict[key] = value

    def harmonize(self,
                 ):
        self.harmonizer.harmonize(self.s_dict)

    def map_data(self,
                 save_summary=True,
                 xl_fname='mapping_summary.xlsx'
                ):
        
        writer = None
        if save_summary:
            writer = pd.ExcelWriter(xl_fname)
        
        if self.header_map:
            h_dict= self.header_map.match(self.s_dict, 'header', writer)
            for key in self.s_dict.copy():
                self.s_dict[key]['header'] = h_dict[key]

        if self.unit_map:
            u_dict = self.unit_map.match(self.s_dict, 'unit', writer)
            for key in self.s_dict.copy():
                self.s_dict[key]['unit'] = u_dict[key]

        if writer:
            writer.save()

    def read_data(self,
                  file_path,
                  pd_reader='read_excel',
                  **kwargs):

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

        for pd_kwargs in panes:
            if ((self.format == 'stacked') & ('units_row' in pd_kwargs)):
                pd_kwargs.pop('units_row')
                warnings.warn("Argument 'units_row' can not be used in combination with wide format and will be ignored.")
            if ((self.format == 'stacked') & ('datatype' in pd_kwargs)):
                pd_kwargs.pop('datatype')
                warnings.warn("Argument 'datatype' is ignored when format is 'stacked'.")
        
        self.df, units, datatypes = self._read_file(file_path,
                                                    pd_reader,
                                                    panes)

        #self._check_df_requirements()
        self._create_s_dict(units, datatypes)
    
    # @staticmethod
    # def _s_dict2df(s_dict):
    #     data = {k0: [v0.get(k1) for k1 in v0 if k1 != 'values'] for k0, v0 in s_dict.items()}
    #     return pd.DataFrame.from_dict(data, orient='index')

    def _read_file(self,
                  file_path,
                  pd_reader_name,   
                  panes):
        
        # Get reference to pandas reader function
        pd_reader = getattr(pd, pd_reader_name)
        # Determine its valid keyword arguments
        valid_kwargs = inspect.signature(pd_reader).parameters
        
        # Start with an empty DataFrame
        df = pd.DataFrame()
        units = []
        datatypes = []
        # Loop over the sets of kwargs
        for pd_kwargs in panes:
            # Drop any kwarg passed to read_file that is not a valid
            # keyword argument for the reader function in pandas
            units_row = -1
            datatype = DEFAULT_DATATYPE
            column_map = {}
            for kwarg in pd_kwargs.copy(): # copy() is needed to avoid RuntimeError
                if (kwarg == 'units_row'):
                    units_row = pd_kwargs[kwarg]
                if (kwarg == 'datatype'):
                    datatype = check_arg(pd_kwargs[kwarg], 
                                         VALID_DATATYPES)
                if (kwarg == 'column_map'):
                    column_map = pd_kwargs[kwarg]
                if (kwarg == 'index_col'):
                    raise ValueError("Argument 'index_col' not allowed in WADI")
                if kwarg not in valid_kwargs:
                    pd_kwargs.pop(kwarg)
            
            # Use the pd.concat function to join the return values from the 
            # pandas reader function (i.e. the DataFrames read from the file)
            print('Reading...')
            df_r = pd_reader(file_path, **pd_kwargs)
            print('Done reading...')
            df_r.rename(columns=column_map, inplace=True)
            df = pd.concat([df, df_r], axis=1)

            if units_row > -1:
                units += self._read_single_row_as_list(file_path, pd_reader, pd_kwargs, units_row)
            else:
                units += ([''] * df_r.shape[1])
            
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
            warnings.warn(f"argument 'units_row' may not work as expected with reader {pd_reader}")
        if ('sheet_name' in pd_kwargs):
            units_kwargs['sheet_name'] = pd_kwargs['sheet_name']
        if ('usecols' in pd_kwargs):
            units_kwargs['usecols'] = pd_kwargs['usecols']

        return pd_reader(file_path, **units_kwargs).fillna('').values[-1].tolist()

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
