Using blocks to import messy data
=================================

By using Pandas' exhaustive functionality for reading spreadsheet
and comma separated values (csv) files, WaDI can handle almost any
file, even if its contents are poorly organized. Inspection of the
spreadsheet file 'messy_data.xlsx' shows that its contents are a 
real mess. For example, some concentration data are spread over two 
columns. Also the rows with column headers are not nicely aligned, 
there are empty rows and columns and there are trailing rows with 
data that should be skipped. This example demonstrates how WaDI uses
the keyword arguments of the  :code:`read_excel` function to import 
separate blocks of data (called 'blocks') into a single DataFrame.

Step 1: Initialize the WaDI DataObject class
--------------------------------------------

Nothing special needs to be done in this step, except to provide the
log file name.

.. ipython:: python
    :okexcept:
    :okwarning:

    import wadi as wd

    wdo = wd.DataObject(log_fname='messy_data.log')

Step 2: Read the data
---------------------

Because the required data in the file are scattered, 
three so-called 'blocks' are defined. Each takes a number of keyword
arguments. Basically all keyword arguments of a Pandas reader function, 
in this case :code:`read_excel`, are allowed. In this case, they are
:code:`skiprows`, :code:`usecols` and :code:`na_values`. The latter is 
used to filter out cell that have '999' as values. Note that the keyword
argument :code:`skiprows` accepts a list of (zero-based) row numbers to be
skipped, and for each pane this list is stored in :code:`rows2skip` before 
it is passed as an argument value for :code:`skiprows`. The row numbers,
unfortunately, must be counted manually in the spreadsheet file. Not 
also  how :code:`usecols` is used to grab only the relevant columns from
the file. 

There are also a few keyword arguments that are specific to the 
:code:`read_data` function. These are :code:`datatype`, which tells
WaDI what kind of data is being read. Valid values are :code:`sampleinfo`, 
for sample data that are not going to be modified (for example, sample
coordinates) in any way, and :code:`feature`, for data that are going to be 
mapped and/or harmonized.

The keyword argument :code:`unit_row` tells :code:`read_data` on which row
in the spreadsheet it has to look for the (chemical concentration) units.
As with :code:`skiprows`, the number has to be looked up by the user by 
inspecting the contents of the spreadsheet file.

.. ipython:: python
    :okexcept:
    :okwarning:

    rows2skip = list(range(9)) + [22, 23] + list(range(25, 35))
    df0_kwargs = {'skiprows': rows2skip, 
        'usecols': "C:E", 
        'datatype': 'sampleinfo',
    }

    rows2skip = list(range(3)) + list(range(4, 10)) + [22, 23]
    df1_kwargs = {'skiprows': rows2skip, 
        'usecols': "F:AF", 
        'units_row': 4, 
        'datatype': 'feature', 
        'na_values': [999],
    }

    rows2skip = list(range(8)) + [9, 22, 23]
    df2_kwargs = {'skiprows': rows2skip, 
        'usecols': "AG", 
        'datatype': 'sampleinfo',
    }

Now that the arguments for the three data blocks have been defined,
the :code:`read_data` function is called to import the data into a
DataFrame. In addition to the list with the previously defined
keyword arguments assigned to :code:`blocks`, the data format is 
passed on as the argument :code:`format`. In this case, the 
concentrations are organized in columns, so the data are in wide 
format.

.. ipython:: python
    :okexcept:
    :okwarning:

    wdo.read_data(file_path='messy_data.xlsx',
        format='wide',
        blocks=[df0_kwargs, df1_kwargs, df2_kwargs],
    )

Once the data have been read, the contents of the DataFrame that was
imported can be inspected. Note how Pandas (not WaDI) has 
automatically numbered the second column of duplicate columns by
appending '.1'.

.. ipython:: python
    :okexcept:
    :okwarning:

    wdo.df.head()

Step 3: Map the data and units
------------------------------

The data are mapped using a dictionary that matches the original column names
to the desired column names. In the code below, this dictionary is created
manually and is stored as :code:`feature_dict`. Note how a mistake has 
creeped in the spelling of 'Nitrate' in the spreadsheet: by accident the 
Dutch word was typed in the first column. It will turn out later 
that this mistake does not cause any problems, because
the 'fuzzy' search algorithm is used. This alogrithm finds a match if two
terms are sufficiently close based on score between 0 and 100 percent. The 
other match method used here is 'exact', which requires the search terms 
to be equal. The :code:`feature_dict` is assigned to the :code:`m_dict` 
keyword argument of the :code:`map_names` function. The match methods are
grouped in a list that is assigned to the :code:`match_method` keyword 
argument.

.. ipython:: python
    :okexcept:
    :okwarning:

    feature_dict = wd.MapperDict({'Phosphate': 'PO4', 
            'Nitrate': 'NO3', 
            'Nitrite': 'NO2',
            'Ammonium': 'NH4',
            'Silica': 'SiO2',
            'Sulphate': 'SO4', 
            'Sodium': 'Na',
            'Calcium': 'Ca',
            'Arsenic': 'As',
        }
    )

    wdo.map_names(m_dict=feature_dict,
        match_method=['exact', 'fuzzy'],
    )

Units are mapped with the :code:`map_units` function. In this case
the preferred match method is 'regex', which uses a special WaDI 
search method (based on regular expressions) that tries to decipher
the format of the units string. For example, it can tell the 
difference between 'mg N/l', 'mg N/l NO3' or 'mg/l NO3', and knows
what molecular weight to use when mass units are to be converted to 
molar units. 

In this case there are also a few symbols that need to be replaced
for the unit mapping to be successful. These are passed as a 
dictionary with the keyword arguments :code:`replace_strings`.

.. ipython:: python
    :okexcept:
    :okwarning:

    wdo.map_units(match_method=['regex'],
        replace_strings={'μ': 'u', '-': ' ', '%': 'percent'},
    )

The code above did not generate any output but the result of the 
mapping is summarized in the file 'name_mapping_results_messy_data.xlsx'
for the features, and 'unit_mapping_results_messy_data.xlsx' for the 
units.

Step 4: Harmonize the data
--------------------------

The :code:`harmonize` method is used below to combine duplicate columns,
delete a column and to convert the concentrations to a different unit.

The columns to be combined must be grouped in a list of at least two 
column names. The data in the first column in the list will be 
overwritten with data from the next column where the values in the
first column are NaN (not a number). More than two columns are 
allowed, WaDI will simply try to fill up as many NaN values as 
possible. Note that eight column pairs are selected for merging
and that these are grouped in a list. This means that the value 
passed for :code:`merge_columns` must always be a nested list,
even if only one set of column names is passed.

The :code:`harmonize` method also has a keyword argument 
:code:`drop_columns`, which takes a list of column names that will
be deleted.

The :code:`target_units` keyword argument specifies what 
(concentration) units will be used for the feature data. In this 
case the values will be converted to 'mmol/l'. This value can be
overridden for individual columns with the :code:`override_units` 
keyword argument. The code example below shows how this option can
be used to convert only the arsenic concentrations to umol/l.

.. note::
    Behind the scenes, WaDI relies on Pint to convert the units. Any
    problems that it encountered will be recorded in the log file 
    (messy_data.log in this example). It is strongly advised that the 
    user always checks the log file to verify that no unexpected 
    behavior occurred.

.. ipython:: python
    :okexcept:
    :okwarning:

    merge_cols = [['Phosphate', 'Phosphate.1'], 
        ['Nitraat', 'Nitrate'],
        ['Nitrite', 'Nitrite.1'],
        ['Ammonium', 'Ammonium.1'],
        ['Silica', 'Silica.1'],
        ['Sulphate', 'Sulphate.1'],
        ['Calcium', 'Calcium.1'],
        ['Arsenic', 'Arsenic.1'],
    ]
    df = wdo.harmonize(merge_columns=merge_cols, 
        drop_columns=['Unnamed: 18'],
        target_units = 'mmol/l',
        override_units = {'Arsenic': 'umol/l'},
    )

    df.head()

Displaying the DataFrame does not show the values for arsenic. To verify
that the values were converted correctly the column name can be specified

.. ipython:: python
    :okexcept:
    :okwarning:

    df['As'].head()

Finally, the resulting DataFrame can be saved to an Excel file using the
:code:`to_excel` function.

.. ipython:: python
    :okexcept:
    :okwarning:

    df.to_excel('tidied_data.xlsx')
