from collections import UserDict
import json
import numpy as np
import pandas as pd
from pathlib import Path
import re

import fuzzywuzzy.fuzz as fwf
import fuzzywuzzy.process as fwp

from wadi.base import WadiBaseClass
from wadi.utils import StringList, check_arg_list, fuzzy_min_score
from wadi.api_utils import (
    translate_strings,
    query_pubchem_fuzzy,
    query_pubchem_cas,
    query_pubchem_synonyms,
)
from wadi.unitconverter import UnitRegexMapper

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
    "°C": "degC",
    "°F": "degF",
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

VALID_MATCH_METHODS = ["exact", "ascii", "regex", "fuzzy", "pubchem"]


class MapperDict(UserDict):
    """
    Instances of this class are meant to be used as dictionaries
    that translate names and units into their aliases. It derives
    from the UserDict wrapper to extend the functionality of a
    regular Python dict with some class methods to create an
    instance from json files or PubChem queries. The dictionary
    can also be saved to a json file and it contains a translate
    method to create a dictionary that translates between languages
    (currently not working due to issues with Google Translate).
    """

    @classmethod
    def from_file(cls, file_path):
        """
        This method initializes the class by reading a dictionary
        from a json file.

        Parameters
        ----------
        file_path : str
            The json file to be read.

        Returns
        ----------
        result : class instance
            An instance of the UserDict class containing the
            imported data.
        """
        with open(file_path, "r") as fp:
            return cls(json.load(fp))

    @classmethod
    def default_dict(cls, keys, values):
        """
        This method initializes the class by reading a dictionary
        from the file default_feature_map.json. The function
        arguments are the column names that should become the
        dictionary keys and values, respectively.

        Parameters
        ----------
        keys : str
            The name of the column whose values should become
            the dictionary keys.
        values : str
            The name of the column whose values should become
            the dictionary values.

        Returns
        ----------
        result : class instance
            An instance of the UserDict class containing the
            imported data.
        """
        # The json file resides in the parent directory of the
        # current module's py file. The __file__ attribute returns
        # the pathname of the current py file and .parent
        # provides its parent directory.
        filepath = Path(__file__).parent
        # Import the file into a DataFrame.
        dfj = pd.read_json(Path(filepath, "default_feature_map.json"))
        # Use the DataFrame's explode function to transform any keys
        # that are a list (or list-like) into a row. The corresponding
        # value is duplicated for each list element that becomes a row.
        dfd = dfj[[keys, values]].explode(keys).dropna()
        # Convert the DataFrame to a dictionary
        rv_dict = dfd.set_index(keys)[values].to_dict()
        # Values are lists, gives problems when they become aliases so
        # keep only first list element if there are multiple.
        rv_dict = {k: str(v[0]) for k, v in rv_dict.items()}
        return cls(rv_dict)

    @classmethod
    def _create_hgc_units_dict(cls):
        """
        This method initializes the class by reading the csv
        files in the folder hgc_constants, which contain
        the feature names and their target units.

        Returns
        ----------
        result : class instance
            An instance of the UserDict class containing the
            imported data.
        """

        rv_dict = {}
        filepath = Path(Path(__file__).parents[1], "hgc_constants")
        for fname in ["atoms.csv", "ions.csv", "other_than_concentrations.csv"]:
            df = pd.read_csv(Path(filepath, fname), comment='#')
            rv_dict = {**rv_dict, **df.set_index("feature")["unit"].to_dict()}

        return cls(rv_dict)

    @classmethod
    def pubchem_cas_dict(
        cls,
        strings,
        src_lang=None,
        max_attempts=10,
    ):
        """
        This method creates a dictionary with CAS numbers for the
        names in 'strings' using the PubChem REST API.

        Parameters
        ----------
        strings : list or list-like
            A list of the names that should be looked up.
        src_lang : str, optional
            String that specifies the original language of the names
            in 'strings. Default: None.
        max_attempts : int, optional
            The maximum number of attempts to connect to the Google
            Translate API. Default: 10.

        Returns
        ----------
        result : class instance
            An instance of the UserDict class in which the elements
            of 'strings' are the keys and the CAS numbers the values.
            An empty dictionary is returned if translation of the
            strings failed for some reason.
        """
        # Convert 'strings' into a list just in case a single string
        # is passed
        strings = list(strings)
        if src_lang is not None:
            translated_keys = translate_strings(strings, src_lang, "EN", max_attempts)
        else:
            translated_keys = strings

        # Start with an empty dict
        rv_dict = {}
        if translated_keys is not None:
            rv_dict = {
                s: query_pubchem_cas(s_en) for s, s_en in zip(strings, translated_keys)
            }

        return cls(rv_dict)

    @classmethod
    def pubchem_cid_dict(
        cls,
        strings,
        src_lang=None,
        max_attempts=10,
    ):
        """
        This method creates a dictionary with CID numbers for the
        names in 'strings' using the PubChem REST API.

        Parameters
        ----------
        strings : list or list-like
            A list of the names that should be looked up.
        src_lang : str, optional
            String that specifies the original language of the names
            in 'strings. Default: None.
        max_attempts : int, optional
            The maximum number of attempts to connect to the Google
            Translate API. Default: 10.

        Returns
        ----------
        result : class instance
            An instance of the UserDict class in which the elements
            of 'strings' are the keys and the CID numbers the values.
            An empty dictionary is returned if translation of the
            strings failed for some reason.
        """
        # Convert 'strings' into a list just in case a single string
        # is passed
        strings = list(strings)
        if src_lang is not None:
            translated_keys = translate_strings(strings, src_lang, "EN", max_attempts)
        else:
            translated_keys = strings

        # Start with an empty dict
        rv_dict = {}
        if translated_keys is not None:
            for s, s_en in zip(strings, translated_keys):
                # Add each element s to the dict
                rv_dict[s] = None
                # Look up the PubChem synonyms
                res = query_pubchem_synonyms(s_en)
                # If a result was returned
                if res is not None:
                    # Look up the key 'CID' in the first element
                    # of the dict that was returned. An IndeXError
                    # may occur if either of the keys '0' or 'CID'
                    # was not returned (in which case rv_dict[s]
                    # remains None).
                    try:
                        rv_dict[s] = res[0]["CID"]
                    except IndexError:
                        pass

        return cls(rv_dict)

    @classmethod
    def translation_dict(
        cls,
        strings,
        src_lang="NL",
        dst_lang="EN",
        max_attempts=10,
    ):
        """
        This method attempts to create a mapping dictionary with
        'strings' being the keys and their translations being the
        values.

        Parameters
        ----------
        strings : list
            List with the strings to translate.
        src_lang : str, optional
            String that specifies the language to translate from.
            Default: "NL".
        dst_lang : str, optional
            String that specifies the language to translate to.
            Default: "EN".
        max_attempts : int, optional
            The maximum number of attempts to connect to the Google
            Translate API. Default: 10.
        """

        translated_keys = translate_strings(strings, src_lang, dst_lang, max_attempts)
        if translated_keys is not None:
            rv_dict = {k: v for k, v in zip(strings, translated_keys)}
            return cls(rv_dict)

    def to_file(self, file_path):
        """
        This method saves the contents of the dictionary as a json
        file.

        Parameters
        ----------
        file_path : str
            The json file to be written.
        """
        with open(file_path, "w") as fp:
            json.dump(self.data, fp, indent=2)

    def translate_keys(
        self,
        src_lang="NL",
        dst_lang="EN",
        max_attempts=10,
    ):
        """
        This method attempts to translate the dictionary keys from
        src_lang to dst_lang using Google Translate.

        Parameters
        ----------
        src_lang : str, optional
            String that specifies the language to translate from.
            Default: "NL".
        dst_lang : str, optional
            String that specifies the language to translate to.
            Default: "EN".
        max_attempts : int, optional
            The maximum number of attempts to connect to the Google
            Translate API. Default: 10.
        """

        translated_keys = translate_strings(
            self.data.keys(), src_lang, dst_lang, max_attempts
        )
        if translated_keys is not None:
            translated_dict = {
                k: v for k, v in zip(translated_keys, self.data.values())
            }
            self.data = translated_dict

    def __str__(self):
        """
        This method provides the string representation of the
        mapping dictionary.

        Returns
        ----------
        result : str
            String that provides an overview of the keys and the values of
            the mapping dictionary.
        """
        max_lines = 10
        rv = f"This dictionary contains {len(self.data)} elements.\n"
        if len(self.data) > max_lines:
            rv += f"Only the first {max_lines} elements are shown.\n"
        rv += (
            f"This mapping dictionary contains the following names and their aliases:\n"
        )
        for i, (key, value) in enumerate(self.data.items()):
            rv += f" - {key} --> {value}\n"
            if i > max_lines:
                break

        return rv


class Mapper(WadiBaseClass):
    """
    WaDI class that implements the operations to map feature names
    and units to their aliases.
    """

    def __init__(
        self,
        key_1,
    ):
        """
        Class initialization method.

        Parameters
        ----------
        key_1 : str
            The value of key_1 is either 'name' or 'unit' depending
            on what needs to be mapped. Note that these names must
            correspond to their respective keys in the dict_1
            elements of the InfoTable, hence the attribute name 'key_1'.
        """
        # Call the ancestor's initialization method to define the
        # generic class attributes and methods.
        super().__init__()

        # Set the key that defines the mapper type
        self._key_1 = key_1

        # Select appropriate default match method depending on the
        # mapper type.
        if self._key_1 == "name":
            self.match_method = ["exact"]
        elif self._key_1 == "unit":
            self.match_method = ["regex"]

        # Define the _m_dict attribute but do not assign a mapping
        # dictionary.
        self._m_dict = None

        # For parsing units, add a UnitRegexMapper object (could
        # be used for name mapping in principle as well)
        self._regex_map = UnitRegexMapper()

        # Define some of the string manipulation attributes
        self._strip_parentheses = False
        self._replace_strings = DEFAULT_STR2REPLACE
        self._remove_strings = DEFAULT_STR2REMOVE

    def __call__(
        self,
        m_dict=None,
        match_method=None,
        regex_map=UnitRegexMapper(),
        replace_strings=None,
        remove_strings=None,
        # strip_parentheses=False,
    ):
        """
        This method provides an interface for the user to set the
        attributes that determine the Mapper object behavior.

        Parameters
        ----------
        m_dict : MapperDict or dict
            The dictionary that will map the names to their alias.
        match_method : str or list
            One or more names of the match method(s) to be used to find
            feature and unit names. Valid values include 'exact', 'ascii',
            'regex', 'fuzzy', 'pubchem'. Default is 'exact' for name
            mapping or 'regex' for unit mapping.
        regex_map : UnitRegexMapper
            UnitRegexMapper object to be used for mapping when match_method
            = 'regex'.
        replace_strings : dict
            Dictionary for searching and replacing string values in in
            the feature names or units. The keys are the search strings
            and the values the replacement strings. Default:
            DEFAULT_STR2REPLACE.
        remove_strings : list
            List of strings that need to be deleted from the feature names
            or units. Default: DEFAULT_STR2REMOVE.
        """

        if self._key_1 == "name":
            self.match_method = match_method or ["exact"]
        elif self._key_1 == "unit":
            self.match_method = match_method or ["regex"]
        self.match_method = check_arg_list(self.match_method, VALID_MATCH_METHODS)

        if isinstance(m_dict, dict):
            self._m_dict = MapperDict(m_dict)
        else:
            self._m_dict = m_dict

        # For parsing units, add a UnitRegexMapper object (could
        # be used for name mapping in principle as well)
        self._regex_map = regex_map

        # Define some of the string manipulation attributes
        self._replace_strings = replace_strings or DEFAULT_STR2REPLACE
        self._remove_strings = remove_strings or DEFAULT_STR2REMOVE
        # self._strip_parentheses = strip_parentheses

    def _df2excel(self, df):
        """
        This method creates an ExcelWriter instance that will either
        append a worksheet to an existing Excel file (for example
        when units are mapped after names) or creates a new Excel
        file when it does not yet exist (when mapping is performed
        for the first time). Any sheets in an already-existing file
        will get overwritten through the use of if_sheet_exists='replace'.

        Parameters
        ----------
        df : DataFrame
            The DataFrame to be saved to the Excel file.

        Raises
        ------

        FileNotFoundError
            When the file exists but has a size of zero bytes. This
            error is caught internally and the 'mode' attribute is
            changed from 'a' to 'w' to overwrite the existing file.
        """
        # Define the Excel file name based on the name of the log file.
        xl_fpath = Path(
            self._output_dir,
            f"mapping_results_{self._log_fname.stem}.xlsx",
        )

        try:
            # Check if any existing file with the same name has a
            # size greater than zero bytes. A file may have been
            # created but not properly written if an error occured.
            # If that was the case, an error will occur.
            if xl_fpath.stat().st_size > 0:
                # If the file size is greater than zero, initialize
                # the ExcelWriter object with mode="a" to append the
                # worksheet.
                xl_writer = pd.ExcelWriter(
                    xl_fpath,
                    mode="a",
                    engine="openpyxl",
                    if_sheet_exists="replace",
                )
            else:
                # If the file size is zero, raise the same error that
                # would be raised if the file did not exists.
                raise FileNotFoundError
        except FileNotFoundError:
            # If the file does not exist, initialize the ExcelWriter
            # object with mode="w" so that the worksheet is added to
            # an empty file.
            xl_writer = pd.ExcelWriter(
                xl_fpath,
                engine="openpyxl",
                mode="w",
            )

        # Add the DataFrame to write it to the Excel file.
        df.to_excel(
            xl_writer,
            sheet_name=f"{self._key_1.capitalize()}s",
            index=False,
        )
        # Must call close otherwise any append operation will fail.
        xl_writer.close()

    def _match_exact(self, strings, m_dict):
        """
        This method returns the values of the items in m_dict for the
        elements in 'strings' that match exactly with a key.

        Parameters
        ----------
        strings : list
            A list with strings to be matched to the keys in m_dict.
        m_dict : dict
            Dictionary to look up the elements of 'strings' in.

        Returns
        -------
        result : list
            A nested list which for each element in 'strings'
            contains a two-item list, the first element being
            the key that was matched, the second element being
            the corresponding value from m_dict.
        """
        return [[s, m_dict[s]] if s in m_dict else [None, None] for s in strings]

    def _match_regex(self, strings):
        """
        This method returns the strings returned by the RegexMapper
        which tries to match and parse the elements in 'strings'
        using a regular expression.

        Parameters
        ----------
        strings : list
            A list with strings to be parsed.

        Returns
        -------
        result : list
            A nested list which for each element in 'strings'
            contains a two-item list, the first element being
            the string produced by the RegexMapper, the second
            element being None.
        """
        regex_match = re.compile(self._regex_map.RE)
        matches = [regex_match.match(s) for s in strings]
        return [
            [self._regex_map.str(m.groupdict()), None] if m else [None, None]
            for m in matches
        ]

    def _match_fuzzy(self, strings, m_dict):
        """
        This method returns the values of the keys in m_dict for the
        elements in 'strings' that have a fuzzy score above a certain
        threshold. The score is calculated by fuzzywuzzy's extractOne
        method.

        Parameters
        ----------
        strings : list
            A list with strings to be matched to the keys in m_dict.
        m_dict : dict
            Dictionary to look up the elements of 'strings' in.

        Returns
        -------
        result : list
            A nested list which for each element in 'strings'
            contains a two-item list, the first element being
            the key that was matched (alongside with the score),
            the second element being the corresponding value from
            m_dict.
        """
        # Create a lambda function to call the extractOne function
        # for an element in 'strings'.
        fuzzy_score = lambda s: fwp.extractOne(
            s,
            list(m_dict.keys()),
            scorer=fwf.token_sort_ratio,
            score_cutoff=fuzzy_min_score(s),
        )
        # Also create a lambda function that formats the name
        # of the matched string and the fuzzy score.
        tuple2str = lambda t: f"{t[0]} (score: {t[1]}%)"
        # Call the fuzzy_score lambda function for each element in
        # 'strings'.
        scores = [fuzzy_score(s) for s in strings]
        # Return the nested list with the matched keys (including
        # the score) and their corresponding values.
        return [[tuple2str(s), m_dict.get(s[0])] if s else [None, None] for s in scores]

    def _match_pubchem(self, strings):
        """
        This method tries to look up the first compound returned by
        a call to PubChem's autocomplete API and its synonym.

        Parameters
        ----------
        strings : list
            A list with strings for which to look up the PubChem
            compound and synonym.

        Returns
        -------
        result : list
            A nested list which for each element in 'strings'
            contains a two-item list, the first element being
            the first compound returned by the PubChem autocomplete
            API, the second element being the corresponding synonym.
        """
        # Call the query_pubchem_fuzzy function for each element in
        # 'strings'. Note that the function returns a list with two
        # elements.
        return [query_pubchem_fuzzy(s) for s in strings]

    def _execute(
        self,
        columns,
        strings,
    ):
        """
        This method calls the match methods specified by the user and
        saves a summary of the results in an Excel file. The results
        are passe back to WaDI's DataObject in a dictionary.

        Parameters
        ----------
        columns : list
            A list with the names of the features (for 'stacked'
            data) or columns for 'wide' data. In both cases they
            correspond to the 'key_0' items in the InfoTable.
        strings : list
            A list with strings to be matched. These can be (feature)
            names or units.

        Returns
        -------
        result : dict
            A dictionary with the aliases (for names) or parsed
            strings (for units) for each element in 'columns'.
        """
        self._msg(f"{self._key_1.capitalize()} mapping", header=True)

        # Convert the input strings to a StringList (which has special
        # methods to modify the string elements of the list).
        try:
            strings = StringList(strings)
        except:
            TypeError("Not a valid type")

        # If the user didn't specify a mapping dictionary, create one
        # using the input strings as keys (the values will all be None).
        if self._m_dict is None:
            self._m_dict = dict.fromkeys(strings)

        # Create a DataFrame that will contain a summary of the results.
        df = pd.DataFrame({"header": columns, "name": strings})

        # Use the StringList method replace_string to replace and remove
        # strings as specified by the user.
        strings.replace_strings(self._replace_strings)
        strings.replace_strings({k: "" for k in self._remove_strings})
        # Remove any leading or trailing whitespace
        strings.strip()
        # Store the modified strings in df
        df["modified"] = strings

        # Check if 'ascii' or 'fuzzy' were passed
        if any([m in ["ascii", "fuzzy"] for m in self.match_method]):
            # Create a new StringList object and call the tidy_strings,
            # (converts all characters to lowercase and removes all
            # non-ASCII characters, as well as characters that are
            # not letters, numbers or whitespace).
            strings_t = StringList(strings)
            strings_t.tidy_strings()
            # Add the tidied strings to df
            df["tidied"] = strings_t

            # Define a new mapping dictionary for which the keys are
            # tidied versions of the keys of the mapping dictionary
            # specified by the user. Repeats the same methods that
            # were used to create strings_t, but now for the keys of
            # m_dict.
            keys_t = StringList(self._m_dict.keys())
            keys_t.replace_strings(self._replace_strings)
            keys_t.replace_strings({k: "" for k in self._remove_strings})
            keys_t.strip()
            keys_t.tidy_strings()
            m_dict_t = {
                k1: self._m_dict.get(k0) for k0, k1 in zip(self._m_dict, keys_t)
            }

        # Add columns to df that will be populated after calling the
        # match method(s).
        df["searched"] = np.nan  # Stores the item that was searched,
        df["found"] = np.nan  # the item that was found,
        df["alias"] = np.nan  # the alias of the found item,
        df["method"] = np.nan  # and the method by which the match was found.

        # Iterate over the specified match methods.
        for m in self.match_method:
            # Select only the rows for which no match was found yet
            idx = df["found"].isnull()
            if all(idx == False):
                break
            dfsub = df.loc[idx, df.columns].copy()
            # The terms to be matched depends on the method
            if m in ["exact", "regex", "pubchem"]:
                dfsub["searched"] = dfsub["modified"]
            else:  # m is ascii or fuzzy
                dfsub["searched"] = dfsub["tidied"]
            # Call the appropriate match method (a bit verbose for readability)
            if m == "exact":
                res = self._match_exact(dfsub["searched"], self._m_dict)
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

            # Store the matched strings in the 'found' column and
            # their aliases in the 'alias' columns. Note that the
            # regex match method does not set the unit aliases.
            dfsub[["found", "alias"]] = res
            # Only place method in the 'method' column if a match
            # was found.
            idx = ~dfsub["found"].isnull()
            dfsub.loc[idx, "method"] = m
            # Update the main df with the values in dfsub.
            df.update(dfsub)

            # Write an overview of the match method's results to the
            # log file.
            self._log(f"* Match method '{m}' yielded the following results:")
            for name, searched, found, alias in zip(
                dfsub["name"], dfsub["searched"], dfsub["found"], dfsub["alias"]
            ):
                if found is not None:
                    self._log(
                        f" - {name}: Searched {searched}, found {found}, alias {alias}."
                    )

        idx = df["alias"].isnull()
        df.loc[idx, "alias"] = df.loc[idx, "modified"]

        # Write the logged messages to the log file and the DataFrame
        # to the Excel file
        self.update_log_file()
        self._df2excel(df)

        # Create the functions return value (a dictionary with the name
        # aliases or parsed unit strings).
        rv_dict = {}
        if self._key_1 == "name":
            # Transfer the aliases found to the DataObject's
            # InfoTable by iterating over the 'alias' column. The
            # values in the 'header' column match up with the level-0
            # keys of the InfoTable.
            for index, (key_0, alias) in df[["header", "alias"]].dropna().iterrows():
                rv_dict[key_0] = {"alias_n": alias}
        elif self._key_1 == "unit":
            # Transfer the unit strings found to the DataObject's
            # InfoTable by iterating over the 'found' column. The
            # values in the 'header' column match up with the level-0
            # keys of the InfoTable.
            for index, (key_0, u_str) in df[["header", "found"]].dropna().iterrows():
                rv_dict[key_0] = {"u_str": u_str}

        return rv_dict

    def match(
        self,
        strings,
    ):

        alias_dict = self._execute(strings, strings)
        df_dict = {}
        for key, value in alias_dict.items():
            alias = list(value.values())[0]
            if key == alias:
                df_dict[key] = np.nan
            else:
                df_dict[key] = alias

        return pd.DataFrame.from_dict(
            df_dict, orient="index", columns=["alias"]
        ).reset_index()
