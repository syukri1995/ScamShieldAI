# ScamShield AI

AI-Powered Scam and Fraud Detection Assistant built for a 9-day hackathon.

## Features
- Analyze suspicious text/email/URL input
- Generate risk score (0-100)
- Explain suspicious signals
- Save scan history in SQLite
- Show dashboard analytics

## Tech Stack
- Frontend: Streamlit
- ML: scikit-learn (TF-IDF + Logistic Regression)
- Database: SQLite
- Language: Python

## Quick Start
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Train model artifacts using raw datasets in `data/`:
   ```bash
   python -m model.train_model
   ```
   The trainer reads:
   - `data/SMSSpamCollection`
   - `data/PhishingEmailDataset.csv`

   Optional: control phishing sampling size for faster runs:
   ```bash
   PHISHING_SAMPLE_SIZE=120000 python -m model.train_model
   ```
3. Run app:
   ```bash
   streamlit run app.py
   ```

## Project Structure
- `app.py`: Streamlit entrypoint
- `ui/`: Analyzer, History, Dashboard pages
- `model/`: training, prediction, rules
- `database/`: SQLite init and queries
- `services/`: orchestration layer
- `tests/`: unit and flow tests

## Notes
- If `model.pkl`/`vectorizer.pkl` do not exist, the app uses a lightweight heuristic fallback for scoring.
- `PhishingEmailDataset.csv` is large; lower `PHISHING_SAMPLE_SIZE` if your machine is memory constrained.
