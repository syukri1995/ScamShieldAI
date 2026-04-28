## 2024-05-18 - Optimize Keyword Frequency Extraction with SQLite json_each
**Learning:** Extracting and parsing JSON stored in text columns on the Python side (using `json.loads` in a loop) is extremely inefficient compared to using SQLite's native JSON extension, especially when paginating or limiting rows.
**Action:** Use SQLite's `json_each` to flatten and aggregate JSON arrays directly in the database query. This drastically reduces the overhead of serialization/deserialization and avoids sending unneeded data over the connection.

## 2024-05-18 - Optimize Pickled ML Model Loading with memory caching
**Learning:** Pickling a scikit-learn model and loading it from disk via `joblib.load` at every request is highly inefficient and creates an IO bottleneck taking ~1.5s per prediction.
**Action:** Use global variables to cache model and vectorizer loading into memory instead of reloading them on every call. Avoid `functools.lru_cache` since it would cache `(None, None)` if called before the model is fully trained, making it impossible to refresh the cache without restarting the server.

## 2024-05-18 - Optimize URL extraction with pre-compiled regex
**Learning:** Python's inline regex compilation (`re.findall(pattern)`) inside loops or frequently called functions is noticeably slower than pre-compiling (`pattern = re.compile()`) at the module level. Furthermore, doing repeated conversion from `list` to `set` for deduplication adds overhead that can be avoided by simply using a `set` natively from the beginning.
**Action:** Always pre-compile regex patterns at the module level for string matching algorithms that run frequently. Use native sets for uniqueness tracking rather than intermediate lists.
