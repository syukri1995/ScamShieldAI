import sys
from unittest.mock import MagicMock

def pytest_configure():
    # Only mock if they aren't already available in the environment
    # This is a safer way to handle missing dependencies in constrained environments
    # without poisoning a healthy environment.

    missing_deps = []

    for mod in ["networkx", "pyvis", "pyvis.network", "joblib", "sklearn",
                "sklearn.feature_extraction", "sklearn.feature_extraction.text",
                "sklearn.linear_model", "numpy", "pandas", "openai", "dotenv", "altair"]:
        try:
            __import__(mod)
        except ImportError:
            missing_deps.append(mod)
            sys.modules[mod] = MagicMock()

    if missing_deps:
        print(f"\nNOTE: The following dependencies were missing and have been mocked for tests: {', '.join(missing_deps)}")
