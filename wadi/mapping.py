import fuzzywuzzy.fuzz as fwf
import fuzzywuzzy.process as fwp
import pandas as pd
import re

REQUIRED_HEADERS_S = ['Feature', 'Value', 'Unit'] #, 'SampleId']
DEFAULT_HEADER_MAP_S = {s: s for s in REQUIRED_HEADERS_S}
REQUIRED_HEADERS_W = []
DEFAULT_HEADER_MAP_W = {s: s for s in REQUIRED_HEADERS_W}

DEFAULT_STR2REPLACE = {'Ä': 'a', 'ä': 'a', 'Ë': 'e', 'ë': 'e',
                       'Ö': 'o', 'ö': 'o', 'ï': 'i', 'Ï': 'i',
                       'μ': 'u', 'µ': 'u', '%': 'percentage'}
DEFAULT_FILTERSTR = ['gefiltreerd', 'na filtratie', 'filtered', 'filtration', ' gef', 'filtratie']                           

DEFAULT_STR2REMOVE = ['icpms', 'icpaes', 'gf aas', 'icp', 'koude damp aas', 'koude damp',  # whitespace, string
                      'berekend', 'opdrachtgever', 'gehalte', 'kretl',
                      'tijdens meting',
                      # 'gefiltreerd', 'na filtratie', 'filtered', 'gef', 'filtratie',
                      'na destructie', 'destructie', 'na aanzuren', 'aanzuren',
                      'bij',  # whitespace, string, whitespace
                     ]

VALID_METHODS = ['exact', 'ascii', 'fuzzy', 'pubchem']

class Mapper(object):
    """
    Class for importing hydrochemical data in a variety of formats

    Examples
    --------

    TBC::
    """

    def __init__(self,
                 map=DEFAULT_HEADER_MAP_S,
                 match_method=VALID_METHODS,
                 minscores={1: 100, 3: 100, 4: 90, 5: 85, 6: 80, 8: 75},
                 replace_strings=DEFAULT_STR2REPLACE,
                 remove_strings=DEFAULT_STR2REMOVE,
                 strip_parentheses=False,
                 trim_duplicate_suffixes=True,
                ):
        """
        Parameters
        ----------
            trim_duplicate_suffixes: bool
                If True, the suffixes added to column headers by the pandas functions
                read_csv and read_excel will be trimmed from the elements in strings.
        """
        self.df = {}
        self.map = map
        self.match_method = self._check_method(match_method)
        self.minscores = minscores
        self.strip_parentheses = strip_parentheses
        self.replace_strings = replace_strings
        self.remove_strings = remove_strings
        self.trim_duplicate_suffixes = trim_duplicate_suffixes

    @staticmethod
    def _check_method(methods):
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

    def _match_fuzzy(self, strings, map):
        score = lambda s: fwp.extractOne(s, 
                                         list(map.keys()),
                                         scorer=fwf.token_sort_ratio,
                                         score_cutoff=80,
                                        )
        scores = [score(s) for s in strings]
        self.df['Fuzzy'] = [map.get(s[0]) if s is not None else None for s in scores]

    @staticmethod
    def _replace_strings(strings, r_dict):
        """
        Function to replace strings in the elements of an iterable.

        Function proceeds in three steps to keep the code readable
        """
        if not isinstance(r_dict, dict):
            raise TypeError("Argument 'r_dict' must be of type dict")
        try:
            rv = list(strings)
            for key, value in r_dict.items():
                rv = [s.replace(key, value) for s in rv]
        except:
            pass

        return rv

    @staticmethod
    def _strip_parentheses(strings):
        return [re.sub('\(.*\)', '', s) for s in strings]

    def _tidy_strings(self, strings):
        rv = self._replace_strings(strings, self.replace_strings)
        rv = self._replace_strings(rv, {k: '' for k in self.remove_strings})
        rv = [s.lower() for s in rv]
        rv = [s.encode('ascii', 'ignore').decode('ascii') for s in rv]
        rv = [re.sub('[^0-9a-zA-Z\s]', '', s) for s in rv]

        return rv

    @staticmethod
    def _trim_duplicate_suffixes(strings):
        """
        Function to remove the suffixes added by the pandas reader
        functions like read_csv and read_excel when duplicate columns
        are encountered.

        Function proceeds in three steps to keep the code readable
        """
        # First use list comprehension with a regular expression search
        # to find trailing (hence the $ sign) integers (the \d+ part)
        # preceded by a dot (the \.) in strings (an iterable). Note
        # that re.search returns a match object, or None if the 
        # expression was not found
        res = [re.search('\.\d+$', s) for s in strings]
        
        # Use the group function of the match objects in res to get 
        # the trailing string (for example '.1'). Store an empty string
        # for the elements in strings for which the expression was
        # not found
        matches = [r.group() if r is not None else '' for r in res]

        # Return the strings with the trailing parts removed by calling
        # the removesuffix function (requires Python 3.9 or higher)
        return [s.removesuffix(m) for s, m in zip(strings, matches)]

    def map_strings(self,
                    strings,
                    ):
        """
        
        Parameters
        ----------
        """

        if isinstance(strings, str):
            strings = [strings]
        
        try:
            # Use list to create a copy of strings if it is of type list,
            # or cast to list type if strings is another iterable type
            strings = list(strings)
        except TypeError:
            raise TypeError("Argument 'strings' is not an iterable")

        self.df = pd.DataFrame({'Headers': strings})

        if self.trim_duplicate_suffixes:
            strings = self._trim_duplicate_suffixes(strings)

        # Check if any other match methods besides 'exact' were passed
        if len([m for m in self.match_method if m != 'exact']): 
            strings_t = self._tidy_strings(strings)
            self.df['Headers_tidied'] = strings_t

            keys_t = self._tidy_strings(self.map)
            map_t = {k1: self.map.get(k0) for k0, k1 in zip(self.map, keys_t)}

        for m in self.match_method:
            try:
                match_method = getattr(self, f'_match_{m}')
                if (m == 'exact'):
                    match_method(strings, self.map)
                else:
                    match_method(strings_t, map_t)

                print(self.df)
            except AttributeError:
                pass
