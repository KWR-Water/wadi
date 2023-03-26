# https://pypi.org/project/fuzzywuzzy/
# Installation
# Using PIP via PyPI
# pip install fuzzywuzzy
# or the following to install python-Levenshtein too
# pip install fuzzywuzzy[speedup]

import fuzzywuzzy.fuzz as fwf
import fuzzywuzzy.process as fwp

# Define the search string
s = "benzeen"
# Your database items
database = ["Benzene", "Methylbenzene", "Toluene", "Ethylbenzene", "Xylene"]
# Set a value for the minimum score (100% is a perfect match)
minscore = 60

# Extract all matches for which the score > minscore
fuzzy_score = fwp.extract(
    s,
    database,
    scorer=fwf.token_sort_ratio,
)
print(fuzzy_score)

# Return only the highest scoring item
fuzzy_score = fwp.extractOne(
    s,
    database,
    scorer=fwf.token_sort_ratio,
    score_cutoff=minscore,
)

print(fuzzy_score)

# Slightly more advanced: Let the minimum score be a function of the length of the string

DEFAULT_FUZZY_MINSCORES = {1: 100, 3: 100, 4: 90, 5: 85, 6: 80, 8: 75}
import numpy as np

def fuzzy_min_score(s):
    """
    This function calculates the minimum score required for a valid
    match in fuzzywuzzy's extractOne function. The minimum score depends
    on the length of 's' and is calculated based on the string lengths and
    scores in the DEFAULT_MINSCORES dictionary.

    Parameters
    ----------
    s : str
        String for which the minimum score must be determined.

    Returns
    -------
    result : float
        The minimum score for 's'.
    """
    xp = list(DEFAULT_FUZZY_MINSCORES.keys())
    fp = [v for v in DEFAULT_FUZZY_MINSCORES.values()]
    # Use the interp function from NumPy. By default this function
    # yields fp[0] for x < xp[0] and fp[-1] for x > xp[-1]
    return np.interp(len(s), xp, fp)

minscore = fuzzy_min_score(s)

# Return only the highest scoring item
fuzzy_score = fwp.extractOne(
    s,
    database,
    scorer=fwf.token_sort_ratio,
    score_cutoff=minscore,
)

print(f"Minimum required score: {minscore}", fuzzy_score)