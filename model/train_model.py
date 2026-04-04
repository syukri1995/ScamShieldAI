import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
SMS_RAW_PATH = DATA_DIR / "SMSSpamCollection"
PHISHING_RAW_PATH = DATA_DIR / "PhishingEmailDataset.csv"
MODEL_PATH = BASE_DIR / "model.pkl"
VECTORIZER_PATH = BASE_DIR / "vectorizer.pkl"


def load_sms_dataset(path: Path) -> pd.DataFrame:
    # Normalize SMS labels to binary target expected by the classifier.
    if not path.exists():
        raise FileNotFoundError(f"Missing SMS dataset: {path}")
    df = pd.read_csv(path, sep="\t", header=None, names=["raw_label", "text"])
    df = df.dropna(subset=["raw_label", "text"])
    df["label"] = df["raw_label"].str.lower().map({"spam": 1, "ham": 0})
    df = df.dropna(subset=["label"])
    return df[["text", "label"]]


def load_phishing_dataset(path: Path, sample_size: int) -> pd.DataFrame:
    # Load URL-based phishing dataset and keep only valid binary labels.
    if not path.exists():
        raise FileNotFoundError(f"Missing phishing dataset: {path}")

    df = pd.read_csv(path, usecols=["url", "label"])
    df = df.rename(columns={"url": "text"})
    df = df.dropna(subset=["text", "label"])
    df["label"] = pd.to_numeric(df["label"], errors="coerce")
    df = df[df["label"].isin([0, 1])]

    # Keep training time practical while still using the dropped raw phishing file.
    if sample_size > 0 and len(df) > sample_size:
        df = (
            df.groupby("label", group_keys=False)
            .apply(
                lambda g: g.sample(
                    n=max(1, int(sample_size * len(g) / len(df))), random_state=42
                )
            )
            .reset_index(drop=True)
        )

    return df[["text", "label"]]


def load_combined_dataset() -> pd.DataFrame:
    # Merge SMS + phishing data into one training frame.
    phishing_sample_size = int(os.getenv("PHISHING_SAMPLE_SIZE", "120000"))
    sms_df = load_sms_dataset(SMS_RAW_PATH)
    phishing_df = load_phishing_dataset(PHISHING_RAW_PATH, phishing_sample_size)
    combined = pd.concat([sms_df, phishing_df], ignore_index=True)
    combined = combined.dropna(subset=["text", "label"])
    combined["label"] = combined["label"].astype(int)
    return combined


def train() -> None:
    # Train a TF-IDF + Logistic Regression baseline spam/phishing detector.
    df = load_combined_dataset()
    print(f"Training rows: {len(df)}")
    print(df["label"].value_counts().to_string())

    x_train, x_test, y_train, y_test = train_test_split(
        df["text"],
        df["label"],
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=20000, min_df=2)
    x_train_vec = vectorizer.fit_transform(x_train)
    x_test_vec = vectorizer.transform(x_test)

    model = LogisticRegression(max_iter=400, class_weight="balanced")
    model.fit(x_train_vec, y_train)

    # Print evaluation summary and persist artifacts for inference.
    y_pred = model.predict(x_test_vec)
    print(classification_report(y_test, y_pred, digits=3))

    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved vectorizer to {VECTORIZER_PATH}")


if __name__ == "__main__":
    train()
