import os
from setuptools import setup, find_packages

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

setup(
    name='wadi',
    version='0.1.3',
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='Generic importer for water quality data of the (Dutch) water laboratory',
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Hydrology',
    ],
    python_requires='>=3.9',
    project_urls={
    'Source': 'https://github.com/KWR-Water/wadi',
    'Documentation': 'http://wadi.readthedocs.io/en/latest/',
    'Tracker': 'https://github.com/KWR-Water/wadi/issues',
    'Help': 'https://github.com/KWR-Water/wadi/issues'
    },
    install_requires=[
        'pandas>=0.23',
        'pint',
        'requests',
        'molmass',
        'openpyxl>=3.0.0',
        'googletrans',
        'fuzzywuzzy'
        ],
    include_package_data=True,
    url='https://github.com/KWR-Water/wadi',
    author='KWR Water Research Institute',
    author_email='martin.korevaar@kwrwater.nl, martin.van.der.schans@kwrwater.nl',
)
