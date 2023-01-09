from wadi.base import WadiParentClass
from wadi.harmonizer import Harmonizer
from wadi.mapper import Mapper
from wadi.reader import Reader

DEFAULT_OUTPUT_DIR = "wadi_output"

class DataObject(WadiParentClass):
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

    def __init__(
        self,
        log_fname="wadi.log",
        output_dir=DEFAULT_OUTPUT_DIR,
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
        """

        # Call the ancestors initialization method to set the log file
        # name and output directory. The argument create_file is 
        # set to True to ensure that the log_file is written so that
        # other parts of the code can append to it.
        super().__init__(log_fname, output_dir, create_file=True)

        # Define placeholder attribute for the DataFrame that will 
        # contain the data
        self.df = None

        # Define placeholder attribute for the InfoTable. The InfoTable
        # is a dict with information about column names, units, datatypes
        # and values. It is initialized when the user calls read_data and
        # used by the harmonize function to produce a new DataFrame.
        self._infotable = None

        # Initialize Reader object. The Reader class is designed
        # to be callable so the self.read_data attribute becomes a
        # function that the user can call.
        self.read_data = Reader(self)

        # Initialize Mapper objects. The Mapper class is designed
        # to be callable so the self.map_names and self.map_units
        # attributes becomes functions that the user can call. The
        # 'name' and 'unit' arguments correspond to the keys in the
        # infotable.
        self.map_names = Mapper(self, "name")
        self.map_units = Mapper(self, "unit")

        # Initialize Harmonizer object. The Harmonizer class is designed
        # to be callable so the self.harmonize attribute becomes a
        # function that the user can call.
        self.harmonize = Harmonizer(self)
