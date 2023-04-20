import molmass as mm
from molmass.molmass import FormulaError
from pint import UnitRegistry
from pint.errors import DimensionalityError, UndefinedUnitError, OffsetUnitCalculusError

from wadi.api_utils import get_pubchem_molecular_weight

# DEFAULT_RE_DICT0 is the default dictionary to create a regular 
# expression for matching chemical concentration units. It is 
# designed to recognize variants such as mg/l, mg N/l or mg/l N. 
# Each element is a list, the first element being the character set 
# to match, the second element being the separator that follows.
DEFAULT_RE_DICT0 = {
    # Elements before the separator:
    # - descriptor (e.g. mg in mg/l) 
    "num": ["[a-zA-Z]*", "\s*"], 
    # - formula for molar mass (e.g. N in mg N/l) 
    "mw0": ["[a-zA-Z0-9]*", "?\s*"], 
    # Separator:
    "div": ["[/.,]", "\s*"], 
    # Elements following the separator:
    # - a number (e.g. 50 in cfu/50ml)
    "den0": ["[0-9]*", "?"], 
    # - descriptor (e.g. l in mg/l)
    "den1": ["[a-zA-Z]*", "\s*"], 
    # - formula for molar mass (e.g. NO3 in mg/l NO3)
    "mw1": ["[a-zA-Z0-9]*", "?"], 
}
# DEFAULT_RE_DICT1 is a dictionary to create a regular 
# expression that matches simple text.
DEFAULT_RE_DICT1 = {"txt": ["[a-zA-Z]*", ""]}


def dict2str(groupdict):
    """
    This function attempts to create a string that can be parsed by
    Pint based on the elements of a dictionary that is returned by
    the regex match method in Mapper._match_regex. This function works
    only for the default dictionaries defined above and creates a
    string specifically formatted for the _str2pint method in the 
    UnitConverter class.
    """

    # Store the elements of the dictionary as local variables for 
    # shorter code lines
    n = groupdict["num"]
    d0 = groupdict["den0"]
    d1 = groupdict["den1"]
    txt = groupdict["txt"]
    w0 = groupdict["mw0"]
    w1 = groupdict["mw1"]

    # Set return value to None if the groupdict elements do not
    # contain any unit information or if the 'txt' element has
    # length zero (happens when an empty string was matched).
    rv = None

    # Check if at least a numerator and/or one of the denominators
    # is contained in the dictionary with matched terms. 
    if not all(x is None for x in [n, d0, d1]):
        # Create an empty formatted string
        rv = f""
        # Add the numerator to rv if a match was found for it, else add '1'.
        if len(n):
            rv += f"{n}"
        else:
            rv += f"1"
        # Add a '/(' and the first denominator to rv if a match was found for
        # it, else add '/ (1'.
        if len(d0):
            rv += f" / ({d0}"
        else:
            rv += f" / (1"
        # Add the second denominator and a closing parenthesis to rv 
        # if a match was found for it, else add just a closing parenthesis.
        if len(d1):
            rv += f"{d1})"
        else:
            rv += f")"
        # Add the formula that was found for the molar mass (if any was matched). 
        # It is separated from the unit string by a vertical bar, which is what
        # the _str2pint method in the UnitConverter class expects.  
        if len(w0):
            rv += f"|{w0}"
        elif len(w1):
            rv += f"|{w1}"
    elif txt is not None: # Return any text string if one was matched.
        if len(txt) > 0:
            rv = txt

    return rv


class UnitRegexMapper:
    """
    Class to make working with regular expressions to match units a little
    bit easier (not easy).
    """

    def __init__(self, *args, func=dict2str):
        """
        Class initialization method. Defines the dictionaries used to create
        the regular expressions to match the unit strings with, as well as the 
        function to translate the groupdicts returned by the match method to a
        string that can be used by the _str2pint method in the UnitConverter 
        class.
        """
        # Check if any dictionaries were passed as arguments, else use the 
        # default dictionaries defined above.
        if args:
            self.RE = self._dict2RE(*args)
        else:
            self.RE = self._dict2RE(
                DEFAULT_RE_DICT0,
                DEFAULT_RE_DICT1,
            )
        # Set the function to be used for translating the groupdicts returned
        # by the match method to a string for the _str2pint method in the 
        # UnitConverter class.
        self.func = func

    @staticmethod
    def _dict2RE(*args):
        """
        This function creates a string with a regular expression for parsing
        (chemical concentration) units. For more details on group names see 
        https://docs.python.org/3/library/re.html
        """
        rv = r""
        for i, re_dict in enumerate(args):
            if not isinstance(re_dict, dict):
                raise TypeError(f"argument {re_dict} must be of type dict")
            if i == 0:
                rv += r"^\s*"
            else:
                rv += r"|^\s*"
            for key, value in re_dict.items():
                rv += rf"(?P<{key}>{value[0]}){value[1]}"
            rv += r"\s*$"

        return rv

    def str(self, groupdict):
        """
        This function is simply a wrapper that returns the string
        created by the function that translates the groupdicts 
        returned by the match method to a string that can be used by
        the _str2pint method in the UnitConverter class."""
        return self.func(groupdict)


class UnitConverter:
    """
    Class with some methods for unit parsing and conversion with Pint.
    """
    def __init__(self):
        """
        Class initialization method.
        """

        super().__init__()

        self._ureg = UnitRegistry()
        self._ureg.default_format = "~"

    def _get_mw(
        self,
        s,
    ):
        """
        This method uses the molmass library to determine the
        molar mass of a substance.

        Parameters
        ----------
        s : str
            Name of the substance.

        Returns
        ----------
        result : Pint Quantity object
            The molar mass in g/mole, or None if  a FormulaError
            was raised from within the molmass library.
        """
        rv = None
        try:
            rv = mm.Formula(s).mass * self._ureg("g/mol")
        except FormulaError as e:
            print(f" - Could not retrieve molar mass {s} with molmass library. Trying PubChem...")
            rv = get_pubchem_molecular_weight(s) 
            if rv is not None:
                rv = rv * self._ureg("g/mol")
            
        return rv

    def get_uc(
        self,
        qs,
        target_units,
        mw_formula,
    ):
        """
        Use Pint to determine the value of the unit
        conversion factor.

        Parameters
        ----------
        qs : Pint Quantity object
            The source units (for example 1 mg/l).
        target_units : str 
            String that defines the target units.
        mw_formula : str
            Chemical formula with which to convert
            between mass and molar concentration units.

        Returns
        -------
        qt : Pint Quantity object
            The target units
        uc : Pint Quantity object
            The unit conversion factor.
        """
        try:
            # Convert the target_units string to a Pint Quantity object
            qt = self._ureg(target_units)

            # Determine the molecular mass in g/mol.
            mw = None
            # Only try to determine the molecular mass if the target units
            # are molar units, which can be identified using the Pint
            # Quantity's object dimensionality property. If this is the case
            # a key called '[substance]' will be present.
            if ('[substance]' in qt.dimensionality.keys()) and (mw_formula is not None):
                mw = self._get_mw(mw_formula)
                if mw is None:
                    mw = get_pubchem_molecular_weight(mw_formula)

            # Use the source units 'to' method to determine the unit
            # conversion factor.
            if mw is None:
                uc = qs.to(qt)
            else:
                uc = qs.to(qt, "chemistry", mw=mw)

            # Divide uc by qs to get the right dimensions
            uc /= qs
        except (AttributeError, DimensionalityError, OffsetUnitCalculusError) as e:
            qt = None
            uc = None

        return qt, uc

    def _str2pint(
        self,
        name,
        u_str,
    ):
        """
        This function parses the three-part string that is created by
        _match_regex when the units are mapped using a regular
        expression.

        Parameters
        ----------
        name : str
            The feature name alias. Also serves as an alternative string
            to determine the molar mass if Pint fails to parse u_str.
        u_str : str
            String representation of the units to be parsed.

        Returns
        ----------
        uq : Pint Quantity object
            The units represented as Pint Quantity object.
        mw_formula : str
            The chemical formula of the substance, to be used in get_uc
            to convert between mass and molar concentration units.
        msg : str
            A message intended for the log file.

        Notes
        ----------
        The function uses the partition function to split the
        string at the | symbol into a three-part tuple that
        contains (i) the part before the separator, (ii) the
        separator itself (redundant, not used), and (iii) the
        part after the separator.
        The part after the | symbol may or may not contain the
        formula for the molecular mass, depending on the format
        for the units in the input file. In that case name of
        the feature (passed to the function as 'name') is
        used as the formula to determine the molecular mass.
        Both the units and the molecular mass are converted to a
        Pint Quantity object (i.e., the product of a unit and
        a magnitude).
        """
        try:
            # Use the partition to split the string at the | symbol.
            s_parts = u_str.partition("|")
            # Convert the units string to a Pint Quantity object
            uq = self._ureg.Quantity(s_parts[0])

            # Store the substance formula in mw_formula.
            mw_formula = s_parts[2]
            # If no formula was specified the length of mw
            # will be zero and in that case 'name' will be
            # used instead to look up the molecular mass.
            if len(mw_formula) == 0:
                mw_formula = name

            # Write a message to the log file
            msg = f" - Successfully parsed unit '{u_str}' with pint for {name}"

            return uq, mw_formula, msg
        except (AttributeError, TypeError, UndefinedUnitError, ValueError):
            # When an error occurs, write a message to the log file and
            # return empty return values.
            msg = f" - Failed to parse unit '{u_str}' with Pint for {name}"
            return None, None, msg
