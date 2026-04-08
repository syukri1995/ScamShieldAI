## 2025-05-15 - Cache ML model artifacts
**Learning:** Loading `joblib` artifacts (vectorizer and model) from disk on every prediction request represents a severe latency bottleneck in Streamlit applications where state is frequently re-run.
**Action:** Implemented `@functools.lru_cache(maxsize=1)` on the artifact loading function to cache the model in memory. This simple change reduces prediction latency by orders of magnitude and is safe due to the read-only nature of the loaded model.
