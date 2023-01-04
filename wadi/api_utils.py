import re
import requests
import time

RE_CAS = r"^(CAS-)?(\d+)-(\d+)-(\d+)$" # Regular expression for CAS number in PubChem list of synonyms
REQ_PER_SEC = 5 # PUBCHEM API does not accept >5 requests per second
PUBCHEM_COMPOUND_PROPS = [
    'MolecularFormula',
    'MolecularWeight',
    'CanonicalSMILES',
    'IsomericSMILES',
    'InChI',
    'InChIKey',
    'IUPACName',
    'Title',
    'XLogP',
    'ExactMass',
    'MonoisotopicMass',
    'TPSA',
    'Complexity',
    'Charge',
    'HBondDonorCount',
    'HBondAcceptorCount',
    'RotatableBondCount',
    'HeavyAtomCount',
    'IsotopeAtomCount',
    'AtomStereoCount',
    'DefinedAtomStereoCount',
    'UndefinedAtomStereoCount',
    'BondStereoCount',
    'DefinedBondStereoCount',
    'UndefinedBondStereoCount',
    'CovalentUnitCount',
    'Volume3D',
    'XStericQuadrupole3D',
    'YStericQuadrupole3D',
    'ZStericQuadrupole3D',
    'FeatureCount3D',
    'FeatureAcceptorCount3D',
    'FeatureDonorCount3D',
    'FeatureAnionCount3D',
    'FeatureCationCount3D',
    'FeatureRingCount3D',
    'FeatureHydrophobeCount3D',
    'ConformerModelRMSD3D',
    'EffectiveRotorCount3D',
    'ConformerCount3D',
    'Fingerprint2D',
]

def get_json(url):
    try:
        response = requests.get(url, timeout=(2, 5))
        rv = response.json()
        if ("Fault" in rv):
            return None
        response.raise_for_status() # Raises exception unless request was successful
    except Exception as e:
        print("An error occured during contacting of the PubChem Power User Gateway.")
        return None
    else:
        time.sleep(1 / REQ_PER_SEC)
        return rv

def query_pubchem_fuzzy(s):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/{s}/json?limit=3"
    js = get_json(url)
    if (js is None):
        return None
    if (js['total'] > 0):
        compound = js['dictionary_terms']['compound'][0]
        synonym = query_pubchem_synonyms(compound)
        if isinstance(synonym, list):
            synonym = synonym[0].get('Synonym')[0]
        return [compound, synonym]
    else:
        return [None, None]

def query_pubchem_synonyms(s, namespace='name'):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/{namespace}/{s}/synonyms/json"
    js = get_json(url)
    if (js is None):
        return None
    return js['InformationList']['Information']

def query_pubchem_cas(s, namespace='name', allow_multiple=False):
    js_info = query_pubchem_synonyms(s, namespace)
    if (js_info is not None) and (len(js_info)):
        synonyms = js_info[0]['Synonym']
        if (len(synonyms) > 0):
            find = re.compile(RE_CAS, re.IGNORECASE)
            rv = [find.match(syn).groups()[-3:] for syn in synonyms if find.match(syn)]
            if (allow_multiple):                
                return ['-'.join(rvi) for rvi in rv]
            else:
                return '-'.join(rv[0])
            #return list(set(['-'.join(rvi) for rvi in rv])) 
    else:
        return None

def get_pubchem_properties(cids, props):
    if not isinstance(cids, list):
        cids = [cids]
    cids_str = [str(cid) for cid in cids]
    if not isinstance(props, list):
        props = [props]
    for p in props:
        if not (p in PUBCHEM_COMPOUND_PROPS):
            print(f"Property {p} not allowed in PUBCHEM query")
            return []
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{','.join(cids_str)}/property/{','.join(props)}/json"
    js = get_json(url)
    if (js is None):
        return None
    return js['PropertyTable']['Properties']
