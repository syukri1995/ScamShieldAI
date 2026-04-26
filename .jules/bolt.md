## 2024-05-18 - Optimize Keyword Frequency Extraction with SQLite json_each
**Learning:** Extracting and parsing JSON stored in text columns on the Python side (using `json.loads` in a loop) is extremely inefficient compared to using SQLite's native JSON extension, especially when paginating or limiting rows.
**Action:** Use SQLite's `json_each` to flatten and aggregate JSON arrays directly in the database query. This drastically reduces the overhead of serialization/deserialization and avoids sending unneeded data over the connection.

## 2024-05-18 - Optimize Pickled ML Model Loading with memory caching
**Learning:** Pickling a scikit-learn model and loading it from disk via `joblib.load` at every request is highly inefficient and creates an IO bottleneck taking ~1.5s per prediction.
**Action:** Use global variables to cache model and vectorizer loading into memory instead of reloading them on every call. Avoid `functools.lru_cache` since it would cache `(None, None)` if called before the model is fully trained, making it impossible to refresh the cache without restarting the server.

## 2024-11-20 - Pre-compile Regex in `rules.py` for Faster Text Analysis
**Learning:** For performance-sensitive string matching tasks (like repeatedly extracting URLs from messages using `re.findall` or `re.search`), inline compilation of regex expressions causes noticeable overhead compared to declaring a pre-compiled `re.compile()` object at the module level.
**Action:** When implementing new text analyzers or loops involving repetitive regex evaluation, always define pre-compiled pattern objects at the top of the file to improve processing throughput.
