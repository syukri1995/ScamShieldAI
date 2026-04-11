## 2024-05-18 - Optimize Keyword Frequency Extraction with SQLite json_each
**Learning:** Extracting and parsing JSON stored in text columns on the Python side (using `json.loads` in a loop) is extremely inefficient compared to using SQLite's native JSON extension, especially when paginating or limiting rows.
**Action:** Use SQLite's `json_each` to flatten and aggregate JSON arrays directly in the database query. This drastically reduces the overhead of serialization/deserialization and avoids sending unneeded data over the connection.

## 2024-05-18 - Optimize Literal String Search in Pandas
**Learning:** By default, `pandas.Series.str.contains` evaluates the search string as a regular expression. When filtering user input (like a plain text search query), this introduces significant overhead and potential security vulnerabilities (ReDoS, invalid regex errors).
**Action:** Always explicitly set `regex=False` when performing literal substring searches using `pandas.Series.str.contains`.
