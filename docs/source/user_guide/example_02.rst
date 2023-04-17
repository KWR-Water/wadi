Example 2: Using blocks to import messy data
============================================

By using Pandas' exhaustive functionality for reading files,
WaDI can handle almost any spreadsheet or comma separated values
file, even if its contents are poorly organized. Inspection of the
spreadsheet file 'messy_data.xlsx' shows that its contents are truly
a mess. For example, some concentration data are spread over two
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

    import wadi as wd

    wdo = wd.DataObject(
        log_fname='messy_data.log',
        silent=True
    )

Step 2: Read the data
---------------------

Because the required data in the file are scattered,
three so-called 'blocks' are defined. Each takes a number of keyword
arguments. Basically all keyword arguments of a Pandas reader function,
in this case :code:`read_excel`, are allowed. In this case, they are
:code:`skiprows`, :code:`usecols` and :code:`na_values`. The latter is
used to filter out cell that have '999' as values.

The keyword argument :code:`skiprows` accepts a list of (zero-based) row
numbers to be skipped, and for each block this list is stored in
:code:`rows2skip` before it is passed as an argument value for
:code:`skiprows`. The row numbers, unfortunately, must be counted manually
in the spreadsheet file. Note how :code:`usecols` is used to grab only a
selection of columns for each block.

There are also a few keyword arguments that are specific to the
:code:`read_data` function. These are :code:`datatype`, which tells
WaDI what kind of data is being read. Valid values are :code:`sampleinfo`,
for sample data that are not going to be modified (for example, sample
coordinates) in any way, and :code:`feature`, for data that are going to be
mapped and/or harmonized.

The keyword argument :code:`units_row` tells :code:`read_data` on which row
in the spreadsheet it has to look for the (chemical concentration) units.
As with :code:`skiprows`, the number has to be looked up by the user by
inspecting the contents of the spreadsheet file.

.. ipython:: python

    rows2skip0 = list(range(8)) + [21, 22] + list(range(24, 34))
    df0_kwargs = {
        'skiprows': rows2skip0,
        'usecols': "B:D",
        'datatype': 'sampleinfo',
    }

    rows2skip1 = list(range(2)) + list(range(3, 9)) + [21, 22]
    df1_kwargs = {
        'skiprows': rows2skip1,
        'usecols': "E:AE",
        'units_row': 4,
        'datatype': 'feature',
        'na_values': [999],
    }

    rows2skip2 = list(range(7)) + [8, 21, 22]
    df2_kwargs = {
        'skiprows': rows2skip2,
        'usecols': "AF",
        'datatype': 'sampleinfo',
    }

Now that the arguments for the three data blocks have been defined,
they can be passed on to the :code:`file_reader` method.
Additionally, the file name and the data format is passed. In this case, the
concentrations are organized in columns, so the :code:`format` argument
should become 'wide'.

.. ipython:: python

    wdo.file_reader(
        file_path='messy_data.xlsx',
        format='wide',
        blocks=[df0_kwargs, df1_kwargs, df2_kwargs],
    )

Once the data have been read, the contents of the DataFrame that was
imported can be inspected. Note how Pandas (not WaDI) has
automatically numbered the second column of duplicate columns by
appending '.1'.

.. ipython:: python
    :okexcept:

    df = wdo.get_imported_dataframe()
    df.head()

Note how a mistake has creeped in the spelling of 'Nitrate' in the spreadsheet:
by accident the Dutch word was typed in the first column.

Step 3: Map the names and units
-------------------------------

The feature names are mapped using a dictionary that matches the original
column names to the desired column names. In the code below, this dictionary
is created manually and is stored as :code:`feature_dict`. The
:code:`feature_dict` is  assigned to the :code:`m_dict` keyword argument of
the :code:`name_map` method.

The match methods are grouped in a list that is assigned to the
:code:`match_method` keyword argument. Both the 'exact' and 'fuzzy'
match methods are included. The latter will be able to match 'Nitraat'
to 'Nitrate', which will automatically fix the translation mistake for
this feature.

.. ipython:: python

    feature_dict = wd.MapperDict({
            'Phosphate': 'PO4',
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

    wdo.name_map(
        m_dict=feature_dict,
        match_method=['exact', 'fuzzy'],
    )

The way units are mapped can be controlled  with the :code:`unit_map`
method. In this case the preferred match method is 'regex', which uses the
specialized WaDI search method (based on regular expressions) that tries to
decipher the units strings. For example, it can tell the difference between
'mg N/l', 'mg N/l NO3' or 'mg/l NO3', and knows what molecular weight to use
when concentrations reported in mass units are to be converted to molar units.

In this case there are also a few symbols that need to be replaced for the
unit mapping to be successful. These are passed as a dictionary with the
keyword arguments :code:`replace_strings`.

.. ipython:: python

    wdo.unit_map(
        match_method=['regex'],
        replace_strings={'μ': 'u', '-': ' ', '%': 'percent'},
    )

Step 4: Harmonize the data
--------------------------

The :code:`harmonizer` method is used below to define which columns
are to be merged or deleted and to specify how measurement data are
to be converted from one unit to another.

The columns to be combined must be grouped in a list of at least two
column names. The data in the first column in the list will be
overwritten with data from the next column where the values in the
first column are NaN (not a number). More than two columns are
allowed, WaDI will simply try to fill up as many NaN values as
possible. Note that eight column pairs are selected for merging
and that these are grouped in a list. This means that the value
passed for :code:`merge_columns` must always be a nested list,
even if only one set of column names is passed.

The :code:`harmonizer` method also has a keyword argument
:code:`drop_columns`, which takes a list of column names that will
be deleted.

The :code:`target_units` keyword argument specifies what
(concentration) units will be used for the feature data. In this
case the values will be converted to 'mmol/l'. This value can be
overridden for individual columns with the :code:`override_units`
keyword argument. The code example below shows how this option can
be used to convert only the arsenic concentrations to μmol/l.

.. note::
    Behind the scenes, WaDI relies on Pint to convert the units. Any
    problems that it encountered will be recorded in the log file
    (messy_data.log in this example). It is strongly advised that the
    user always checks the log file to verify that no unexpected
    behavior occurred.

.. ipython:: python
    :okexcept:

    drop_cols = [
        "SampleID",
        "Unnamed: 17",
    ]

    override_units = {
        "Arsenic": "umol/l",
        "Arsenic.1": "umol/l",
        "ec": "µS/cm",
    }
    merge_cols = [
        ['Phosphate', 'Phosphate.1'],
        ['Nitraat', 'Nitrate'],
        ['Nitrite', 'Nitrite.1'],
        ['Ammonium', 'Ammonium.1'],
        ['Silica', 'Silica.1'],
        ['Sulphate', 'Sulphate.1'],
        ['Calcium', 'Calcium.1'],
        ['Arsenic', 'Arsenic.1'],
    ]
    df = wdo.harmonizer(
        merge_columns=merge_cols,
        drop_columns=drop_cols,
        convert_units=True,
        target_units="mmol/l",
        override_units=override_units,
    )

    df = wdo.get_converted_dataframe()
    df.head()

.. Displaying the DataFrame does not show the values for arsenic. To verify
.. that the values were converted correctly the column name can be specified

.. .. ipython:: python
..     :okexcept:
..     :okwarning:

..     df['As'].head()

Finally, the resulting DataFrame can be saved to an Excel file using the
:code:`to_excel` function.

.. ipython:: python
    :okexcept:

    df.to_excel('tidied_data.xlsx')
