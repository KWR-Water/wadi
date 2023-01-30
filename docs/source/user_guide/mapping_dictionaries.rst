Creating mapping dictionaries
=============================

.. .. ipython:: python

..     import wadi as wd

..     m_dict = wd.MapperDict.default_dict('SIKB', 'ValidCid')
..     m_dict = {k, v for i, (k, v) in enumerate(m_dict.items())}
..     for i, (key, value) in enumerate(m_dict.items()):
..         print(key,value)

..     .. t_dict = m_dict.translate_keys()
..     .. print(t_dict.keys())
