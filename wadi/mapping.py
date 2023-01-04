from collections import UserDict
import fuzzywuzzy.fuzz as fwf
import fuzzywuzzy.process as fwp
import json
import numpy as np
import pandas as pd
from pathlib import Path
import re

from wadi.base import WadiChildClass
from wadi.utils import StringList, check_arg_list, fuzzy_min_score
from wadi.api_utils import (
    query_pubchem_fuzzy,
    query_pubchem_cas,
    query_pubchem_synonyms,
)
from wadi.regex import UnitRegexMapper

DEFAULT_STR2REPLACE = {
    "Ä": "a",
    "ä": "a",
    "Ë": "e",
    "ë": "e",
    "Ö": "o",
    "ö": "o",
    "ï": "i",
    "Ï": "i",
    "μ": "u",
    "µ": "u",
    "%": "percentage",
}
DEFAULT_FILTERSTR = [
    "gefiltreerd",
    "na filtratie",
    "filtered",
    "filtration",
    " gef",
    "filtratie",
]

DEFAULT_STR2REMOVE = [
    "icpms",
    "icpaes",
    "gf aas",
    "icp",
    "koude damp aas",
    "koude damp",  # whitespace, string
    "berekend",
    "opdrachtgever",
    "gehalte",
    "kretl",
    "tijdens meting",
    # 'gefiltreerd', 'na filtratie', 'filtered', 'gef', 'filtratie',
    "na destructie",
    "destructie",
    "na aanzuren",
    "aanzuren",
    "bij",  # whitespace, string, whitespace
]

VALID_METHODS = ["exact", "ascii", "regex", "fuzzy", "pubchem"]


class MapperDict(UserDict):
    @classmethod
    def from_file(cls, fname):
        with open(fname, "r") as fp:
            return cls(json.load(fp))

    @classmethod
    def default_dict(cls, v0, v1):
        # Get the path of the current module file's parent directory
        filepath = Path(__file__).parents[1]
        dfj = pd.read_json(Path(filepath, "default_feature_map.json"))
        dfd = dfj[[v0, v1]].explode(v0).dropna()
        return cls(dfd.set_index(v0)[v1].to_dict())

    @classmethod
    def pubchem_cas_dict(cls, strings):
        return cls({s: query_pubchem_cas(s) for s in strings})

    @classmethod
    def pubchem_cid_dict(cls, strings):
        rv = {}
        for s in strings:
            res = query_pubchem_synonyms(s)
            # print(s)
            if len(res):
                rv[s] = res[0]["CID"]
            else:
                rv[s] = None
        return cls(rv)
        # return {s: query_pubchem_cid(s) for s in strings}

    def to_file(self, fname):
        with open(fname, "w") as fp:
            json.dump(self.data, fp, indent=2)

    def translate(
        self,
        src_lang="NL",
        dst_lang="EN",
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
                keys_dst = t.translate(keys_src, src=src_lang, dest=dst_lang)
                # return {k: v for k, v in zip(keys_dst, self.data.values())}
            except:
                print(
                    f"Failed attempt ({i}) to connect to Google Translate API. Retrying..."
                )

        if i == (max_attempts - 1):
            raise ValueError("Translation failed. Try again later...")


class Mapper(WadiChildClass):
    """
    Class for mapping hydrochemical data

    Examples
    --------

    TBC::
    """

    def __init__(
        self,
        converter,
        s,
        #  m_dict=None,
        #  match_method=None,
        #  minscores=None,
        #  regex_map=UnitRegexMapper(),
        #  replace_strings=None,
        #  remove_strings=None,
        #  strip_parentheses=False,
        #  allow_empty_aliases=False,
    ):
        """
        Parameters
        ----------
        s : str
            The value of s is either 'name' (when called by map_data) or
            'unit' (when called by map_units), which are valid keys for the
            dicts stored in the infotable.
        """

        super().__init__(converter)

        self.s = s
        self.xl_fname = Path(
            self.converter.output_dir,
            f"{s}_mapping_results_{self.converter.log_fname.stem}.xlsx",
        )

        self.m_dict = None
        self.match_method = ["exact"]
        self.strip_parentheses = False
        self.regex_map = UnitRegexMapper()
        self.replace_strings = DEFAULT_STR2REPLACE
        self.remove_strings = DEFAULT_STR2REMOVE
        self.allow_empty_aliases = False

        # self.df = {}

    def __call__(
        self,
        m_dict=None,
        match_method=None,
        regex_map=UnitRegexMapper(),
        replace_strings=None,
        remove_strings=None,
        strip_parentheses=False,
        allow_empty_aliases=False,
    ):

        if self.s == "name":
            self.match_method = match_method or ["exact"]
        elif self.s == "unit":
            self.match_method = match_method or ["regex"]
        self.match_method = check_arg_list(self.match_method, VALID_METHODS)

        if isinstance(m_dict, dict):
            self.m_dict = MapperDict(m_dict)
        else:
            self.m_dict = m_dict

        self.strip_parentheses = strip_parentheses
        self.regex_map = regex_map
        self.replace_strings = replace_strings or DEFAULT_STR2REPLACE
        self.remove_strings = remove_strings or DEFAULT_STR2REMOVE
        self.allow_empty_aliases = allow_empty_aliases

        # Call the match method. Passes the keys of the infotable along with
        # a list of strings which contains either the 'name' or 'unit' values
        # of all the items in infotable
        self._match(
            # self._infotable.keys(),
            # self._infotable.list(self.s),
        )

        # # Write the DataFrame with the mapping summary to an Excel file
        # fname = Path(OUTPUT_DIR, f"{s}_mapping_results_{self._log_fname.stem}.xlsx")
        # m.df2excel(fname,
        #            f"{s.capitalize()}s")

        # # Transfer the aliases found by match to the infotable
        # # The key will be either alias_n or alias_u
        # i_key = f"alias_{s[0]}"
        # # Convert the alias column to a dictionary, the keys will be
        # # the values in the header column (which correspond to the keys
        # # of the infotable)
        # a_dict = m.df.set_index('header')['alias'].to_dict()

        # # Loop over the new dict with the aliases and tranfer the results
        # # into the infotable
        # for key, value in a_dict.items():
        #     self._infotable[key][i_key] = value

    def _default_m_dict(self, strings):
        return {k: k for k in dict.fromkeys(strings)}

    def _match_exact(self, strings, m_dict):
        return [[s, m_dict.get(s)] for s in strings]

    def _match_regex(self, strings):
        regex_match = re.compile(self.regex_map.RE)
        matches = [regex_match.match(s) for s in strings]
        return [
            [None, self.regex_map.str(m.groupdict())] if m else [None, None]
            for m in matches
        ]

    def _match_fuzzy(self, strings, m_dict):
        fuzzy_score = lambda s: fwp.extractOne(
            s,
            list(m_dict.keys()),
            scorer=fwf.token_sort_ratio,
            score_cutoff=fuzzy_min_score(s),
        )
        scores = [fuzzy_score(s) for s in strings]
        return [[s, m_dict.get(s[0])] if s else [None, None] for s in scores]

    def _match_pubchem(self, strings):
        return [query_pubchem_fuzzy(s) for s in strings]

    def _match(
        self,
        #   columns,
        #   strings,
    ):
        """

        Parameters
        ----------
        """

        self._log(f"{self.s.capitalize()} mapping...")

        columns = self.converter._infotable.keys()
        strings = StringList(self.converter._infotable.list(self.s))
        # try:
        #     columns = self.parent._infotable.keys()
        #     strings = StringList(self.parent._infotable.list(self.s))
        # except:
        #     TypeError("Not a valid type")

        if self.m_dict is None:
            self.m_dict = self._default_m_dict(strings)

        df = pd.DataFrame({"header": columns, "name": strings})

        strings.replace_strings(self.replace_strings)
        strings.replace_strings({k: "" for k in self.remove_strings})
        df["modified"] = strings

        # Check if 'ascii' or 'fuzzy' were passed
        if any([m in ["ascii", "fuzzy"] for m in self.match_method]):
            strings_t = StringList(strings)
            strings_t.tidy_strings()

            keys_t = StringList(self.m_dict.keys())
            keys_t.replace_strings(self.replace_strings)
            keys_t.replace_strings({k: "" for k in self.remove_strings})
            keys_t.tidy_strings()
            m_dict_t = {k1: self.m_dict.get(k0) for k0, k1 in zip(self.m_dict, keys_t)}

            df["tidied"] = strings_t

        df["searched"] = np.nan  # Stores the item that was searched
        df["found"] = np.nan  # Stores the item that was matched
        df["alias"] = np.nan  # Stores the alias of the matched item
        df["method"] = np.nan  # Stores the method with which a match was found

        # Copy only relevant columns from df to dfsub. List comprehension
        # is necessary to make a selection because 'tidied' may not occur in
        # df if the method is not 'ascii' or 'fuzzy'
        cols = [
            c
            for c in ["name", "modified", "tidied", "searched", "found"]
            if c in df.columns
        ]
        for m in self.match_method:
            try:
                # Select only the rows for which no match was found yet
                idx = df["alias"].isnull()
                dfsub = df.loc[idx, cols].copy()
                # The term to be matched depends on the method
                if m in ["exact", "regex", "pubchem"]:
                    dfsub["searched"] = dfsub["modified"]
                else:
                    dfsub["searched"] = dfsub["tidied"]
                # Call the appropriate match method (a bit verbose for readability)
                if m == "exact":
                    res = self._match_exact(dfsub["searched"], self.m_dict)
                elif m == "ascii":
                    res = self._match_exact(dfsub["searched"], m_dict_t)
                elif m == "regex":
                    res = self._match_regex(dfsub["searched"])
                elif m == "fuzzy":
                    res = self._match_fuzzy(dfsub["searched"], m_dict_t)
                elif m == "pubchem":
                    res = self._match_pubchem(dfsub["searched"])
                else:
                    raise NotImplementedError

                # Store the aliases of the matched values in 'alias' column
                dfsub[["found", "alias"]] = res
                # dfsub['alias'] = res[1]
                # Only place method in 'method' column if an alias was found
                idx = ~dfsub["alias"].isnull()
                dfsub.loc[idx, "method"] = m
                # Update the main df with the values in dfsub
                df.update(dfsub)

                self._log(f" * Match method {m} found the following matches:")
                for name, alias in zip(dfsub["name"], dfsub["alias"]):
                    if alias is not None:
                        self._log(f"   - {name}: {alias}")

            except NotImplementedError:
                raise NotImplementedError(f"Match method '{m}' not implemented")

        if not self.allow_empty_aliases:
            idx = df["alias"].isnull()
            df.loc[idx, "alias"] = df.loc[idx, "modified"].array
            df.loc[idx, "found"] = ""

        # Write the DataFrame with the mapping summary to an Excel file
        sheet_name = f"{self.s.capitalize()}s"
        # self._df2excel(fname,
        #     f"{self.s.capitalize()}s")
        df.to_excel(
            self.xl_fname,
            sheet_name=sheet_name,
            index=False,
        )

        # Transfer the aliases found by match to the convertor's infotable
        # The key will be either alias_n or alias_u
        i_key = f"alias_{self.s[0]}"
        # Convert the alias column to a dictionary, the keys will be
        # the values in the header column (which correspond to the keys
        # of the convertor's infotable)
        a_dict = df.set_index("header")["alias"].to_dict()

        # Loop over the new dict with the aliases and tranfer the results
        # into the infotable
        for key, value in a_dict.items():
            self.converter._infotable[key][i_key] = value

        # Write the logged messages to the log file
        self.update_log_file()

    # def _df2excel(self,
    #              xl_fname,
    #              sheet_name):

    #     writer = pd.ExcelWriter(xl_fname)

    #     self.df.to_excel(writer,
    #                      sheet_name=sheet_name,
    #                      index=False,
    #                     )

    #     writer.save()
