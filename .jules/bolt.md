## 2024-05-18 - Optimize Keyword Frequency Extraction with SQLite json_each
**Learning:** Extracting and parsing JSON stored in text columns on the Python side (using `json.loads` in a loop) is extremely inefficient compared to using SQLite's native JSON extension, especially when paginating or limiting rows.
**Action:** Use SQLite's `json_each` to flatten and aggregate JSON arrays directly in the database query. This drastically reduces the overhead of serialization/deserialization and avoids sending unneeded data over the connection.

## 2024-05-19 - Cache Model Artifacts to Avoid Redundant Disk I/O
**Learning:** In the `predict_text` function within `model/predict.py`, the ML model and vectorizer were being loaded from disk using `joblib.load()` on *every* single prediction request. Disk I/O is very slow compared to memory access.
**Action:** Use Python's built-in `functools.lru_cache(maxsize=1)` decorator on the `_load_artifacts` function. This caches the loaded objects in memory, reducing prediction overhead drastically when handling multiple requests.
