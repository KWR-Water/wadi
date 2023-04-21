Example 1: Import stacked data
==============================

This example is an extension of the
:doc:`minimal working example <../getting_started/minimal_working_example>`
and demonstrates how to import an Excel file with stacked
data and perform some basic transformations. It is intended to
illustrate a typical WaDI workflow:

* `Step 1: Initialize the DataObject class`_
* `Step 2: Read the data`_
* `Step 3: Map the names`_
* `Step 4: Harmonize the data`_

.. note::
  Instructions for importing 'wide' data are provided in
  :doc:`example 2 <../user_guide/example_02>`.

Step 1: Initialize the DataObject class
---------------------------------------

The very first thing to do is to import the WaDI library.
In the code example below it is renamed to wd.

.. ipython:: python
    :okexcept:
    :okwarning:

    import wadi as wd

The DataObject class is now available as :code:`wd.DataObject`. This
class must always be initialized. It can be called without arguments,
but the optional arguments :code:`log_fname` and :code:`output_dir`
make it possible to change the name and the output directory of the
log file that WaDI creates.

.. ipython:: python
    :okexcept:
    :okwarning:

    wdo = wd.DataObject(log_fname='WaDI_example.log', silent=True)

The DataObject class instance is stored as :code:`wdo`, which will be used
in the next step to read the data from the spreadsheet file.

.. note::
    The log file contains information about all the steps it takes
    to process the data. Users must always inspect the contents of
    this file to ensure that the WaDI methods resulted in the
    expected behavior.

Step 2: Read the data
---------------------

Once the DataObject class has been initialized, its :code:`file_reader`
method must be called to specify the name and the structure of the file
that is to be imported. For the purpose of the demonstration in this
documentation, find the directory with the data files with `get_data_dir`


.. ipython:: python
    :okexcept:
    :okwarning:

    from wadi.documentation_helpers import get_data_dir
    DATA_DIRECTORY = get_data_dir()

    wdo.file_reader(DATA_DIRECTORY / 'stacked_data.xlsx',
        format='stacked',
        c_dict={'SampleId': 'Sample number',
                'Features': 'Parameter description',
                'Units': 'Unit description',
                'Values': 'Reported value',
        },
    )
The :code:`format` argument is to indicate if the data are in
'stacked' format. This means that four compulsory columns must
be present in the spreadsheet file

1. SampleId: A unique sample identifier
2. Features: The names of the features
3. Units: The (chemical concentration) units
4. Values: The measured data

Inspection of the spreadsheet file 'stacked_data.xlsx' shows that
these columns are called 'Sample number', 'Parameter description',
'Unit description' and 'Reported value'. Therefore, for WaDI to be
able to find the compulsory columns, their names must be mapped to
the column names listed above. This is why the :code:`c_dict`
argument (the `c` is shorthand for column) is used: It takes a
dictionary with the compulsory column names as keys, and each
corresponding value contains the column name as it appears in the
spreadsheet file.

.. note::
    By default, :code:`file_reader` will set the Pandas method
    :code:`read_excel` as the importer for the file contents. With the keyword
    argument :code:`pd_reader` the name of any Pandas reader function
    (for example :code:`read_csv`) can be used instead (note that WaDI
    has been designed to work with :code:`read_excel` and
    :code:`read_csv`, other functions are not guaranteed to work).

The contents of the imported DataFrame can be displayed by calling the
:code:`get_imported_dataframe()` method of the :code:`wdo` object. Note
that the imported DataFrame has nine rows of data.

.. ipython:: python
    :okexcept:
    :okwarning:

    df = wdo.get_imported_dataframe()
    df.head(9)

Inspection of the parameter names shows that sulphate was wrongly
spelled as `Sulpate` and that the name for calcium also includes
the laboratory method (ICP-AES). Issues such as these can be remedied
by mapping the names to new values, which will be demonstrated in the
next step.

Step 3: Map the names
---------------------

Mapping involves 'translating' the feature names and the units to a
desired format. To illustrate the principle, the following mapping
operations will be performed

* 'Chloride' will be mapped to 'Cl'
* 'Sulpate' will be mapped to 'SO4'
* The text string '(ICP-AES)' will be removed and 'Calcium' will be
  mapped to 'Ca'.

By assigning the text string '(ICP-AES)' to the :code:`remove_strings`
argument (note that this must be within a list, as there could be
multiple text strings that need removing), it will be deleted from the
feature name. The name mapping is accomplished by defining a dictionary called
:code:`name_mapper`, which is passed as the :code:`m_dict` argument
of the :code:`name_map` method. The keys of :code:`m_dict` are the feature
names to be matched, which will be replaced by the corresponding values.

.. ipython:: python
    :okexcept:

    name_mapper = {'Chloride': 'Cl',
        'Calcium': 'Ca',
        'Sulphate': 'SO4',
    }

    wdo.name_map(m_dict=name_mapper,
        match_method=['exact', 'fuzzy'],
        remove_strings=['(ICP-AES)'],
    )

Both the 'exact' and 'fuzzy' mapping methods are used to match feature names
to the keys in :code:`m_dict`. The fuzzy search algorithm finds a match if two
terms are sufficiently close based on score between 0 and 100 percent. This
match method will therefore result in a match for the misspelled feature name
'Sulpate'. The 'exact' match method will find 'Chloride' and 'Calcium'. The
organic substances are not in :code:`name_mapper`, so their names will remain
unchanged.

.. note::
  More information on creating mapping dictionaries can be found :doc:`here <../user_guide/mapping_dictionaries>`

Step 4: Harmonize the data
--------------------------

Harmonizing the data can involve several operations (combining
features, deleting features, converting units). Here a :code:`harmonizer`
object it will be added to the WaDI DataObject :code:`wdo` to convert
the data format from 'stacked' to 'wide' and to convert the chemical
concentrations to mmol/l by setting  :code:`convert_units` to True
(the default is False).

.. ipython:: python
    :okexcept:

    df = wdo.harmonizer(convert_units=True,
        target_units='mmol/l',
    )

Finally the result of the operations defined above can be obtained by
calling the :code:`get_converted_dataframe` method.

.. ipython:: python
    :okexcept:

    df = wdo.get_converted_dataframe()
    df.head()

The mapping results are summarized in the file
'mapping_results_WaDI_example.xlsx' in the folder named 'WaDI_output'.
In this file it can be seen that a match was found for Chloride,
Sulpate and Calcium         (ICP-AES).  All the other features will
keep their original names.

WaDI uses the molmass package, which tries to calculate the molar mass
from chemical formulas.
If the molmass package is unable to determine the molar mass, WaDI tries
to find it in the online PubChem library. In some cases unit conversion
fails and the imported data will remain in their original units. This is
the case here for the electrical conductivity (as expected this cannot
be converted to molar concentration units) and the original
numbers are simply kept. Concentrations that were below the detection limit
(values with a '<' symbol) were originally reported with a comma as a decimal
separator. In the converted DataFrame the decimal separator is replaced with a dot.
