## 2024-05-18 - Optimize Keyword Frequency Extraction with SQLite json_each
**Learning:** Extracting and parsing JSON stored in text columns on the Python side (using `json.loads` in a loop) is extremely inefficient compared to using SQLite's native JSON extension, especially when paginating or limiting rows.
**Action:** Use SQLite's `json_each` to flatten and aggregate JSON arrays directly in the database query. This drastically reduces the overhead of serialization/deserialization and avoids sending unneeded data over the connection.

## 2024-05-18 - Optimize Pickled ML Model Loading with memory caching
**Learning:** Pickling a scikit-learn model and loading it from disk via `joblib.load` at every request is highly inefficient and creates an IO bottleneck taking ~1.5s per prediction.
**Action:** Use global variables to cache model and vectorizer loading into memory instead of reloading them on every call. Avoid `functools.lru_cache` since it would cache `(None, None)` if called before the model is fully trained, making it impossible to refresh the cache without restarting the server.

## 2024-05-18 - Optimize URL Matching and Flag Deduplication in Rules
**Learning:** Compiling regex inline (`re.findall(r"...", text)`) inside a function called frequently (like rule evaluation) creates a measurable CPU overhead due to internal regex dictionary caching and lookups. Furthermore, dynamically constructing a list of URL flags just to immediately call `set()` on them repeatedly throughout the score boosting and response payload generation is computationally wasteful.
**Action:** Always pre-compile regular expressions as module-level constants (`re.compile(r"...")`) when they are used in high-frequency string processing functions. Construct native `set()` collections instead of lists to inherently deduplicate items if uniqueness is the goal.
