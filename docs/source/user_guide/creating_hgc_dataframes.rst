Creating HGC compatible DataFrames
==================================

WaDI is intended to be a generic processor of hydrochemical data but also
offers special support for `HGC <https://github.com/KWR-Water/hgc>`_,
which is a package for correction, validation and analysis of groundwater
quality samples. An example workflow for reading data from a spreadsheet
file in wide format is provided below. It demonstrates two key features

* how to use WaDI's default dictionary to map the feature names to HGC feature names
* automatic unit conversion to HGC compatible units

As always, the first step is to define the WaDI :code:`DataObject` that will
perform the required steps. As can be seen from the function arguments, the
name of the log file will be 'hgc_compatible.log' and no messages will be
printed to the screen because the :code:`silent` keyword argument is set
to :code:`True`.

.. ipython:: python
    :okexcept:

    import wadi as wd

    wdo = wd.DataObject(log_fname='hgc_compatible.log',
        silent=True,
    )

Second, the :code:`file_reader` of the :code:`DataObject` must understand the
structure of the spreadsheet file. As explained in
:doc:`example 2 <../user_guide/example_02>`, this is done by creating
dictionaries with keyword arguments which enable importing multiple
different 'blocks' of data from the file. Here, the general sample data
(sample code, location, sampling date) are found in columns A through E
and the feature data in columns F through N. A separate dictionary needs to
be created for both.

.. ipython:: python
    :okexcept:

    df0_kwargs = {
        "skiprows": [1],
        "usecols": "A:E",
        "units_row": 1,
        "datatype": "sampleinfo",
    }

    df1_kwargs = {
        "skiprows": [1],
        "usecols": "F:N",
        "units_row": 1,
        "datatype": "feature",
    }

As can be seen from the items in both dictionaries defined above,
:code:`"skiprows": [1]` is provided so that the second row of the spreadsheet
is not read when reading the concentration (or sample info) data. This is
because the second row contains the units. This row must be read separately,
which is accomplished by also passing :code:`"units_row": 1`.

With these dictionaries defined, the :code:`file_reader` can be initialized
and the result of the import operation can be visualized by printing the
contents of the imported DataFrame

For the purpose of the demonstration in this documentation, find the folder
with the data files

.. ipython:: python
    :okexcept:

    from wadi.documentation_helpers import get_data_dir
    DATA_DIRECTORY = get_data_dir()

.. ipython:: python
    :okexcept:

    wdo.file_reader(
        file_path=DATA_DIRECTORY / "hgc_example.xlsx",
        format="wide",
        blocks=[df0_kwargs, df1_kwargs],
    )

    print(wdo.get_imported_dataframe().head())

The next step is to define a mapping dictionary. WaDI's default dictionary
already contains the HGC names for features. In this case, the feature names provided
in the spreadsheet are according to the Dutch SIKB standard, which are also known to
WaDI's default database (see :doc:`example 2 <../user_guide/mapping_dictionaries>`).

The mapping dictionary is created by calling the :code:`default_dict` function
of the MapperDict object, with the arguments 'SIKB' and 'HGC'. The resulting dictionary
is stored under the variable name :code:`names_dict`, which is then used
to initialize the :code:`name_map` of the WaDI :code:`DataObject`. The
selected match methods are 'exact' and 'fuzzy', with the latter being
included because it is case insensitive.

.. ipython:: python
    :okexcept:

    names_dict = wd.mapper.MapperDict.default_dict('SIKB', 'HGC')

    wdo.name_map(
        m_dict=names_dict,
        match_method=["exact", "fuzzy"],
    )

The final step before the data can be converted is to define the
:code:`harmonizer`. The :code:`convert_units` argument needs to be
set to :code:`True` and instead of specifying chemical concentration
units, the :code:`target_units` are set to 'hgc'. WaDI then understands
that it must convert the feature units to values that are prescribed in
HGC, which are different for different species (for example, mg/l for
chloride, but ug/l for bromide).

.. ipython:: python
    :okexcept:

    df = wdo.harmonizer(
        convert_units=True,
        target_units="hgc",
    )

The data can now be converted and displayed on the screen.

.. ipython:: python
    :okexcept:

    df = wdo.get_converted_dataframe()

    print(df.head())

The user should always check the contents of the DataFrame created
by WaDI to ensure that the mapping and harmonzing operations yielded
the desired results. This is why it is critically important to inspect
the conversion results, especially the column names, the units and the
concentrations before proceeding with doing any calculations in HGC!

HGC requires a DataFrame without the units. This can be created
by setting the :code:`include_units` argument of the
:code:`get_converted_dataframe` function to :code:`False`.

.. ipython:: python
    :okexcept:

    df_hgc = wdo.get_converted_dataframe(include_units=False)

    print(df_hgc.head())
