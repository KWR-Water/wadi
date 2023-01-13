import re

import molmass as mm
from molmass.molmass import FormulaError
from pint import UnitRegistry
from pint.errors import DimensionalityError, UndefinedUnitError

from wadi.base import WadiBaseClass

DEFAULT_RE_DICT0 = {'num': ["[a-zA-Z]*", "\s*"],
                    'mw0': ["[a-zA-Z0-9]*", "?\s*"],
                    'div': ["[/.,]", "\s*"],
                    'den0': ["[0-9]*", "?"],
                    'den1': ["[a-zA-Z]*", "\s*"],
                    'mw1': ["[a-zA-Z0-9]*", "?"],
                   }
DEFAULT_RE_DICT1 = {'txt': ["[a-zA-Z]*", ""]}

def dict2str(groupdict):
    n = groupdict['num']
    d0 = groupdict['den0']
    d1 = groupdict['den1']
    txt = groupdict['txt']
    w0 = groupdict['mw0']
    w1 = groupdict['mw1']

    rv = f"" 

    if not all(x is None for x in [n, d0, d1]):
        if len(n):
            rv += f"{n}"
        else:
            rv += f"1"
        if len(d0):
            rv += f" / ({d0}"
        else:
            rv += f" / (1"
        if len(d1):
            rv += f"{d1})"
        else:
            rv += f")"
        if len(w0):
            rv += f"|{w0}"
        elif len(w1):
            rv += f"|{w1}"

    elif (txt is not None):
        rv += txt
    return rv

class UnitRegexMapper:
    def __init__(self, *args, func=dict2str):
        if args:
            self.RE = self._dict2RE(*args)
        else:
            self.RE = self._dict2RE(DEFAULT_RE_DICT0, 
                                    DEFAULT_RE_DICT1, 
                                   )
        self.func = func

    @staticmethod
    def _dict2RE(*args):
        rv = r""
        for i, re_dict in enumerate (args):
            if not isinstance(re_dict, dict):
                raise TypeError(f"argument {re_dict} must be of type dict")
            if (i == 0):
                rv += r"^\s*"
            else:
                rv += r"|^\s*"
            for key, value in re_dict.items():
                rv += rf"(?P<{key}>{value[0]}){value[1]}"
            rv += r"\s*$"

        return rv

    def str(self, groupdict):
        return self.func(groupdict)

class UnitConverter:
    def __init__(self):

        super().__init__()

        self.ureg = UnitRegistry()
        self.ureg.default_format = "~"

    def _get_mw(
        self,
        s,
    ):
        """
        This function uses the molmass library to determine the
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
        try:
            return mm.Formula(s).mass * self.ureg('g/mol')
        except FormulaError:
            return None

    def get_uc(
        self,
        qs,
        target_units,
        mw,
    ):
        """
        Use Pint to determine the value of the unit
        conversion factor.
        """
        try:
            qt = self.ureg(target_units)
            if mw is None:
                uc = qs.to(qt)
            else:
                uc = qs.to(qt, 'chemistry', mw=mw)

            # Divide uc by qs to get the right dimensions
            uc /= qs 
        except (AttributeError, DimensionalityError) as e:
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
        mw : Pint Quantity object
            The molecular mass of the substance.
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
            uq = self.ureg.Quantity(s_parts[0])

            # Store the substance formula in mw_formula.
            mw_formula = s_parts[2]
            # If no formula was specified the length of mw
            # will be zero and in that case 'name' will be 
            # used instead to look up the molecular mass.
            if (len(mw_formula) == 0):
                mw_formula = name
            mw = self._get_mw(mw_formula)

            # Write a message to the log file
            msg = f" - Successfully parsed unit '{u_str}' with pint for {name}"

            return uq, mw, msg
        except (AttributeError, TypeError, UndefinedUnitError, ValueError):
            # When an error occurs, write a message to the log file and
            # return empty return values.
            msg = f" - Failed to parse unit '{u_str}' with pint for {name}"
            return None, None, msg    
        
