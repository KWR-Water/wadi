========================================================================================================
Importing and recognizing hydrogeochemical data in any format
========================================================================================================
From experience, we know that each organization has its own (different) formats and
data models to store water quality data. Importing data to a uniform database
that is suitable for analysis in HGC can therefore be quite cumbersome.

Highlights
===================

The aim of this import module is to partly automate importing water quality data.
It takes csv and excel files (or pandas' dataframe). And can handle both ‘wide’ data formats
(with each parameter stored in a different column) and ‘stacked’ data formats where all data
is stored in 1 column. Features are automatically recognized using an algorithm
for name entity recognition (ner).

Note
----------------
The following packages are needed in running this module; they are installed automatically when installing the package
with pip via either github or pypi using the requirement.txt file.
Please install them from terminal if you have not done it yet:

pip intall fuzzywuzzy, molmass, pubchempy, pint, googletrans
