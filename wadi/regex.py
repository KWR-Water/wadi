import re

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
