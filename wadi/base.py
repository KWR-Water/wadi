import codecs
from datetime import datetime as dt
import os
from pathlib import Path
import warnings


class WadiParentClass:
    """
    Base class for WADI Importer class and its children.
    Defines functions to provide functionality to log and
    print messages and warnings.
    """

    def __init__(
        self,
        log_fname,
        output_dir,
        create_file=False,
    ):
        """
        Class initialization method.

        Parameters
        ----------
        log_fname : str, optional
            Name of the log file
        output_dir : str, optional
            Name of the directory with output files
        create_file : bool, optional
            Flag to indicate if the log file must be created. Must be
            explicitly set to True when an object of this class is
            initialized for the first time. In WaDI this happens in
            the init method of Converter.
        """

        # Convert output_dir to a Path object and get the absolute
        # path by calling resolve
        self.output_dir = Path(output_dir).resolve()
        # Convert log_fname to a Path object
        self.log_fname = Path(log_fname)
        # Check if only a filename or a full path was specified for
        # the log filename. If only a filename was specified then
        # the parts argument will be equal to one. In that case the
        # output_dir is prefixed to the log filename
        if len(self.log_fname.parts) == 1:
            self.log_fname = Path(self.output_dir, self.log_fname)

        # Create subdirectory for output (log files, Excel files)
        self.output_dir.mkdir(exist_ok=True)

        # Add the _log_str attribute. Descendants of this class will
        # use this attribute to create the text strings that will be
        # written to the log file
        self._log_str = ""
        # The first time the class is initialized the create_file
        # argument must be set to True to write the file. A single
        # line with a timestamp will be written. Note that _log_str
        # is reset to "" by the function update_log_file
        if create_file:
            self._log("WADI log file", timestamp=True)
            self.update_log_file(mode="w")

    def _remove_log_file(self):
        """
        Attempts to delete the log file
        """
        try:
            os.remove(self.log_fname)
        except OSError:
            pass

    def _log(
        self,
        s,
        timestamp=False,
    ):
        """
        Appends a new line to the log file string.

        Parameters
        ----------
            s: str
                Text string to be written to log file.
            timestamp: bool
                If True the text string is followed by the current time
                between parentheses. No timestamp is appended when False.
        """

        if timestamp:
            ts = dt.now().strftime("%d/%m/%Y %H:%M:%S")
            self._log_str += f"{s} ({ts})\n"
        else:
            self._log_str += f"{s}\n"

    def _msg(
        self,
        s,
    ):
        """
        Prints a message to the screen and appends it as a new line to the
        log file string.

        Parameters
        ----------
            s: str
                Text string to be printed to the screen and written to
                the log file.
        """

        print(s)
        self._log_str += f"{s}\n"

    def _warn(
        self,
        s,
    ):
        """
        Throws a UserWarning and appends it as a new line to the
        log file string.

        Parameters
        ----------
            s: str
                Text string to be passed to the UserWarning and written to
                the log file.
        """

        warnings.warn(s)
        self._log_str += f"Warning: {s}\n"

    def update_log_file(
        self,
        mode="a",
    ):
        """
        Saves the log file string to a text file

        Parameters
        ----------
            mode: str
                Python file mode for opening the file. Default is 'a',
                which means that the log file string will be appended
                to the log file.
        """

        try:
            # Uses the file open method from codecs to enable unicode
            # characters to be written to the file.
            with codecs.open(self.log_fname, mode, encoding="utf8") as f:
                f.write(self._log_str)
        except FileNotFoundError:
            self._warn(f"Log file {self.log_fname} could not be created.")

        # Reset _log_str to an empty string
        self._log_str = ""


class WadiChildClass(WadiParentClass):
    """
    Base class for children of the WADI Converter class. Has the
    same functionality as WadiParentClass but adds the converter
    attribute. The __init__ function is designed to ensure that
    the class instance has the same log_fname and output_dir as
    the Converter class instance to which the object belongs.
    """

    def __init__(
        self,
        converter,
    ):

        # Call the ancestor init function to set the log_fname
        # and output_dir attributes to be the same as for the
        # Converter class instance to which the object belongs
        super().__init__(converter.log_fname, converter.output_dir)

        self.converter = converter
