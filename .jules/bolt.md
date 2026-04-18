## 2024-05-18 - Optimize Keyword Frequency Extraction with SQLite json_each
**Learning:** Extracting and parsing JSON stored in text columns on the Python side (using `json.loads` in a loop) is extremely inefficient compared to using SQLite's native JSON extension, especially when paginating or limiting rows.
**Action:** Use SQLite's `json_each` to flatten and aggregate JSON arrays directly in the database query. This drastically reduces the overhead of serialization/deserialization and avoids sending unneeded data over the connection.

## 2024-05-18 - Optimize Pickled ML Model Loading with memory caching
**Learning:** Pickling a scikit-learn model and loading it from disk via `joblib.load` at every request is highly inefficient and creates an IO bottleneck taking ~1.5s per prediction.
**Action:** Use global variables to cache model and vectorizer loading into memory instead of reloading them on every call. Avoid `functools.lru_cache` since it would cache `(None, None)` if called before the model is fully trained, making it impossible to refresh the cache without restarting the server.

## 2024-06-25 - Optimize URL extraction with Pre-Compiled Regex
**Learning:** For performance-sensitive string matching, pre-compiling regex patterns at the module level is the preferred architectural pattern. It avoids the overhead of Python's internal regex caching dictionary lookups on every function call. Benchmarking in this environment showed that `text.lower()` combined with a pre-compiled regex is significantly faster than inline compilation or using the `re.IGNORECASE` flag for URL extraction.
**Action:** Replace inline `re.findall(r"...", text)` with module-level `PATTERN = re.compile(r"...")` and use `PATTERN.findall(text)` across the codebase.
