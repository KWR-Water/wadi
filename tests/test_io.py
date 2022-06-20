import sys
sys.path.append('..')

import pytest

import wadi as wd

def test_check_format_valid_strings():
    wi = wd.Importer()
    assert wi._check_format('s') == 'stacked'
    assert wi._check_format('w') == 'wide'
    assert wi._check_format('g') == 'gef'

    
