from collections import UserDict
import fuzzywuzzy.fuzz as fwf
import fuzzywuzzy.process as fwp
import json
import numpy as np
import pandas as pd
import re
from wadi.utils import RegexMapper, StringList, check_arg_list

DEFAULT_STR2REPLACE = {'Ä': 'a', 'ä': 'a', 'Ë': 'e', 'ë': 'e',
                       'Ö': 'o', 'ö': 'o', 'ï': 'i', 'Ï': 'i',
                       'μ': 'u', 'µ': 'u', '%': 'percentage'}
DEFAULT_FILTERSTR = ['gefiltreerd', 'na filtratie', 'filtered', 'filtration', ' gef', 'filtratie']                           

DEFAULT_MINSCORES = {1: 100, 3: 100, 4: 90, 5: 85, 6: 80, 8: 75}

DEFAULT_STR2REMOVE = ['icpms', 'icpaes', 'gf aas', 'icp', 'koude damp aas', 'koude damp',  # whitespace, string
                      'berekend', 'opdrachtgever', 'gehalte', 'kretl',
                      'tijdens meting',
                      # 'gefiltreerd', 'na filtratie', 'filtered', 'gef', 'filtratie',
                      'na destructie', 'destructie', 'na aanzuren', 'aanzuren',
                      'bij',  # whitespace, string, whitespace
                     ]
# DEFAULT_UNITS_REGEX_PATTERN = r"^\s*([a-zA-Z]*)\s*([a-zA-Z0-9]*)?\s*[/.,]\s*([a-zA-Z])\s*([a-zA-Z0-9]*)?\s*$"

VALID_METHODS = ['exact', 'ascii', 'regex', 'fuzzy', 'pubchem']

DEFAULT_RE_DICT0 = {'num': ["[a-zA-Z]*", "\s*"],
                    'gfw0': ["[a-zA-Z0-9]*", "?\s*"],
                    'div': ["[/.,]", "\s*"],
                    'den0': ["[0-9]*", "?"],
                    'den1': ["[a-zA-Z]*", "\s*"],
                    'gfw1': ["[a-zA-Z0-9]*", "?"],
                   }
DEFAULT_RE_DICT1 = {'txt': ["[a-zA-Z]*", ""]}

def dict2str(groupdict):
    n = groupdict['num']
    d0 = groupdict['den0']
    d1 = groupdict['den1']
    rv = f"" 
    if not any(x is None for x in [n, d0, d1]):

        if len(n):
            rv += f"{n} / "
        else:
            rv += f"1 / "
        if len(d0):
            rv += f"({d0}"
        else:
            rv += f"(1"
        if len(d1):
            rv += f"{d1})"
        else:
            rv += f")"
    return rv

DEFAULT_UNITS_REGEX_MAP = RegexMapper(DEFAULT_RE_DICT0, 
                                      DEFAULT_RE_DICT1, 
                                      func=dict2str)

class MapperDict(UserDict):
    @classmethod
    def from_file(cls, fname):
        with open(fname, 'r') as fp:
            return cls(json.load(fp))

    def to_file(self, fname):
        with open(fname, 'w') as fp:
            json.dump(self.data, fp, indent=2)
class Mapper(object):
    """
    Class for importing hydrochemical data in a variety of formats

    Examples
    --------

    TBC::
    """

    def __init__(self,
                 m_dict=None,
                 match_method=None,
                 minscores=None,
                 regex_map=DEFAULT_UNITS_REGEX_MAP,
                 replace_strings=None,
                 remove_strings=None,
                 strip_parentheses=False,
                ):
        """
        Parameters
        ----------
            trim_duplicate_suffixes: bool
                If True, the suffixes added to column headers by the pandas functions
                read_csv and read_excel will be trimmed from the elements in strings.
        """

        self.m_dict = m_dict
        self.match_method = match_method or VALID_METHODS
        self.minscores = minscores or DEFAULT_MINSCORES
        self.strip_parentheses = strip_parentheses
        self.regex_map = regex_map
        self.replace_strings = replace_strings or DEFAULT_STR2REPLACE
        self.remove_strings = remove_strings or DEFAULT_STR2REMOVE
        self.match_method = check_arg_list(self.match_method, VALID_METHODS)

    def _match_exact(self, strings, m_dict):
        return [m_dict.get(s) for s in strings]

    def _match_regex(self, strings):
        regex_match = re.compile(self.regex_map.RE)
        matches = [regex_match.match(s) for s in strings]
        return [self.regex_map.str(m.groupdict()) if m else None for m in matches]

    def _match_fuzzy(self, strings, m_dict):
        fuzzy_score = lambda s: fwp.extractOne(s, 
                                               list(m_dict.keys()),
                                               scorer=fwf.token_sort_ratio,
                                               score_cutoff=80,
                                              )
        scores = [fuzzy_score(s) for s in strings]
        return [m_dict.get(s[0]) if s else None for s in scores]

    def match(self,
              s_dict,
              match_key,
              writer,
             ):
        """
        
        Parameters
        ----------
        """

        try:
            strings = StringList([v[match_key] for v in s_dict.values()])
        except TypeError:
            raise TypeError("Argument 's_dict' is not of type dict")

        df = pd.DataFrame({'Header': s_dict.keys(),
                           'original': strings})

        strings.replace_strings(self.replace_strings)
        strings.replace_strings({k: '' for k in self.remove_strings})
        df['modified'] = strings

        # Check if 'ascii' or 'fuzzy' were passed
        if any([m in ['ascii', 'fuzzy'] for m in self.match_method]): 
            strings_t = StringList(strings)
            strings_t.tidy_strings()

            keys_t = StringList(self.m_dict.keys())
            keys_t.replace_strings(self.replace_strings)
            keys_t.replace_strings({k: '' for k in self.remove_strings})
            keys_t.tidy_strings()
            m_dict_t = {k1: self.m_dict.get(k0) for k0, k1 in zip(self.m_dict, keys_t)}

            df['tidied'] = strings_t

        df['match'] = np.nan # Stores the item that was matched
        df['alias'] = np.nan # Stores the alias of the matched item
        df['method'] = np.nan # Stores the method with which a match was found
        
        # Copy only relevant columns from main df to dfsub. List comprehension
        # is necessary to make a selection because 'tidied' may not occur in the
        # main df if the method is not 'ascii' or 'fuzzy'
        cols = [c for c in ['modified', 'tidied', 'match'] if c in df.columns]
        for m in self.match_method:
            try:
                # Select only the rows for which no match was found yet
                idx = df['alias'].isnull()
                dfsub = df.loc[idx, cols].copy()
                # The term to be matched depends on the method
                if m in ['exact', 'regex']:
                    dfsub['match'] = dfsub['modified']
                else:
                    dfsub['match'] = dfsub['tidied']
                # Call the appropriate match method (a bit verbose for readability)
                if (m == 'exact'):
                    res = self._match_exact(dfsub['match'], self.m_dict)
                elif (m == 'ascii'):
                    res = self._match_exact(dfsub['match'], m_dict_t)
                elif (m == 'regex'):
                    res = self._match_regex(dfsub['match'])
                elif (m == 'fuzzy'):
                    res = self._match_fuzzy(dfsub['match'], m_dict_t)
                else:
                    raise NotImplementedError
                
                # Store the aliases of the matched values in 'alias' column
                dfsub['alias'] = res
                # Only place method in 'method' column if an alias was found
                idx = ~dfsub['alias'].isnull()
                dfsub.loc[idx, 'method'] = m
                # Update the main df with the values in dfsub
                df.update(dfsub)
            except NotImplementedError:
                raise NotImplementedError(f"Match method '{m}' not implemented")

        if writer:
            df.to_excel(writer, sheet_name=match_key.capitalize())

        rv = {}
        for key, value in df.set_index('Header').to_dict('index').items():
            rv[key] = {k: v for k, v in value.items()}

        return rv