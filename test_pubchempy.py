import pubchempy as pcp

feature = 'glucose'
compounds = pcp.get_compounds(feature, 'name')
print(compounds)
compound = pcp.Compound.from_cid(compounds[0].cid)
#print(compound.iupac_name)
#print(compound.molecular_weight)

import requests
# Get PubChem CID by name
name = "glucos"

url = f"https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/{name}/json?limit=3"
r = requests.get(url).json()
print(r['total'])
print(r['dictionary_terms']['compound'])
# response = r.json()
# if "IdentifierList" in response:
#     cid = response["IdentifierList"]["CID"][0]
# else:
#     raise ValueError(f"Could not find matches for compound: {name}")
# print(f"PubChem CID for {name} is:\n{cid}")
# NBVAL_CHECK_OUTPUT