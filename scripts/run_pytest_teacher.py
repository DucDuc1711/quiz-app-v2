import pytest
import sys
sys.exit(pytest.main(['-q', 'backend/tests/test_teacher.py', '--tb=short']))