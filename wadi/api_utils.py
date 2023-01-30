import re
import requests
import time

import googletrans as gt

"""
This file contains several functions to interact with the PubChem and 
Google Translate APIs. Interaction with the PubChem REST API is directly
through the use of the requests module. The URL paths are based on the
description of the API found # here (Last consulted on 15 January 2023): 
https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest.

For Google Translate, the googletrans package is used. Note that version 
3.0.0 of this package no longer seems to work, so version 3.1.0 or higher
is needed.
"""

# Define some global constants for the PubChem methods
RE_CAS = r"^(CAS-)?(\d+)-(\d+)-(\d+)$"  # Regular expression for CAS number in PubChem list of synonyms
REQ_PER_SEC = 5  # PUBCHEM API does not accept >5 requests per second
# List of property names available in PubChem when querying compound properties. See
# https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest#section=Compound-Property-Tables 
PUBCHEM_COMPOUND_PROPS = [  
        "MolecularFormula",
        "MolecularWeight",
        "CanonicalSMILES",
        "IsomericSMILES",
        "InChI",
        "InChIKey",
        "IUPACName",
        "Title",
        "XLogP",
        "ExactMass",
        "MonoisotopicMass",
        "TPSA",
        "Complexity",
        "Charge",
        "HBondDonorCount",
        "HBondAcceptorCount",
        "RotatableBondCount",
        "HeavyAtomCount",
        "IsotopeAtomCount",
        "AtomStereoCount",
        "DefinedAtomStereoCount",
        "UndefinedAtomStereoCount",
        "BondStereoCount",
        "DefinedBondStereoCount",
        "UndefinedBondStereoCount",
        "CovalentUnitCount",
        "Volume3D",
        "XStericQuadrupole3D",
        "YStericQuadrupole3D",
        "ZStericQuadrupole3D",
        "FeatureCount3D",
        "FeatureAcceptorCount3D",
        "FeatureDonorCount3D",
        "FeatureAnionCount3D",
        "FeatureCationCount3D",
        "FeatureRingCount3D",
        "FeatureHydrophobeCount3D",
        "ConformerModelRMSD3D",
        "EffectiveRotorCount3D",
        "ConformerCount3D",
        "Fingerprint2D",
    ]


def translate_strings(
    strings,
    src_lang,
    dst_lang,
    max_attempts,
):
    """
    This method attempts to translate a list of strings from
    src_lang to dst_lang using Google Translate.

    Parameters
    ----------
    src_lang : str
        String that specifies the language to translate from.
        Default: "NL".
    dst_lang : str
        String that specifies the language to translate to.
        Default: "EN".
    max_attempts : int
        The maximum number of attempts to connect to the Google
        Translate API. Default: 10.
    """

    strings = list(strings)

    if not all([l.lower() in gt.LANGUAGES for l in [src_lang, dst_lang]]):
        raise ValueError("Invalid language(s) specified")

    t = gt.Translator()
    for i in range(max_attempts):
        try:
            rv = []
            for s in strings:
                rv.append(t.translate(s, src=src_lang, dest=dst_lang).text)
            return rv
        except:
            print(
                f"Failed attempt ({i}) to connect to Google Translate API. Retrying..."
            )

    return None


def get_pubchem_json(url):
    """
    This method interacts with the PubChem REST API by sending
    a URL and, when successful, returns a json dict.

    Parameters
    ----------
    url : str
        The URL containing the query/request.

    Returns
    -------
    result : dict or None
        Returns the json dictonary returned by the PubChem API, or
        None if an error occurred.
    """
    try:
        # Send the request and try to get the json dictionary
        # from the response
        response = requests.get(url, timeout=(2, 5))
        rv = response.json()
        # Any fault on the PubChem side will result in a
        # key 'Fault'. If this key exists, return None.
        if "Fault" in rv:
            return None
        # Call raise_for_status, which raises an exception
        # when the request was unsuccessful.
        response.raise_for_status()
    except Exception as e:
        # Handle the exception raised by raise_for_status(). Print a
        # message to the screen and return None.
        print("An error occured during contacting of the PubChem Power User Gateway.")
        return None
    else:
        # Pause to avoid exceeding the permitted number of requests
        # per second.
        time.sleep(1 / REQ_PER_SEC)
        # Return the json dictionary.
        return rv


def query_pubchem_fuzzy(s):
    """
    This method uses the PubChem REST auto-complete API service
    that supports fuzzy matching of input strings.

    Parameters
    ----------
    s : str
        The string to look up

    Returns
    -------
    result : list
        A two-element list. The first element is the first compound name
        returned if the request was successful, the second the first
        synonym returned by calling query_pubchem_synonyms. Returns
        [None, None] if any error occurred.
    """
    # Insert 's' into the URL for the auto-complete service.
    url = (
        f"https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/{s}/json?limit=3"
    )
    # Get the json dict, return [None, None] if an error occurred.
    js = get_pubchem_json(url)
    if js is None:
        return [None, None]
    # Check the value of the 'total' key, which will be greater than zero
    # if the fuzzy search yielded any compounds.
    if js["total"] > 0:
        # Grab the first compound from the list of compounds in the dict.
        compound = js["dictionary_terms"]["compound"][0]
        # Try to determine its synonym.
        synonym = query_pubchem_synonyms(compound)
        # The return value is a list, the synonyms are in the dict that
        # is the first element of the list. Only the first synonym from
        # the list is used (there may be many).
        if isinstance(synonym, list):
            synonym = synonym[0].get("Synonym")[0]
            # Return the fuzzy-matched compound and its synonym.
            return [compound, synonym]

    # If this part of the code gets reached then the compoud/synonym
    # pair could not be returned, so return [None, None]
    return [None, None]


def query_pubchem_synonyms(s, namespace="name"):
    """
    This method uses the PubChem REST API service to look up synonyms
    of a PubChem compound based on its name or other allowed namespace.
    See https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest#section=Input.

    Parameters
    ----------
    s : str
        The string to look up
    namespace : str, optional
        The namespace to seach for (for example, 'name', 'cid',
        'smiles', ...). Default: 'name'

    Returns
    -------
    result : list
        The return value is the list that is stored in the 'Information'
        item of the json dict. This list contains a dict (or perhaps more?)
        with the CID and a list of synonyms. Returns None if an error
        occurred.
    """
    # Insert 's' and 'namespace' into the URL.
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/{namespace}/{s}/synonyms/json"
    # Get the json dict, return None if an error occurred.
    js = get_pubchem_json(url)
    if js is None:
        return None
    # Return the list that contains the dict(s?) with CID and synonyms list.
    return js["InformationList"]["Information"]


def query_pubchem_cas(s, namespace="name", allow_multiple=False):
    """
    This method uses the PubChem REST API service to look up the CAS
    of a PubChem compound based on its name or other allowed namespace.
    See https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest#section=Input.
    The CAS number returned is the first number matched by a regular
    expression in the list of synonyms for the compound.

    Parameters
    ----------
    s : str
        The string to look up
    namespace : str, optional
        The namespace to seach for (for example, 'name', 'cid',
        'smiles', ...). Default: 'name'
    allow_multiple : bool, optional
        When False only the first CAS that was identified is returned.
        When True all CAS numbers in the synonym list are returned. Default:
        False.

    Returns
    -------
    result : list
        The return value is the list that is stored in the 'Information'
        item of the json dict. This list contains a dict (or perhaps more?)
        with the CID and a list of synonyms. Returns None if an error
        occurred.
    """
    # Get the synonyms for compound s
    js_info = query_pubchem_synonyms(s, namespace)
    # If a list was returned then get the list with synonyms from the
    # dict that is the first list element.
    if (js_info is not None) and (len(js_info)):
        synonyms = js_info[0]["Synonym"]
        # If the list contains any synonyms...
        if len(synonyms) > 0:
            # ... collect the elements that are identified as a CAS number
            # by the RE_CAS regular expression.
            find = re.compile(RE_CAS, re.IGNORECASE)
            rv = [find.match(syn).groups()[-3:] for syn in synonyms if find.match(syn)]
            # Convert the three-element lists within rv to their string representation.
            rv = ["-".join(rvi) for rvi in rv]
            # If only a single CAS number is allowed return the first item, else
            # return the entire list.
            if allow_multiple:
                return rv
            else:
                return rv[0]
    else:
        # If an error occured return None
        return None


def get_pubchem_molecular_weight(s, namespace="name"):
    """
    This method uses the PubChem REST API service to look up the molecular
    weight of a PubChem compound based on its name or other allowed namespace.
    See https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest#section=Input.

    Parameters
    ----------
    s : str
        The string to look up
    namespace : str, optional
        The namespace to seach for (for example, 'name', 'cid',
        'smiles', ...). Default: 'name'

    Returns
    -------
    result : float
        The return value is the 'MolecularWeight' item of the json dict returned by PubChem or None
        if an error occurred.
    """
    # Insert 's' and 'namespace' into the URL.
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/{namespace}/{s}/property/MolecularWeight/json"
    # Get the json dict, return None if an error occurred.
    js = get_pubchem_json(url)
    if js is None:
        return None
    if len(js["PropertyTable"]["Properties"]) > 0:
        # Return the MolecularWeight property.
        return float(js["PropertyTable"]["Properties"][0]["MolecularWeight"])
    else:
        return None
        
def get_pubchem_properties(cids, props):
    """
    This method uses the PubChem REST API service to retrieve a table of
    compound properties for one or more compounds based on their cid(s).

    Parameters
    ----------
    cids : int, str or list
        The PubChem ID(s) of the compound(s) to look up.
    props : str or list
        The names of the properties to return. For possible values see
        https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest#section=Compound-Property-Tables

    Returns
    -------
    result : list
        A list with the requested properties, or None if the request
        was unsuccessful.
    """
    # Ensure that cids is a list.
    if not isinstance(cids, list):
        cids = [cids]
    # Convert all elements of cids to strings.
    cids_str = [str(cid) for cid in cids]
    # Ensure that props is a list.
    if not isinstance(props, list):
        props = [props]
    # Check if each element in props is a value accepted by the API. Otherwise 
    # return None.
    for p in props:
        if not (p in PUBCHEM_COMPOUND_PROPS):
            print(f"Property {p} not allowed in PUBCHEM query")
            return None
    # Insert the cid(s) and propert(y/ies) into the URL.
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{','.join(cids_str)}/property/{','.join(props)}/json"
    # Get the json dict
    js = get_pubchem_json(url)
    # If the request was unsuccessful js will be None, so return None.
    if js is None:
        return None
    # If successful return the 'Properties' dict item.
    return js["PropertyTable"]["Properties"]
