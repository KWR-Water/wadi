Step 4: Harmonize the data
--------------------------

The :code:`harmonizer` method can do a number of things (combining 
features, deleting features, converting units). Here it will be 
called to convert the data format from 'stacked' to 'wide' and to
convert all chemical concentrations to mg/l by setting 
:code:`convert_units` to True (the default is False).

.. ipython:: python
    :okexcept:
    :okwarning:

    df = wdo.harmonizer(convert_units=True, 
        target_units='mmol/l',
    )

    df = wdo.get_frame()
    df.head()

Note that the concentrations for the organic substances were below
the detection limit and were reported with a comma as a decimal 
separator. The :code:`harmonize` method automatically recognizes
the '<' symbol, as well as the decimal separator, and converts the
concentration value to the target units.