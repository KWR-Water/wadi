from collections import UserList
import inspect
import re
import requests
import time

def query_pubchem(s, requests_per_second=5):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/{s}/json?limit=3"
    try:
        response = requests.get(url, timeout=(2, 5))
        response.raise_for_status() # Raises exception unless request was successful
    except Exception as e:
        print("An error occured during contacting of the PubChem API.")
        return None
    else:
        r = response.json()
        if (r['total'] > 0):
            return (r['dictionary_terms']['compound'][0])
        else:
            return None
        time.sleep(1 / requests_per_second) # API does not accept >5 requests per second

def check_arg(arg, valid_args):
    """
    """
    try:
        #idx = [s.find(arg.lower()) for s in valid_args].index(0)
        #return valid_args[idx]
        find = re.compile(rf"^{arg}", re.IGNORECASE)
        return [s for s in valid_args if find.match(s)][0]
    except (ValueError, IndexError) as e:
        raise ValueError(f"invalid argument: '{arg}' must be in {valid_args}")

def check_arg_list(arg_list, valid_args):
    """
    """

    if isinstance(arg_list, str):
        arg_list = [arg_list]

    return [check_arg(a, valid_args) for a in arg_list]

def check_if_nested_list(n_list, min_elements=2):
    """
    """
    error_msg = f"Each nested element must be a list with >={min_elements} elements."
    if isinstance(n_list, list):
        for l in n_list:
            if isinstance(l, list):
                if (len(l) < min_elements):
                    raise ValueError(error_msg)
            else:
                raise TypeError(error_msg)
    else:
        raise TypeError("Expected a nested list")

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

def valid_kwargs(f, **kwargs):
    valid_kwargs = inspect.signature(f).parameters
    rv = kwargs
    for kw in rv.copy(): 
        if kw not in valid_kwargs:
            rv.pop(kw)
    
    return rv