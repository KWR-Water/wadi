from collections import UserList
import inspect
import re

import numpy as np

# DEFAULT_FUZZY_MINSCORES = {1: 100, 3: 100, 4: 90, 5: 85, 6: 80, 8: 75}
DEFAULT_FUZZY_MINSCORES = {1: 100, 3: 100, 4: 90, 5: 85, 6: 80}


def check_arg(arg, valid_args):
    """
    Function that checks if an argument is an element of a list of valid
    arguments.

    Parameters
    ----------
    arg : str
        The string to be checked.
    valid_args : iterable
        List or other iterable with valid arguments.

    Returns
    -------
    result : str
        The first element of a list with the elements in valid_args
        that produced a match for arg.

    Raises
    ------
    IndexError
        When no match was found.

    Notes
    ------
    Uses a regular expression that checks if the argument appears
    at the start of a string (case-insensitive).
    """

    try:
        find = re.compile(rf"^{arg}", re.IGNORECASE)
        return [s for s in valid_args if find.match(s)][0]
    except (ValueError, IndexError) as e:
        raise ValueError(f"invalid argument: '{arg}' must be in {valid_args}")


def check_arg_list(arg_list, valid_args):
    """
    Function that checks if the elements of a list of arguments are
    in a list of valid arguments by calling the function check_arg.

    Parameters
    ----------
    arg_list : str or iterable
        List or other iterable with arguments to be checked. If a str type
        is passed then it is converted to a list.
    valid_args : iterable
        List or other iterable with valid arguments.

    Returns
    -------
    result : list
        List with elements from valid_args that produced a match for the
        elements in arg_list.

    Raises
    ------
    IndexError
        When no match was found for any of the elements in arg_list.
    """

    if isinstance(arg_list, str):
        arg_list = [arg_list]

    return [check_arg(a, valid_args) for a in arg_list]


def check_if_nested_list(n_list, min_elements=2):
    """
    Function that checks if all elements of a list are lists with a
    minimum number of elements.

    Parameters
    ----------
    n_list : list
        The list to be checked.
    min_elements : int
        The minimum number of elements that the list(s) within n_list
        must consist of.

    Raises
    ------
    TypeError
        When n_list or any of its elements is not a list.
    ValueError
        When a list within n_list contains less than min_elements elements.
    """
    error_msg = f"Each nested element must be a list with >={min_elements} elements."
    if isinstance(n_list, list):
        for l in n_list:
            if isinstance(l, list):
                if len(l) < min_elements:
                    raise ValueError(error_msg)
            else:
                raise TypeError(error_msg)
    else:
        raise TypeError("Expected a nested list")

def parse_name_and_units(s):
    """
    This function attempts to extract the feature name and units from 
    a string. It tries to split the string at the first space character.
    The first item before the space is the feature name (verbatim). If
    the part after the space contains any parentheses, brackets or accolades
    these are stripped off and the remaining part is considered to contain
    the units. For example, it will correctly recognize the following 
    formats: 'Ca', 'Mg mg/l', 'Na (mg/l)', 'NO3 [mg N/l]', 'SO4 {mg/l S}'.
    The units for 'Ca tot mg/l' will be incorrectly inferred because the
    string contains two spaces.

    Parameters
    ----------
    s : str
        A string from which the name and units must be extracted.

    Returns
    -------
    name : str
        The feature name extracted from 's'. For the example strings above, 
        the resulting names will be 'Ca', 'Mg', 'Na', 'NO3', 'SO4' and 'Ca'.
    units: str
        The units extracted from 's'. For the example strings above, the 
        corresponding units will be '', 'mg/l', 'mg/l', 'mg N/l', 
        'mg/l S' and 'tot mg/l'.
    """

    # Split string at the first space.
    split_str = s.split(sep=None, maxsplit=1)
    # If the string contains no space separator the
    # string is considered to be the feature name. An
    # empty string is returned for the units.
    if len(split_str) == 1:
        return split_str[0], ""
    # If the string was sucessfully split, the
    # first list element is considered to be the 
    # feature name, the second the units.
    elif len(split_str) == 2:
        # Use a regular expression to strip off any
        # parentheses, brackets or accolades from the
        # string with the units.
        return split_str[0], re.sub("[\(\)\[\]\{\}]", "", split_str[1])
    
    # For empty strings the list returned by the split
    # function will be empty. Return empty strings for
    # both name and units in that case.
    return "", ""

class StringList(UserList):
    """
    Class with convenience methods for lists of strings.
    """
    def __init__(self, initlist=None):
        """
        Class initialization method. Ensures that all items are of type str.

        Parameters
        ----------
        initlist : list
            List of items to add to the StringList.
        """
        if initlist is not None: 
            super().__init__([str(s) for s in initlist])

    def replace_strings(self, r_dict):
        """
        This method modifies the elements of the StringList by
        performing a search and replace based on the elements in
        r_dict.

        Parameters
        ----------
        r_dict : dict
            Dictionary of which the keys are the strings to search for
            and the  values are the strings to replace the search values
            with.

        Raises
        ------
        TypeError
            When r_dict is not a dictionary.
        """
        if not isinstance(r_dict, dict):
            raise TypeError("Argument 'r_dict' must be of type dict")
        try:
            for key, value in r_dict.items():
                self.data = [s.replace(key, value) for s in self.data]
        except:
            pass

    def strip(self):
        """
        This method removes all leading or trailing whitespace from
        the string items in the list.
        """
        self.data = [s.strip() for s in self.data]

    def strip_parentheses(self):
        """
        This method modifies the elements of the StringList by
        removing all characters between parentheses and the
        parentheses themselves.
        """
        # The .* in the regular expression indicates zero or more
        # repetitions (as per the *) of any character except a
        # newline (as per the .)
        self.data = [re.sub("\(.*\)", "", s) for s in self.data]

    def tidy_strings(self):
        """
        This method modifies the elements of the StringList by
        (i) turning all characters to lowercase (ii) stripping all
        non-ASCII characters and (iii) removing all characters that
        are not letters, numbers or whitespace.
        """
        self.data = [s.lower() for s in self.data]
        self.data = [s.encode("ascii", "ignore").decode("ascii") for s in self.data]
        # Regular expression to filter out any character that is not
        # a numeric lowercase or uppercase symbol (the caret inside the
        # square brackets serves as the not operator).
        self.data = [re.sub("[^0-9a-zA-Z\s]", "", s) for s in self.data]


def valid_kwargs(f, **kwargs):
    """
    This function checks if one or more function arguments are valid
    keyword arguments for callable 'f'.

    Parameters
    ----------
    f : callable function
        Function for which the keyword arguments must be checked.
    kwargs : dict
        Dictionary of keyword arguments.

    Returns
    -------
    result : dict
        Dictionary with only the valid keyword arguments passed in kwargs.
    """
    valid_kwargs = inspect.signature(f).parameters
    rv = kwargs
    for kw in rv.copy():
        if kw not in valid_kwargs:
            rv.pop(kw)

    return rv


def fuzzy_min_score(s):
    """
    This function calculates the minimum score required for a valid
    match in fuzzywuzzy's extractOne function. The minimum score depends
    on the length of 's' and is calculated based on the string lengths and
    scores in the DEFAULT_MINSCORES dictionary.

    Parameters
    ----------
    s : str
        String for which the minimum score must be determined.

    Returns
    -------
    result : float
        The minimum score for 's'.
    """
    xp = list(DEFAULT_FUZZY_MINSCORES.keys())
    fp = [v for v in DEFAULT_FUZZY_MINSCORES.values()]
    # Use the interp function from NumPy. By default this function
    # yields fp[0] for x < xp[0] and fp[-1] for x > xp[-1]
    return np.interp(len(s), xp, fp)


def _wadi_style_warning(message):
    """
    This function formats the warning messages created when
    warnings.warn is called from within the _warn method of
    WadiBaseClass. Note that this function has prescribed
    kwargs, see https://docs.python.org/3/library/warnings.html#warnings.formatwarning

    Parameters
    ----------
    message : str
        The warning message to be displayed.
    """
    return f"WaDI warning: {message}\n"
