from datetime import datetime as dt
import os
import warnings

class WadiBaseClass(object):
    """
    Class for importing hydrochemical data in a variety of formats

    Examples
    --------

    TBC::
    """

    def __init__(self,
                ):
        """
        Parameters
        ----------
        """

        self._log_str = ""
    
    def _remove_log_file(self,
                       ):
        try:
            os.remove(self._log_file)
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
                        fname,
                        mode='a',
                        ):
        """
        Saves the log file string to a text file

        Parameters
        ----------
            fname: str
                Name of the log file
            mode: str
                Python file mode for opening the file. Default is 'a',
                which means that the log file string will be appended 
                to the log file.
        """

        try:
            with open(fname, mode) as f:
                ascii_str = self._log_str.encode('ascii', 'ignore').decode()
                f.write(ascii_str)
            self._log_str = ""
        except FileNotFoundError:
            self._warn(f"Log file {fname} could not be created.")