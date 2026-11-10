import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import pytest
sys.exit(pytest.main(['-q', 'tests/test_play.py', '--tb=short']))