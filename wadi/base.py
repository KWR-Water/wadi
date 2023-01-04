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

    def __init__(self,
        log_fname,
        output_dir,
        create_file=False,
        ):
        
        self.log_fname = Path(log_fname)
        self.output_dir = Path(output_dir).resolve()

        # Create subdirectory for output (log files, Excel files)
        self.output_dir.mkdir(exist_ok=True)

        self._log_str = ""
        if (create_file):
            self._log("WADI log file", timestamp=True)
            self.update_log_file(mode='w')

    def _remove_log_file(self):
        """
        Attempts to delete the log file
        """
        try:
            os.remove(self.log_fname)
        except OSError:
            pass
    
    def _log(self,
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
        
    def _msg(self,
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

    def _warn(self,
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

    def update_log_file(self,
                        mode='a',
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
            with open(self.log_fname, mode) as f:
                ascii_str = self._log_str.encode('ascii', 'ignore').decode()
                f.write(ascii_str)
            self._log_str = ""
        except FileNotFoundError:
            self._warn(f"Log file {self.log_fname} could not be created.")

class WadiChildClass(WadiParentClass):
    """
    Base class for children of the WADI Importer class. Has the
    same functionality but adds the parent attribute. The __init__
    function is designed to ensure that the class instance has the
    same log_fname and output_dir as the Importer class.
    """

    def __init__(self,
                 parent,
                ):
        
        super().__init__(parent.log_fname,
                         parent.output_dir)
        
        self.parent = parent
