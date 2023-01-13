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

    wi = wd.DataObject()
    wi.read_data('chem_data.xlsx')
    """
    # file_reader = GenericSetter()
    # name_map = GenericSetter()
    # unit_map = GenericSetter()
    # harmonizer = GenericSetter()

    def __init__(
        self,
        log_fname="wadi.log",
        output_dir=DEFAULT_OUTPUT_DIR,
        silent=False,
    ):
        """
        Class initialization method. Initializes the parent class 
        object so that a log file and an output directory are created.
        Also initializes the Reader, Mapper and Harmonizer callable
        classes to create functions for the user to read, map and 
        harmonize the data.

        Parameters
        ----------
        log_fname : str, optional
            Name of the log file
        output_dir : str, optional
            Name of the directory with output files
        silent : bool, optional,
            Flag to indicate if screen output is desired during
            data processing. When True then no screen output is
            displayed. Default is False (recommended for large 
            data files when processing can be slow). When
            True messages will still appear in the log file. Warnings
            are always displayed on the screen regardless of the
            value for 'silent'.
        """

        # Call the ancestors initialization method to set the log file
        # name and output directory. The argument create_file is 
        # set to True to ensure that the log_file is written so that
        # other parts of the code can append to it.
        super().__init__(log_fname, 
            output_dir, 
            silent,
            create_file=True,
        )

        # Define placeholder attribute for the DataFrame that will 
        # contain the imported data...
        self._imported_df = None
        # # ... as well as the converted data
        # self._converted_df = None

        # Define placeholder attribute for the InfoTable. The InfoTable
        # is a dict with information about column names, units, datatypes
        # and values. It is initialized when the user calls read_data and
        # used by the harmonize function to produce a new DataFrame.
        self._infotable = None

        # Initialize Reader object. The Reader class is designed
        # to be callable so the self.read_data attribute becomes a
        # function that the user can call.
        self.file_reader = FileReader()

        # Initialize Mapper objects. The Mapper class is designed
        # to be callable so the self.map_names and self.map_units
        # attributes becomes functions that the user can call. The
        # 'name' and 'unit' arguments correspond to the keys in the
        # infotable.
        self.name_map = Mapper("name")
        self.unit_map = Mapper("unit")

        # Initialize Harmonizer object. The Harmonizer class is designed
        # to be callable so the self.harmonize attribute becomes a
        # function that the user can call.
        self.harmonizer = Harmonizer()

        # Loop over all attributes and check which are a subclass of 
        # WadiBaseClass. If they are, ensure that the log file name
        # and output directory are set to the same value as the
        # current class.
        for v in self.__dict__.values():
            if issubclass(type(v), WadiBaseClass):
                v._log_fname = self._log_fname
                v._output_dir = self._output_dir
                v._silent = self._silent

    def get_frame(self):
        # Read the file and return a DataFrame with the data,
        # and lists with the (concentration) units and the
        # datatype. The keyword arguments can contain any valid
        # kwarg that is accepted by the pd_reader function.
        # They are passed verbatim to the _read_data function
        # and are checked for consistency there.
        self._imported_df, self._infotable = self.file_reader._read_data()
        info_table_items = self.name_map.match(self._infotable.keys(), 
            self._infotable.list('name'))
        self._infotable.update_items(info_table_items)
        
        info_table_items = self.unit_map.match(self._infotable.keys(), 
            self._infotable.list('unit'))
        self._infotable.update_items(info_table_items)

        converted_df = self.harmonizer.harmonize(self._infotable)

        return converted_df
