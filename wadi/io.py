from pathlib import Path
from wadi.base import OUTPUT_DIR, WadiBaseClass
from wadi.harmonize import Harmonizer
from wadi.mapping import Mapper
from wadi.reader import Reader

class Importer(WadiBaseClass):
    """
    Class for importing hydrochemical data in a variety of formats

    Examples
    --------

    import wadi as wd

    wi = wd.Importer()
    wi.read_data('chem_data.xlsx')
    """

    def __init__(self):
        """
        Class initialization method

        Parameters
        ----------
        """

        # Call the ancestors initialization method
        WadiBaseClass.__init__(self)
        
        # Infer log file name from file_path
        self._log_fname = Path(OUTPUT_DIR, "wadi.log")
        self._log("WADI log file", timestamp=True)

        # Define placeholder for the DataFrame that will contain the data
        self.df = None

        # Define infotable attribute. The infotable is a dict with
        # information about column names, units, datatypes and values.
        # It is initialized when the user calls read_data and used
        # by the harmonize function to produce a new DataFrame. 
        self._infotable = None

        # Initialize Reader object. The Reader class is designed
        # to be callable so the self.read_data attribute becomes a
        # function that the user can call.
        self.read_data = Reader(self)

        # Initialize Mapper objects. The Mapper class is designed
        # to be callable so the self.map_data and self.map_units 
        # attributes becomes functions that the user can call. The
        # 'name' and 'unit' arguments correspond to the keys in the
        # infotable.
        self.map_data = Mapper(self, 'name')
        self.map_units = Mapper(self, 'unit')

        # Initialize Harmonizer object. The Harmonizer class is designed
        # to be callable so the self.harmonize attribute becomes a
        # function that the user can call.
        self.harmonize = Harmonizer(self)





    # def _create_infotable(self, units, datatypes):
    #     """
    #     Creates a nested dict with information about the imported data.
    #     Each dict in the infotable will contain the following items:
    #     - 'name': the name of the feature
    #     - 'unit': the feature's units
    #     - 'sampleids' (only for stacked data): the sample identifiers
    #     - 'values': a view to the (concentration) values in self.df
    #     - 'datatype': to indicate if the data are for a feature or sampleinfo

    #     Parameters
    #     ----------
    #     units : list of strings
    #         List with the units for each feature (or sampleinfo data). This
    #         list is created by the '_read_file' function based on the unit_row
    #         kwarg passed by the user to read_data.
    #     datatypes : list of strings
    #         List with the datatype for each feature (or sampleinfo data). This
    #         list is created by the '_read_file' function based on the datatype
    #         kwarg passed by the user to read_data. Datatypes must all 
    #         be in VALID_DATATYPES.
    #     """
    #     # Initialize
    #     self._infotable = InfoTable() 

    #     # Populate the infotable depending on the data format
    #     if (self.format == 'stacked'):
    #         # Find the unique cominations of features + units in the DataFrame
    #         ufus = (self.df[self._col_f] + self.df[self._col_u]).dropna().unique()
    #         for fu in ufus:
    #             # Select a unique feature + unit combination
    #             idx = (self.df[self._col_f] + self.df[self._col_u] == fu)
    #             # Set the key in the infotable to the first element in the
    #             # feature name column (all values in the column will be equal)
    #             key = self.df.loc[idx, self._col_f].iloc[0]
    #             # Define the dictionary with the required data
    #             i_dict = {'name': key,
    #                       'unit': self.df.loc[idx, self._col_u].iloc[0], 
    #                       'sampleids': self.df.loc[idx, self._col_s],
    #                       'values': self.df.loc[idx, self._col_v],
    #                       'datatype': 'feature'}
    #             # Add i_dict to the info_table
    #             self._infotable[key] = i_dict
    #     elif (self.format == 'wide'):
    #         # Iterate over the columns in the DataFrame
    #         for i, key in enumerate(self.df.columns):
    #             # Pandas adds a dot followed by a number for duplicate columns
    #             # so to get the real feature name, it must be removed
    #             col_name = key
    #             duplicate_nr = re.search('\.\d+$', col_name)
    #             if duplicate_nr:
    #                 col_name = col_name.removesuffix(duplicate_nr.group()) # Requires Python 3.9 or later
    #             # Define the dictionary with the required data
    #             i_dict = {'name': col_name,
    #                       'unit': units[i], 
    #                       'values': self.df[key],
    #                       'datatype': datatypes[i]}
    #             # Add i_dict to the info_table
    #             self._infotable[key] = i_dict
        
    #     self._log(self._infotable)

    # def harmonize_obsolete(self,
    #               **kwargs  
    #              ):
    #     """
    #     This function lets the user call the harmonize function of the 
    #     Harmonize class.

    #     Parameters
    #     ----------
        

    #     Returns
    #     -------
    #     pandas.DataFrame
    #         A DataFrame with the data in wide format
    #     """        
        
    #     # Initialize
    #     h = Harmonizer(**valid_kwargs(Harmonizer, **kwargs))
        
    #     # Call the harmonize function, which takes the SampleIds as kwarg
    #     # for the stacked format to be able to create a unique index. The
    #     # infotable is passed as the first arg for both 'stacked' and 'wide'.
    #     if (self.format == 'stacked'):
    #         rv = h.harmonize(self._infotable, 
    #                          self.df[self._col_s])
    #     elif (self.format == 'wide'):
    #         rv = h.harmonize(self._infotable)
        
    #     # Write the logged messages to the log file
    #     h.update_log_file(f"{self._log_fname}.log")
    
    #     return rv

    # def _map_obsolete(self,
    #          s,
    #          **kwargs
    #         ):
        
    #     """
    #     Class internal function that is called by map_data and map_units
    #     to start the mapping of feature/sampleinfo names or units.

    #     Parameters
    #     ----------
    #     s : str
    #         The value of s is either 'name' (when called by map_data) or 
    #         'unit' (when called by map_units), which are valid keys for the
    #         dicts stored in the infotable.        
    #     """ 

    #     # Initialize
    #     m = Mapper(**valid_kwargs(Mapper, **kwargs))

    #     # Call the match method. Passes the keys of the infotable along with 
    #     # a list of strings which contains either the 'name' or 'unit' values
    #     # of all the items in infotable
    #     m.match(self._infotable.keys(), 
    #             self._infotable.list(s),
    #             s,
    #            )

    #     # Write the logged messages to the log file      
    #     m.update_log_file(f"{self._log_fname}.log")
    #     # Write the DataFrame with the mapping summary to an Excel file
    #     fname = Path(OUTPUT_DIR, f"{s}_mapping_results_{self._log_fname.stem}.xlsx")
    #     m.df2excel(fname,
    #                f"{s.capitalize()}s")

    #     # Transfer the aliases found by match to the infotable
    #     # The key will be either alias_n or alias_u           
    #     i_key = f"alias_{s[0]}"
    #     # Convert the alias column to a dictionary, the keys will be
    #     # the values in the header column (which correspond to the keys
    #     # of the infotable)
    #     a_dict = m.df.set_index('header')['alias'].to_dict()

    #     # Loop over the new dict with the aliases and tranfer the results
    #     # into the infotable
    #     for key, value in a_dict.items():
    #         self._infotable[key][i_key] = value

    # def map_data_obsolete(self,
    #               **kwargs,
    #              ):
    #     """
    #     Function to map sampleinfo or feature headers

    #     """         
    #     self._map('name', **kwargs)

    # def map_units_obsolete(self,
    #               **kwargs,
    #              ):
    #     """
    #     Function to map units

    #     """  
    #     # If no match method was specified by the user, select 'regex'       
    #     if ('match_method' not in kwargs):
    #         kwargs['match_method'] = 'regex'
    #     self._map('unit', **kwargs)

    # def read_data(self,
    #               file_path,
    #               pd_reader='read_excel',
    #               mask=None, # Only for stacked data, column name with T/F data
    #               **kwargs):

    #     # Infer log file name from file_path
    #     p = Path(file_path)
    #     self._log_fname = Path(OUTPUT_DIR, p.stem)
    #     self._log("WADI log file", timestamp=True)

    #     # Before calling the Pandas reader function, do some error 
    #     # checking/tweaking of the kwargs
    #     pd_kwargs = copy.deepcopy(vars()['kwargs']) # deepcopy just to be sure

    #     # Use the defaults for na_values if the user did not specify their own 
    #     if ('na_values' not in pd_kwargs):
    #         pd_kwargs['na_values'] = DEFAULT_NA_VALUES
        
    #     # Check if the user specified the 'panes' kwarg, which
    #     # means that multiple dataframes must be read and joined
    #     if ('panes' not in kwargs):
    #         # If panes is not in kwargs then store the kwargs in a 
    #         # one-element list
    #         panes = [kwargs]
    #     else:
    #         # If panes is in kwargs then check if it's a sequence
    #         # before continuing
    #         panes = kwargs['panes']
    #         if not isinstance(panes, (list, tuple)):
    #             raise ValueError("Argument 'panes' must be a list or a tuple")

    #     # Loop over the panes
    #     for pd_kwargs in panes:
    #         # Perform some checks for inconsistent kwargs
    #         if ((self.format == 'stacked') & ('units_row' in pd_kwargs)):
    #             pd_kwargs.pop('units_row')
    #             self._warn("Argument 'units_row' can not be used in combination with wide format and will be ignored.")
    #         if ((self.format == 'stacked') & ('datatype' in pd_kwargs)):
    #             pd_kwargs.pop('datatype')
    #             self._warn("Argument 'datatype' is ignored when format is 'stacked'.")
        
    #     # Call read file to import the data into a single DataFrame
    #     self.df, units, datatypes = self._read_file(file_path,
    #                                                 pd_reader,
    #                                                 panes)

    #     if (mask is not None):
    #         self.df = self.df.loc[self.df[mask]]
    #     #self._check_df_requirements()

    #     # Create the dictionary that stores views to the data read as well as
    #     # additional information (units, data type)
    #     self._create_infotable(units, datatypes)

    #     # Write the log string to the log file (note that mode is 'w',
    #     # because at this point the log file is created for the first time)
    #     self.update_log_file(f"{self._log_fname}.log", 'w')

    # def _read_file(self,
    #               file_path,
    #               pd_reader_name,   
    #               panes):

    #     # Inform user with message on screen that reading has started (may
    #     # take a long time for large files)
    #     self._msg(f"Reading ...")
        
    #     # Get reference to pandas reader function and determine its valid
    #     # keyword arguments
    #     pd_reader = getattr(pd, pd_reader_name)
        
    #     # Start with an empty DataFrame and empty lists for units and datatype
    #     df = pd.DataFrame()
    #     units = []
    #     datatypes = []
    #     # Loop over the sets of kwargs
    #     for pd_kwargs in panes:
    #         units_row = -1
    #         datatype = DEFAULT_DATATYPE
    #         for kwarg in pd_kwargs.copy(): # copy() is needed to avoid RuntimeError
    #             if (kwarg == 'units_row'):
    #                 units_row = pd_kwargs[kwarg]
    #             if (kwarg == 'datatype'):
    #                 datatype = check_arg(pd_kwargs[kwarg], 
    #                                      VALID_DATATYPES)
    #             if (kwarg == 'index_col'):
    #                 raise ValueError("Argument 'index_col' not allowed in WADI")
            
    #         # Create a verbose message for the log file
    #         kws = ", ".join(f"{k}={v}" for k,v in pd_kwargs.items())
    #         self._log(f" * pandas.{pd_reader_name}('{file_path}', {kws})")
            
    #         # Call the requested Pandas reader function to import the data
    #         df_r = pd_reader(file_path, 
    #                          **valid_kwargs(pd_reader, **pd_kwargs))
                        
    #         # Use the pd.concat function to join the return values from the 
    #         # pandas reader function (i.e. the DataFrames read from the file)
    #         df = pd.concat([df, df_r], axis=1)

    #         # Read the units if the user specified a valid row number, else...
    #         if units_row > -1:
    #             units += self._read_single_row_as_list(file_path, pd_reader, pd_kwargs, units_row)
    #         # ... create a list of empty strings with the same length as the
    #         # number of columns read
    #         else:
    #             units += ([''] * df_r.shape[1])
            
    #         # Make sure that the datatype for this pane is copied as many 
    #         # times as there are columns in the DataFrame that was read
    #         datatypes += ([datatype] * df_r.shape[1])

    #     return df, units, datatypes

    # def _read_single_row_as_list(self, file_path, pd_reader, pd_kwargs, units_row):
    #     units_kwargs = {}
    #     if (pd_reader.__name__ in ['read_excel', 'read_csv']):
    #         # Note that header=None does not seem to work in conjuction with skiprows!
    #         # Therefore, read the data up until row units_row + 1, the units will be 
    #         # in the last row of the dataframe returned by the reader
    #         units_kwargs['header'] = None 
    #         units_kwargs['nrows'] = units_row + 1
    #     else:
    #         self._warn(f"argument 'units_row' may not work as expected with reader {pd_reader}")
    #     if ('sheet_name' in pd_kwargs):
    #         units_kwargs['sheet_name'] = pd_kwargs['sheet_name']
    #     if ('usecols' in pd_kwargs):
    #         units_kwargs['usecols'] = pd_kwargs['usecols']

    #     return pd_reader(file_path, **units_kwargs).fillna('').values[-1].tolist()

    # def save_mapping_summary(self, 
    #                          xl_fname='mapping_summary.xlsx'):
    #     writer = pd.ExcelWriter(xl_fname)

    #     for s, m in self.mappers.items():
    #         if m is None:
    #             continue
    #         self._log(f"Saving {s} mapping results to {xl_fname}.")
    #         m.df.to_excel(writer, 
    #                       sheet_name=f"{s.capitalize()}s")
        
    #     writer.save()

    #     self.update_log_file(self._log_fname, 'a')

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
