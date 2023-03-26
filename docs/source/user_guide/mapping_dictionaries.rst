Creating mapping dictionaries
=============================

Using the default dictionary
----------------------------

.. ipython:: python
    :okexcept:
    :okwarning:

    # Import the library
    import wadi as wd

    # Create an instance of a WaDI DataObject, specify the log file name
    wdo = wd.DataObject(log_fname='mapping_example.log', silent=True)

    # Import the data. The 'c_dict' dictionary specifies the column names
    # for the sample identifiers,  feature names, concentrations and units.
    wdo.file_reader('mapping_example.xlsx',
        format='stacked',
        c_dict={'SampleId': 'sample_code',
                'Features': 'parameter',
                'Units': 'dimensie',
                'Values': 'waarde',
        },
    )

    names_dict = wd.mapper.MapperDict.default_dict('REWAB', 'ValidCid')

    # Print the names of the imported features
    names = wdo.get_imported_dataframe()["parameter"]
    print(names)

    # Show the result
    for name in names:
        print(name, "will be mapped to", names_dict.get(name))

    wdo.name_map(m_dict=names_dict)
    df = wdo.get_converted_dataframe()
    
    print(df.head())

Querying PubChem for CIDs
-------------------------

.. ipython:: python
    :okexcept:
    :okwarning:

    names_dict = wd.mapper.MapperDict.pubchem_cid_dict(names, src_lang="NL")

    print(names_dict)

    wdo.name_map(m_dict=names_dict)
    df = wdo.get_converted_dataframe()
    print(df.head())

Querying PubChem for CAS numbers
--------------------------------

.. ipython:: python
    :okexcept:
    :okwarning:

    names_dict = wd.mapper.MapperDict.pubchem_cas_dict(names, src_lang="NL")

    print(names_dict)

    wdo.name_map(m_dict=names_dict)
    df = wdo.get_converted_dataframe()
    print(df.head())

Creating a translation dictionary
---------------------------------

.. ipython:: python
    :okexcept:
    :okwarning:

    names_dict = wd.mapper.MapperDict.translation_dict(names,
        src_lang="NL",
        dst_lang="EN",
    )

    print(names_dict)

    wdo.name_map(m_dict=names_dict)
    df = wdo.get_converted_dataframe()
    print(df.head())

