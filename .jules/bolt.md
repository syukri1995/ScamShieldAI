## 2024-05-18 - Optimize Keyword Frequency Extraction with SQLite json_each
**Learning:** Extracting and parsing JSON stored in text columns on the Python side (using `json.loads` in a loop) is extremely inefficient compared to using SQLite's native JSON extension, especially when paginating or limiting rows.
**Action:** Use SQLite's `json_each` to flatten and aggregate JSON arrays directly in the database query. This drastically reduces the overhead of serialization/deserialization and avoids sending unneeded data over the connection.

## 2024-05-19 - Caching Machine Learning Artifacts
**Learning:** Loading machine learning artifacts (e.g. via `joblib.load`) inside prediction functions on every request is a severe performance bottleneck due to continuous disk I/O and deserialization overhead.
**Action:** Use Python's built-in `@functools.lru_cache(maxsize=1)` decorator on the artifact loading function to ensure the model and vectorizer are read from disk only once and then kept in memory for subsequent predictions.
