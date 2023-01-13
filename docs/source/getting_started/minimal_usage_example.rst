Minimal usage example
=====================

This example demonstrates how to import an Excel file with stacked 
data. It does nothing other than to convert the data from 'stacked'
to 'wide' format. The dictionary passed with the :code:`c_dict`
argument informs WaDI about the names of the columns that contain 
the sample identifiers,  feature names, as well as the concentrations 
and units.

.. ipython:: python
    :okexcept:
    :okwarning:

    # Import the library
    import wadi as wd

    # Create an instance of a WaDI DataObject
    wdo = wd.DataObject(log_fname='minimal_usage.log', silent=True)

    # Import the data
    wdo.file_reader('tutorial_data.xlsx',
        format='stacked',
        c_dict={'SampleId': 'Sample number',
                'Features': 'Parameter description',
                'Units': 'Unit description',
                'Values': 'Reported value',
        },
    )

    # Process the data (converts from 'stacked' to 'wide' format)
    df = wdo.get_frame()

    # Show the result
    df.head()

More complex examples that show the full functionality of WaDI are 
given in the :doc:`user guide section <../user_guide/index>`.