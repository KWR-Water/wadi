from collections import UserList
import fuzzywuzzy.fuzz as fwf
import fuzzywuzzy.process as fwp
import pandas as pd
import re

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
DEFAULT_UNITS_REGEX_PATTERN = r"^\s*([a-zA-Z]*)\s*([a-zA-Z0-9]*)?\s*[/.,]\s*([a-zA-Z])\s*([a-zA-Z0-9]*)?\s*$"

VALID_METHODS = ['exact', 'ascii', 'regex', 'fuzzy', 'pubchem']

class StringList(UserList):
    def replace_strings(self, r_dict):
        if not isinstance(r_dict, dict):
            raise TypeError("Argument 'r_dict' must be of type dict")
        try:
            for key, value in r_dict.items():
                self.data = [s.replace(key, value) for s in self.data]
        except:
            pass

    def strip_parentheses(self):
        self.data = [re.sub('\(.*\)', '', s) for s in self.data]

    def tidy_strings(self):
        self.data = [s.lower() for s in self.data]
        self.data = [s.encode('ascii', 'ignore').decode('ascii') for s in self.data]
        self.data = [re.sub('[^0-9a-zA-Z\s]', '', s) for s in self.data]


class Mapper(object):
    """
    Class for importing hydrochemical data in a variety of formats

    Examples
    --------

    TBC::
    """

    def __init__(self,
                 map=None,
                 match_method=None,
                 minscores=None,
                 regex_pattern=DEFAULT_UNITS_REGEX_PATTERN, # str, immutable
                 replace_strings=None,
                 remove_strings=None,
                 strip_parentheses=False,
                #  trim_duplicate_suffixes=None,
                ):
        """
        Parameters
        ----------
            trim_duplicate_suffixes: bool
                If True, the suffixes added to column headers by the pandas functions
                read_csv and read_excel will be trimmed from the elements in strings.
        """
        self.df = pd.DataFrame()
        self.map = map
        self.match_method = match_method or VALID_METHODS
        self.minscores = minscores or DEFAULT_MINSCORES
        self.strip_parentheses = strip_parentheses
        self.regex_pattern = regex_pattern
        self.replace_strings = replace_strings or DEFAULT_STR2REPLACE
        self.remove_strings = remove_strings or DEFAULT_STR2REMOVE
        # self.trim_duplicate_suffixes = trim_duplicate_suffixes or True

    @staticmethod
    def _check_methods(methods):
        """
        """

        if isinstance(methods, str):
            methods = [methods]
    
        rv = []
        try:
            methods = [m.lower() for m in methods]
            for m in methods:
                idx = [s.find(m) for s in VALID_METHODS].index(0)
                rv.append(VALID_METHODS[idx])
        except ValueError:
            raise ValueError(f'invalid method argument: {m}, must be in {VALID_METHODS}')

        return rv
    
    def _match_exact(self, strings, map):
        self.df['Exact'] = [map.get(s) for s in strings]

    def _match_ascii(self, strings, map):
        self.df['ASCII'] = [map.get(s) for s in strings]

    def _match_regex(self, strings, map):
        regex_match = lambda s: re.match(self.regex_pattern, s)
        matches = [regex_match(s) for s in strings]
        self.df['Regex'] = [m.group(0) if m else None for m in matches]

    def _match_fuzzy(self, strings, map):
        fuzzy_score = lambda s: fwp.extractOne(s, 
                                               list(map.keys()),
                                               scorer=fwf.token_sort_ratio,
                                               score_cutoff=80,
                                              )
        scores = [fuzzy_score(s) for s in strings]
        self.df['Fuzzy'] = [map.get(s[0]) if s else None for s in scores]


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

        self.df = pd.DataFrame({'Header': s_dict.keys(),
                                'Match_string': strings})

        strings.replace_strings(self.replace_strings)
        strings.replace_strings({k: '' for k in self.remove_strings})
        self.df['Match_string_modified'] = strings

        # Check if any other match methods besides 'exact' or 'regex' were passed
        if any([m not in ['exact', 'regex'] for m in self.match_method]): 
            strings_t = StringList(strings)
            strings_t.tidy_strings()

            keys_t = StringList(self.map.keys())
            keys_t.replace_strings(self.replace_strings)
            keys_t.replace_strings({k: '' for k in self.remove_strings})
            keys_t.tidy_strings()
            map_t = {k1: self.map.get(k0) for k0, k1 in zip(self.map, keys_t)}

            self.df['Match_string__tidied'] = strings_t

        for m in self.match_method:
            try:
                match_method = getattr(self, f'_match_{m}')
                if (m in ['exact', 'regex']):
                    match_method(strings, self.map)
                else:
                    match_method(strings_t, map_t)
            except AttributeError:
                pass

        if writer:
            self.df.to_excel(writer, sheet_name=match_key.capitalize())

        rv = {}
        for key, value in self.df.set_index('Header').to_dict('index').items():
            rv[key] = {k: v for k, v in value.items()}

        return rv