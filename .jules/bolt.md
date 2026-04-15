## 2024-05-18 - Optimize Keyword Frequency Extraction with SQLite json_each
**Learning:** Extracting and parsing JSON stored in text columns on the Python side (using `json.loads` in a loop) is extremely inefficient compared to using SQLite's native JSON extension, especially when paginating or limiting rows.
**Action:** Use SQLite's `json_each` to flatten and aggregate JSON arrays directly in the database query. This drastically reduces the overhead of serialization/deserialization and avoids sending unneeded data over the connection.
## 2024-05-18 - Caching model prediction artifacts
**Learning:** The ML model and vectorizer in `predict.py` are loaded redundantly from disk via `joblib.load()` on every single text analysis request. In this environment, disk I/O for these artifacts adds ~0.1s latency per call.
**Action:** Apply `functools.lru_cache` to the artifact loading function (`_load_artifacts`) so they are read from disk once and persisted in memory for all subsequent predictions.
