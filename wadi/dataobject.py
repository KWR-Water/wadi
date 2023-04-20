from wadi.base import WadiBaseClass
from wadi.harmonizer import Harmonizer
from wadi.mapper import Mapper
from wadi.filereader import FileReader

DEFAULT_OUTPUT_DIR = "wadi_output"

class DataObject(WadiBaseClass):
    """
    Class for importing hydrochemical data in a variety of formats. The
    class provides various functions that allow the user to convert the
    data into different formats.

    Examples
    --------

    import wadi as wd

    wdo = wd.DataObject()
    wdo.file_reader('chem_data.xlsx')
    df = wd.get_frame()
    """

    def __init__(
        self,
        log_fname="wadi.log",
        output_dir=DEFAULT_OUTPUT_DIR,
        silent=False,
    ):
        """
        Class initialization method. Initializes the parent class
        object so that a log file and an output directory are
        created. Also initializes the Reader, Mapper and Harmonizer
        callable classes so that the user can set their attributes
        via the methods file_reader, name_map, unit_map and
        harmonizer.

        Parameters
        ----------
        log_fname : str, optional
            Name of the log file. Default: 'wadi.log'
        output_dir : str, optional
            Name of the directory with output files. Default:
            'wadi_output'
        silent : bool, optional
            Flag to indicate if screen output is desired during
            data processing. When True then no screen output is
            displayed. Default is False (recommended for large
            data files when processing can be slow). When
            True messages will still appear in the log file. Warnings
            are always displayed on the screen regardless of the
            value for 'silent'.
        """

        # Call the ancestor's initialization method to set the log 
        # file name and output directory. The argument create_file is
        # set to True to ensure that the log_file is written so that
        # other parts of the code can append to it.
        super().__init__(
            log_fname,
            output_dir,
            silent,
            create_file=True,
        )

        # Define placeholder attribute for the DataFrame that will
        # contain the imported data...
        self._imported_df = None
        # # ... as well as the converted data
        self._converted_df = None

        # Define placeholder attribute for the InfoTable. The InfoTable
        # is a dict with information about column names, units, datatypes
        # and values. It is initialized when the _execute method of the
        # FileReader instance is called and used by the Harmonizer
        # to produce the converted DataFrame
        self._infotable = None

        # Initialize the FileReader object. The FileReader class
        # is designed to be callable so the self.file_reader attribute
        # becomes a method that the user can call.
        self.file_reader = FileReader()

        # Initialize Mapper objects. The Mapper class is designed
        # to be callable so the self.name_map and self.unit_map
        # attributes becomes methods that the user can call. The
        # 'name' and 'unit' arguments correspond to the keys in the
        # InfoTable class instance.
        self.name_map = Mapper("name")
        self.unit_map = Mapper("unit")

        # Initialize Harmonizer object. The Harmonizer class is
        # designed to be callable so the self.harmonizer
        # attribute becomes a method that the user can call.
        self.harmonizer = Harmonizer()

        # Loop over all attributes and check which are a subclass of
        # WadiBaseClass. If they are, ensure that the log file name
        # output directory and silent flag are all set to the same
        # value as the current object.
        for v in self.__dict__.values():
            if issubclass(type(v), WadiBaseClass):
                v._log_fname = self._log_fname
                v._output_dir = self._output_dir
                v._silent = self._silent

    def _execute(self, import_only=False):
        """
        This method calls the _execute methods of the child objects
        that read, map and harmonize the data. Upon success the
        converted data are stored in self._converted_df

        Parameters
        ----------
        import_only : bool, optional
            When True the data are read but not mapped or harmonized.
            Default: False.
        """
        # Import data
        self._imported_df, self._infotable = self.file_reader._execute()

        # Exit the function when only the imported data were requested.
        # Note that this function is not supposed to return any values.
        if import_only == True:
            return

        # Map names
        info_table_items = self.name_map._execute(
            self._infotable.list_keys(), self._infotable.list_dict1_item("name")
        )
        self._infotable.update_items(info_table_items)

        # Map units
        info_table_items = self.unit_map._execute(
            self._infotable.list_keys(), self._infotable.list_dict1_item("unit")
        )
        self._infotable.update_items(info_table_items)

        # Harmonize
        self._converted_df = self.harmonizer._execute(self._infotable)

    def get_converted_dataframe(self,
            include_units=True,
            force_conversion=False,
        ):
        """
        This method converts the input data based on the specified
        name and unit maps and harmonizer, and returns the result
        as a DataFrame.

        Parameters
        ----------
        include_units : bool, optional
            When True the DataFrame's columns will be a MultiIndex
            that contains both the feature aliases and their units.
            When set to False a DataFrame is returned of which the 
            columns simply correspond to the feature aliases and 
            the units are discarded. The latter option is useful when
            the DataFrame is intended for further processing in HGC.
            Default: True.
        force_conversion: bool, optional
            When True, the function will always map and harmonize
            the data before it returns the DataFrame. When False,
            the results from any previously executed data mapping
            and harmonizing are returned, when present. Default:
            False. 

        Returns
        ----------
        result : DataFrame
            The converted DataFrame.
        """
        if (self._converted_df is None) or (force_conversion == True):
            self._execute()

        if include_units == True:
            return self._converted_df
        else:
            level0_cols = self._converted_df.columns.get_level_values(0)
            return self._converted_df.set_axis(level0_cols, axis='columns')
    
    def get_imported_dataframe(self):
        """
        This method returns the imported DataFrame (that is, the data 
        'as read').

        Returns
        ----------
        result : DataFrame
            The imported DataFrame.
        """
        if self._imported_df is None:
            self._execute(import_only=True)
        return self._imported_df

    def get_imported_names(self):
        """
        This method returns the names of the features
        in the imported DataFrame.

        Returns
        ----------
        result : list
            A list with feature names in the imported DataFrame.
        """
        if self._infotable is None:
            self._execute(import_only=True)
        return self._infotable.list_dict1_item('name')
