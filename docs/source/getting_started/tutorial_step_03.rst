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
of the :code:`map_names` method. By assigning the text string 
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

The code above did not generate any output but the result of the 
mapping is summarized in the file 'name_mapping_results_wadi_tutorial.xlsx'. 
In this file it can be seen that a match was found for Chloride, 
Sulpate and Calcium         (ICP-AES). All the other features will 
keep their original names.