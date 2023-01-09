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

    wdo = wd.DataObject(log_fname='wadi_tutorial.log')

The DataObject class instance is stored as :code:`wdo`, which will be used
in the next step to read the data from the spreadsheet file.