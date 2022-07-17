========================================================================================================
Example 1: import stacked data
========================================================================================================

Step 1: Initialize the WADI Importer class
==========================================

Let’s try to import an excel file with stacked data as an example. Of course,
the very first thing to do is to import WADI. In the code example below it is renamed to
wd. This makes the Importer class from WADI available as :code:`wd.Importer`. This
class must always be initialized and it takes several arguments. The :code:`format`
argument is to indicate if the data are in 'stacked' or 'wide' format. The 'gef' 
format is currently not supported.

If the data are in stacked format, there are four compulsory columns that must
be present in the file with the data

1. SampleId: A unique sample number.
2. Features: The names of the chemical substances
3. Units: The (chemical concentration) units
4. Values: The measured data/concentrations

Inspection of the spreadsheet file 'realworlddata_subset.xlsx' shows that
these columns are called 'Monster', 'Parameter omschrijving', 
'Eenheid omschrijving' and 'Berekende gerapporteerde waarde' instead. So for
WADI to be able to find the required columns, their names must be mapped.
This is why the :code:`c_dict` argument is used: It takes a dictionary with 
the compulsory column names as keys, and each item contains the corresponding
column name as it appears in the spreadsheet file.

The Importer class instance is stored as :code:`wi`, which will be used in the 
next step to read the data from the spreadsheet file.

.. ipython:: python
    :okexcept:
    :okwarning:

    import wadi as wd

    wi = wd.Importer(format='stacked',
                    c_dict={'SampleId': 'Monster',
                            'Features': 'Parameter omschrijving',
                            'Units': 'Eenheid omschrijving',
                            'Values': 'Berekende gerapporteerde waarde',
                            },
                    )

Step 2: Read the data
==========================================

Once the Importer class has been initialized, the :code:`read_data` function
can be used to import the data that are in the file. In this case, the file
name is the only argument. By default, :code:`read_data` will call the pandas
function :code:`read_excel` to import the file contents. With the keyword 
argument :code:`pd_reader` the name of any Pandas reader function (for example
:code:`read_csv`) can be used instead (note that WADI has been designed to 
work with :code:`read_excel` and :code:`read_csv`, other functions are not
guaranteed to work).

.. ipython:: python
    :okexcept:
    :okwarning:

    wi.read_data('example_1.xlsx',
                )
Once the data have been read, the contents of the DataFrame that was imported
can be inspected

.. ipython:: python
    :okexcept:
    :okwarning:

    wi.df.head()

Note that WADI keeps a log file (extension '.log') that contains information 
about all the steps it takes to process the data. Users must ALWAYS inspect
the contents of this file to ensure that the WADI follows the expected behavior.

Step 3: Map the data
==========================================

Mapping involves 'translating' the column names and the units to a desired
format. To illustrate the principle, the column called 'Chloride' will be 
mapped to 'Cl'. This is accomplished by passing a dictionary for the 
:code:`m_dict` argument of the function :code:`map_data`.

.. ipython:: python
    :okexcept:
    :okwarning:

    wi.map_data(m_dict={'Chloride': 'Cl'})

The code above did not generate any output but the result of the mapping
is summarized in the file 'name_mapping_summary_example_1.xlsx'. In this 
file it can be seen that a match was found only for Chloride, all the other 
features will keep their original names.

Step 4: Harmonize the data
==========================================

The :code:`harmonize` function can do a number of things (combining features,
deleting features, converting units), which will be  demonstrated in the next 
example. Here it will simply be called to convert the data from 'stacked' to
'wide' format. Because no information about unit conversion is passed to the
:code:`harmonize` function, all chemical concentrations are converted to mg/L.

.. ipython:: python
    :okexcept:
    :okwarning:

    df = wi.harmonize()

    df.head()
