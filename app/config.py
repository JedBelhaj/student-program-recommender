"""Configuration settings for the recommendation API."""

from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

# Data files
USERS_FILE = DATA_DIR / "raw" / "users.csv"
PROGRAMS_FILE = DATA_DIR / "raw" / "programs.csv"
INTERACTIONS_FILE = DATA_DIR / "raw" / "interactions.csv"

# Model files
TFIDF_VECTORIZER = MODEL_DIR / "tfidf.pkl"
TFIDF_MATRIX = MODEL_DIR / "program_tfidf.pkl"
CF_MODEL = MODEL_DIR / "cf_svd.pkl"
HYBRID_MODEL = MODEL_DIR / "hybrid_recommender.pkl"

# Feedback log
FEEDBACK_LOG = DATA_DIR / "processed" / "feedback_log.csv"

# Recommendation settings
DEFAULT_K = 5
HYBRID_CONTENT_WEIGHT = 0.6
HYBRID_CF_WEIGHT = 0.4
