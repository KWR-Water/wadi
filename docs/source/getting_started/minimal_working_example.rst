Minimal working example
=======================

This example demonstrates how to import an Excel file with stacked
data. It does nothing other than to convert the data from 'stacked'
to 'wide' format. A more elaborate version of this example is given
in the :doc:`user guide section <../user_guide/index>`.

.. ipython:: python

    # Import the library
    import wadi as wd

Get the folder containing the data that is used within this documentation.

.. ipython:: python

    from wadi.documentation_helpers import get_data_dir
    DATA_DIRECTORY = get_data_dir()


.. ipython:: python

    # Create an instance of a WaDI DataObject, specify the log file name
    wdo = wd.DataObject(log_fname='minimal_usage.log', silent=True)

    # Import the data. The 'c_dict' dictionary specifies the column names
    # for the sample identifiers,  feature names, concentrations and units.
    wdo.file_reader(DATA_DIRECTORY / 'stacked_data.xlsx',
        format='stacked',
        c_dict={'SampleId': 'Sample number',
                'Features': 'Parameter description',
                'Units': 'Unit description',
                'Values': 'Reported value',
        },
    )

    # Get the converted DataFrame
    df = wdo.get_converted_dataframe()

    # Show the result
    df.head()

