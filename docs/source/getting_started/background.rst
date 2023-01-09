Background
==========
Each organization has its own unique file format and data model to 
store hydrogeochemical data. Importing data from a variety of sources
can be quite cumbersome and time consuming. WaDI was designed to 
automate the importing water quality data as much as possible.

The typical workflow for WaDI is to import the data from a spreadsheet
file, map the names of the features to their alias (the term used in WaDI
to indicate the desired name in the final output) and perform actions like
unit conversion and merging of columns. WaDI provides support for:

* importing spreadsheet files in which the data format is  ‘wide’ (with each
  parameter stored in a different column) or ‘stacked’ (all parameters are 
  reported in a row-wise fashion)
* automatically recognizing parameters using an algorithm for name entity 
  recognition (ner)
* recognizing concentration units in a variety of formats (e.g. mg N/l 
  versus mg/l N)
* looking up information about substances in `PubChem <https://pubchem.ncbi.nlm.nih.gov/>`.
