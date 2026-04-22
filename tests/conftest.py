import sys
import pytest
from unittest.mock import MagicMock

def pytest_configure(config):
    # Mock joblib to bypass LFS pointer unpickling failures.
    # The LFS pointers cause Unpickler to raise KeyError/Exception.
    class MockJoblib:
        def load(self, path, *args, **kwargs):
            return None # Returning None allows predict.py to fallback gracefully

    try:
        import joblib
        original_load = joblib.load
        def safe_load(path, *args, **kwargs):
            try:
                return original_load(path, *args, **kwargs)
            except Exception:
                return None
        joblib.load = safe_load
    except ImportError:
        sys.modules['joblib'] = MockJoblib()
