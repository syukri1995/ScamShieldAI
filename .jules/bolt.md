## 2024-05-18 - Optimize Keyword Frequency Extraction with SQLite json_each
**Learning:** Extracting and parsing JSON stored in text columns on the Python side (using `json.loads` in a loop) is extremely inefficient compared to using SQLite's native JSON extension, especially when paginating or limiting rows.
**Action:** Use SQLite's `json_each` to flatten and aggregate JSON arrays directly in the database query. This drastically reduces the overhead of serialization/deserialization and avoids sending unneeded data over the connection.

## 2024-05-18 - Optimize Pickled ML Model Loading with memory caching
**Learning:** Pickling a scikit-learn model and loading it from disk via `joblib.load` at every request is highly inefficient and creates an IO bottleneck taking ~1.5s per prediction.
**Action:** Use global variables to cache model and vectorizer loading into memory instead of reloading them on every call. Avoid `functools.lru_cache` since it would cache `(None, None)` if called before the model is fully trained, making it impossible to refresh the cache without restarting the server.

## 2024-10-24 - Pre-compile regex for regex-heavy URL detection
**Learning:** The previous implementation compiled the regular expression for URLs on every function call for detecting URLs in strings (`re.findall(r"...", text.lower())`). This leads to repetitive parsing logic and slower processing of text data, which in this codebase happens quite a lot when predicting scores and boosting score with heuristic rules on URLs.
**Action:** Always precompile heavily-used static regular expressions (like those used for matching URLs or patterns) into module-level properties so the compiled pattern is stored and re-used globally, improving runtime performance and minimizing standard library overhead.
