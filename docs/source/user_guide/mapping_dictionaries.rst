Creating mapping dictionaries
=============================

When mapping feature names to their alias, WaDI uses a dictionary, of which
the keys are the feature names and the values the corresponding aliases.
There are several options to create a mapping dictionary, which will be
demonstrated in the examples below

Using the default dictionary
----------------------------

The first option is to use the default dictionary, which is bundled with
WaDI and has been developed by Martin van der Schans at KWR. It contains
a curated collection of feature names, CAS numbers and PubChem Identifiers
(CIDs) for a large number of chemical substances. The dictionary is stored
in the file `default_feature_map.json`. Specifically, it contains substance
names according to the following systems:

 - SIKB
 - NVWA
 - REWAB
 - HGC
 - PubChem CIDs
 - CAS numbers

In addition to this, there are also English and Dutch synonyms for substances
that have multiple names. Creating the default dictionary is done with the
following command:

.. ipython:: python
    :okexcept:

    import wadi as wd

    names_dict = wd.mapper.MapperDict.default_dict('REWAB', 'ValidCid')


As can be inferred from the arguments passed to the default_dict function,
the names according to the REWAB system will be used to search for features
and they will be converted to a PubChem CID. Information about the dictionary
contents can be obtained by printing it to the screen

.. ipython:: python
    :okexcept:

    print(names_dict)

Note that there are four synonyms for chloorfenvinfos that will all map to
the same CID (10107).

The use of the mapping dictionaries will be demonstrated using the spreadsheet
file `mapping_example.xlsx`. The following code instructs WaDI what columns
to look for in the spreadsheet file in order to be able to import the data.

.. ipython:: python

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

Let's print the names of the imported features and create a for loop to
see what aliases will be used if a name appears in the dictionary.

.. ipython:: python
    :okexcept:

    names = wdo.get_imported_dataframe()["parameter"]
    print(names)

    for name in names:
        print(name, "will be mapped to", names_dict.get(name))

To actually perform the mapping, a name_map must be added to the WaDI
DataObject :code:`wdo`. By calling :code:`get_converted_dataframe` and printing
the returned DataFrame, the result of the mapping operation can be
inspected

.. ipython:: python
    :okexcept:

    wdo.name_map(m_dict=names_dict)
    df = wdo.get_converted_dataframe()

    print(df.head())

Instead of the original feature names, the column names in the converted
DataFrame are now the PubChem CIDs.

Querying PubChem for CIDs
-------------------------

The above example works for features that are contained in WaDI's default
database. When importing features that are not in there, CIDs can be looked
up directly in the online PubChem database by creating a mapping dictionary
with the :code:`pubchem_cid_dict` function. The first argument for this
function is a list of strings, in this case the list :code:`names` with
the original feature names. For each of the strings, WaDI tries to obtain
the CID by contacting the PubChem online database. Because PubChem uses
English names, translation is necessary for feature names in another language,
in this case Dutch. Therefore the source language may be specified with the
:code:`src_lang` argument. WaDI will use the Google Translate API to determine
the English feature name. However, translations may be unreliable and may
not yield the desired result. In this example, the feature name `koper` is
Dutch for the element `copper` but Google Translate finds the English word
`buyer`, which is another, equally valid, meaning of the Dutch word `koper` (
see :ref:`Creating a translation dictionary<translation-dict>`).
The user should therefore proceed with extreme caution when using this
functionality!

.. ipython:: python

    names_dict = wd.mapper.MapperDict.pubchem_cid_dict(names, src_lang="NL")

    print(names_dict)

    wdo.name_map(m_dict=names_dict)
    df = wdo.get_converted_dataframe()
    print(df.head())

As in the previous example, the column names are now the PubChem CID, except
for copper (`koper`).

Querying PubChem for CAS numbers
--------------------------------

Just like the function :code:`pubchem_cid_dict` can be used to look up
CIDs, the function  :code:`pubchem_cas_dict` can be invoked to look up
CAS numbers in PubChem.

.. ipython:: python

    names_dict = wd.mapper.MapperDict.pubchem_cas_dict(names, src_lang="NL")

    print(names_dict)

    wdo.name_map(m_dict=names_dict)
    df = wdo.get_converted_dataframe()
    print(df.head())

The column names are now the CAS numbers that could be retrieved. When
no CAS number could be determined (such as for `koper`), the original
feature name is retained as the column heading.

.. _translation-dict:

Creating a translation dictionary
---------------------------------

In the previous examples, the translation of the original feature names to
English was done internally by WaDI. This functionality can also be used
to create a mapping dictionary that translates feature names from one
language into another. The function to create this dictionary is
:code:`translation_dict` and is demonstrated in the following code snippet

.. ipython:: python

    names_dict = wd.mapper.MapperDict.translation_dict(names,
        src_lang="NL",
        dst_lang="EN",
    )

    print(names_dict)

    wdo.name_map(m_dict=names_dict)
    df = wdo.get_converted_dataframe()
    print(df.head())

The new column names are now the English names that Google Translate
provided. The Dutch feature name `koper` has been translated to `buyer`,
which stricly speaking is correct, but from a chemical point of view, this
is obviously not the desired result. Future versions of WaDI will incorporate
a better translation service when it becomes available. Until then, the user
must proceed with extreme caution when using the WaDI features that require
translation.