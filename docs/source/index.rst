.. WaDI documentation master file, created by
   sphinx-quickstart on Wed Jul 13 16:49:36 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

WaDI is an open-source Python package for painless Water Data Importing. 

Background
==========

Each organization uses its own unique file format and data model to 
store hydrogeochemical data. Importing data from a variety of sources
can be quite cumbersome and time consuming. WaDI was designed to 
automate the importing water quality data as much as possible.
WaDI provides support for:

* importing spreadsheet files in which the data format is  'wide' (with each
  parameter stored in a different column) or 'stacked' (all parameters are 
  reported in a row-wise fashion)
* automatically recognizing parameters using an algorithm for name entity 
  recognition (NER)
* recognizing concentration units in a variety of formats (e.g. mg N/l 
  versus mg/l N)
* looking up information about substances in `PubChem <https://pubchem.ncbi.nlm.nih.gov/>`_.


.. toctree::
    :maxdepth: 2
    :hidden:

    Getting started <getting_started/index.rst>
    User guide <user_guide/index.rst>
    Developer guide <developer_guide/index.rst>
    API reference <api/modules.rst>

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
