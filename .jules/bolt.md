## 2024-05-18 - Optimize Keyword Frequency Extraction with SQLite json_each
**Learning:** Extracting and parsing JSON stored in text columns on the Python side (using `json.loads` in a loop) is extremely inefficient compared to using SQLite's native JSON extension, especially when paginating or limiting rows.
**Action:** Use SQLite's `json_each` to flatten and aggregate JSON arrays directly in the database query. This drastically reduces the overhead of serialization/deserialization and avoids sending unneeded data over the connection.

## 2025-02-26 - Optimize Model Artifact Loading
**Learning:** The ML model artifacts (`model.pkl` and `vectorizer.pkl`) were being loaded from disk via `joblib.load()` on *every single* call to `predict_text()`. This redundant disk I/O and object deserialization became a significant bottleneck during high-volume processing.
**Action:** Use `@functools.lru_cache(maxsize=1)` on the `_load_artifacts` function. This caches the loaded scikit-learn models in memory after the first read, effectively eliminating the I/O bottleneck for subsequent predictions.
