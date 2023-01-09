Step 2: Read the data
---------------------


Once the DataObject class has been initialized, its :code:`read_data` method
can be used to import the data that are in the file. 

.. ipython:: python
    :okexcept:
    :okwarning:

    wdo.read_data('tutorial_data.xlsx',
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

Inspection of the spreadsheet file 'tutorial_data.xlsx' shows that
these columns are called 'Sample number', 'Parameter description', 
'Unit description' and 'Reported value' instead. So for wadi to be 
able to find the required columns, their names must be mapped.
This is why the :code:`c_dict` argument (the `c` is shorthand for
column) is used: It takes a dictionary with the compulsory column 
names as keys, and each corresponding value contains the column name 
as it appears in the spreadsheet file.

.. note::
  Instructions for importing 'wide' data is provided in 
  :doc:`this example <../user_guide/messy_data>`.

By default, :code:`read_data` will call the Pandas function 
:code:`read_excel` to import the file contents. With the keyword 
argument :code:`pd_reader` the name of any Pandas reader function 
(for example :code:`read_csv`) can be used instead (note that WaDI 
has been designed to work with :code:`read_excel` and 
:code:`read_csv`, other functions are not guaranteed to work).

Once the data have been read, the contents of the imported DataFrame
can be displayed (note that the DataFrame contains nine rows of data)

.. ipython:: python
    :okexcept:
    :okwarning:

    wdo.df.head(9)

Inspection of the parameter names shows that sulphate was wrongly
spelled as `sulphate` and that the name for calcium also includes
the laboratory method (ICP-AES). Issues such as these can be remedied
by mapping the names to new values, which will be demonstrated in the 
next step.