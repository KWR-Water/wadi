Example 1: Import stacked data
==============================

This example is an extension of the 
:doc:`minimal usage example <../getting_started/minimal_usage_example>`
and demonstrates how to import an Excel file with stacked 
data and perform some basic transformations. It is intended to 
illustrate a typical WaDI workflow.

   :ref:`Step 1 Initialize the DataObject class`
   :ref:`Step 2 Read the data`
   :ref:`Step 3 Map the data`
   :ref:`Step 4 Harmonize the data`

Step 1: Initialize the DataObject class
---------------------------------------

The very first thing to do is to import the wadi library. 
In the code example below it is renamed to wd. 

.. ipython:: python
    :okexcept:
    :okwarning:

    import wadi as wd

The DataObject class is now available as :code:`wd.DataObject`. This
class must always be initialized. It can be called without arguments,
but the optional arguments :code:`log_fname` and :code:`output_dir`
make it possible to change the name and the output directory of the
log file that WADI creates. 

.. note::
    The log file contains information about all the steps it takes 
    to process the data. Users must always inspect the contents of 
    this file to ensure that the WaDI methods resulted in the 
    expected behavior.

.. ipython:: python
    :okexcept:
    :okwarning:

    wdo = wd.DataObject(log_fname='wadi_example.log', silent=True)

The DataObject class instance is stored as :code:`wdo`, which will be used
in the next step to read the data from the spreadsheet file.

Step 2: Read the data
---------------------

Once the DataObject class has been initialized, its :code:`read_data` method
can be used to import the data that are in the file. 

.. ipython:: python
    :okexcept:
    :okwarning:

    wdo.file_reader('stacked_data.xlsx',
        format='stacked',
        c_dict={'SampleId': 'Sample number',
                'Features': 'Parameter description',
                'Units': 'Unit description',
                'Values': 'Reported value',
        },
    )
The :code:`format` argument is to indicate if the data are in 
'stacked' (default) or 'wide' format. If the data are in stacked 
format, there are four compulsory columns that must be present 
in the file with the data

1. SampleId: A unique sample identifier.
2. Features: The names of the features
3. Units: The (chemical concentration) units
4. Values: The measured data

Inspection of the spreadsheet file 'stacked_data.xlsx' shows that
these columns are called 'Sample number', 'Parameter description', 
'Unit description' and 'Reported value' instead. So for wadi to be 
able to find the required columns, their names must be mapped.
This is why the :code:`c_dict` argument (the `c` is shorthand for
column) is used: It takes a dictionary with the compulsory column 
names as keys, and each corresponding value contains the column name 
as it appears in the spreadsheet file.

.. note::
  Instructions for importing 'wide' data are provided in 
  :doc:`this example <../user_guide/messy_data>`.

By default, :code:`read_data` will call the Pandas function 
:code:`read_excel` to import the file contents. With the keyword 
argument :code:`pd_reader` the name of any Pandas reader function 
(for example :code:`read_csv`) can be used instead (note that WaDI 
has been designed to work with :code:`read_excel` and 
:code:`read_csv`, other functions are not guaranteed to work).

Once the data have been read, the contents of the imported DataFrame
can be displayed (note that the imported DataFrame has nine rows of
data).

.. ipython:: python
    :okexcept:
    :okwarning:

    df = wdo.get_frame(as_imported=True)
    df.head(9)

It can be seen that a comma is used as a decimal separator in the
concentrations of the organic substances. This will be fixed in
step four. Inspection of the parameter names shows that sulphate was wrongly
spelled as `Sulpate` and that the name for calcium also includes
the laboratory method (ICP-AES). Issues such as these can be remedied
by mapping the names to new values, which will be demonstrated in the 
next step.

Step 3: Map the data
--------------------

Mapping involves 'translating' the feature names and the units to a 
desired format. To illustrate the principle, the following mapping
operations will be performed

* 'Chloride' will be mapped to 'Cl'
* 'Sulpate' will be mapped to 'SO4'
* The text string '(ICP-AES)' will be removed and 'Calcium' will be
  mapped to 'Ca'.

The name mapping is accomplished by defining a dictionary called 
:code:`name_mapper`, which is passed as the :code:`m_dict` argument
of the :code:`name_map` method. By assigning the text string 
'(ICP-AES)' to the :code:`remove_strings` argument (note that this
must be within a list, as there could be multiple text strings that
need removing), it will be deleted from the final feature name.

.. ipython:: python
    :okexcept:
    :okwarning:

    name_mapper = {'Chloride': 'Cl',
        'Calcium': 'Ca',
        'Sulphate': 'SO4',
    }
    
    wdo.name_map(m_dict=name_mapper,
        match_method=['exact', 'fuzzy'],
        remove_strings=['(ICP-AES)'], 
    )

Step 4: Harmonize the data
--------------------------

Harmonizing the data can involve several operations (combining 
features, deleting features, converting units). Here a :code:`harmonizer`
object it will be added to the WaDI DataObject :code:`wdo`to convert
the data format from 'stacked' to 'wide' and to convert the chemical 
concentrations to mmol/l by setting  :code:`convert_units` to True
(the default is False).

.. ipython:: python
    :okexcept:
    :okwarning:

    df = wdo.harmonizer(convert_units=True, 
        target_units='mmol/l',
    )

    df = wdo.get_frame()
    df.head()

Note that the concentrations for the organic substances could not
be transformed from mass units to molar units because their molar
mass could not be determined (details are reported in the log file).
Their concentrations were below the detection limit and were originally
reported with a comma as a decimal separator. The :code:`harmonize` 
method automatically recognized the '<' symbol, as well as the decimal 
separator and replaces it with a dot.

The mapping results are summarized in the file 
'name_mapping_results_wadi_example.xlsx'. In this file it can be
seen that a match was found for Chloride, Sulpate and Calcium         (ICP-AES). 
All the other features will keep their original names.