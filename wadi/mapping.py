from collections import UserDict
import fuzzywuzzy.fuzz as fwf
import fuzzywuzzy.process as fwp
import json
import numpy as np
import os
import pandas as pd
import re
from wadi.base import WadiBaseClass
from wadi.utils import StringList, check_arg_list, query_pubchem
from wadi.regex import UnitRegexMapper

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

VALID_METHODS = ['exact', 'ascii', 'regex', 'fuzzy', 'pubchem']

class MapperDict(UserDict):
    @classmethod
    def from_file(cls, fname):
        with open(fname, 'r') as fp:
            return cls(json.load(fp))

    @classmethod
    def default_dict(cls, v0, v1):
        dfj = pd.read_json('D:/Users/postvi/Documents/github/wadi/default_feature_map.json')
        dfd = dfj[[v0, v1]].explode(v0).dropna()
        return dfd.set_index(v0)[v1].to_dict()

    def to_file(self, fname):
        with open(fname, 'w') as fp:
            json.dump(self.data, fp, indent=2)
    
    def translate(self,
                  src_lang='NL', 
                  dst_lang='EN',
                  max_attempts=10,
                 ):
        try:
            from googletrans import LANGUAGES, Translator
        except ImportError:
            raise ImportError("Package 'googletrans' not installed")

        t = Translator()

        if not all([l.lower() in LANGUAGES for l in [src_lang, dst_lang]]):
            raise ValueError("Invalid language(s) specified")    

        keys_src = list(self.data.keys())
        for i in range(max_attempts):
            try:
                keys_dst = t.translate(keys_src, 
                                       src=src_lang, 
                                       dest=dst_lang
                                      )
                #return {k: v for k, v in zip(keys_dst, self.data.values())}
            except:
                print(f"Failed attempt ({i}) to connect to Google Translate API. Retrying...")

        if (i == (max_attempts - 1)):
            raise ValueError("Translation failed. Try again later...")

class Mapper(WadiBaseClass):
    """
    Class for mapping hydrochemical data

    Examples
    --------

    TBC::
    """

    def __init__(self,
                 m_dict=None,
                 match_method=None,
                 minscores=None,
                 regex_map=UnitRegexMapper(),
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

        WadiBaseClass.__init__(self)

        self.m_dict = m_dict
        self.match_method = match_method or ['exact']
        self.minscores = minscores or DEFAULT_MINSCORES
        self.strip_parentheses = strip_parentheses
        self.regex_map = regex_map
        self.replace_strings = replace_strings or DEFAULT_STR2REPLACE
        self.remove_strings = remove_strings or DEFAULT_STR2REMOVE
        self.match_method = check_arg_list(self.match_method, VALID_METHODS)

        self.df = {}

    def _default_m_dict(self, strings):
        return {k: k for k in  dict.fromkeys(strings)}

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

    def _match_pubchem(self, strings):
        return [query_pubchem(s) for s in strings]

    def match(self,
              columns,
              strings,
              s,
             ):
        """
        
        Parameters
        ----------
        """

        self._log("Mapping...")
        
        try:
            strings = StringList(strings)
        except:
            TypeError("Argument 'strings' is not of a valid type")

        if self.m_dict is None:
            self.m_dict = self._default_m_dict(strings)
        
        self.df = pd.DataFrame({'header': columns,
                                'name': strings})

        strings.replace_strings(self.replace_strings)
        strings.replace_strings({k: '' for k in self.remove_strings})
        self.df['modified'] = strings

        # Check if 'ascii' or 'fuzzy' were passed
        if any([m in ['ascii', 'fuzzy'] for m in self.match_method]): 
            strings_t = StringList(strings)
            strings_t.tidy_strings()

            keys_t = StringList(self.m_dict.keys())
            keys_t.replace_strings(self.replace_strings)
            keys_t.replace_strings({k: '' for k in self.remove_strings})
            keys_t.tidy_strings()
            m_dict_t = {k1: self.m_dict.get(k0) for k0, k1 in zip(self.m_dict, keys_t)}

            self.df['tidied'] = strings_t

        self.df['match'] = np.nan # Stores the item that was matched
        self.df['alias'] = np.nan # Stores the alias of the matched item
        self.df['method'] = np.nan # Stores the method with which a match was found
        
        # Copy only relevant columns from self.df to dfsub. List comprehension
        # is necessary to make a selection because 'tidied' may not occur in 
        # self.df if the method is not 'ascii' or 'fuzzy'
        cols = [c for c in ['name', 'modified', 'tidied', 'match'] if c in self.df.columns]
        for m in self.match_method:
            try:
                # Select only the rows for which no match was found yet
                idx = self.df['alias'].isnull()
                dfsub = self.df.loc[idx, cols].copy()
                # The term to be matched depends on the method
                if m in ['exact', 'regex', 'pubchem']:
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
                elif (m == 'pubchem'):
                    res = self._match_pubchem(dfsub['match'])
                else:
                    raise NotImplementedError
                
                # Store the aliases of the matched values in 'alias' column
                dfsub['alias'] = res
                # Only place method in 'method' column if an alias was found
                idx = ~dfsub['alias'].isnull()
                dfsub.loc[idx, 'method'] = m
                # Update the main df with the values in dfsub
                self.df.update(dfsub)

                self._log(f" * Match method {m} found the following matches:")
                for name, alias in zip(dfsub['name'], dfsub['alias']):
                    if alias is not None:
                        self._log(f"   - {name}: {alias}")
            
            except NotImplementedError:
                raise NotImplementedError(f"Match method '{m}' not implemented")

        idx = self.df['alias'].isnull()
        self.df.loc[idx, 'alias'] = self.df.loc[idx, 'modified'].array
        self.df.loc[idx, 'match'] = ''

    def df2excel(self,
                 xl_fname,
                 sheet_name):

        writer = pd.ExcelWriter(xl_fname)

        self.df.to_excel(writer, 
                         sheet_name=sheet_name,
                         index=False,
                        )
        
        writer.save()