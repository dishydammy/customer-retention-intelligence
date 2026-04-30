import joblib
from functools import lru_cache
from src.utils import get_logger

logger = get_logger(__name__)

# --- Model Paths ---
CHURN_MODEL_PATH       = "models/churn_model.pkl"
SEGMENTATION_MODEL_PATH = "models/segmentation_model.pkl"
SCALER_PATH            = "models/scaler.pkl"


@lru_cache(maxsize=1)
def get_churn_model():
    """
    Loads and caches the churn prediction model.
    Called once at startup, cached for all subsequent requests.
    """
    logger.info(f"Loading churn model from {CHURN_MODEL_PATH}")
    try:
        model = joblib.load(CHURN_MODEL_PATH)
        logger.info("Churn model loaded successfully")
        return model
    except FileNotFoundError:
        logger.error(f"Churn model not found at {CHURN_MODEL_PATH}")
        raise


@lru_cache(maxsize=1)
def get_segmentation_model():
    """
    Loads and caches the KMeans segmentation model.
    """
    logger.info(f"Loading segmentation model from {SEGMENTATION_MODEL_PATH}")
    try:
        model = joblib.load(SEGMENTATION_MODEL_PATH)
        logger.info("Segmentation model loaded successfully")
        return model
    except FileNotFoundError:
        logger.error(f"Segmentation model not found at {SEGMENTATION_MODEL_PATH}")
        raise


@lru_cache(maxsize=1)
def get_scaler():
    """
    Loads and caches the StandardScaler used during segmentation.
    The scaler must be the SAME one fitted during training — 
    using a new scaler would produce wrong cluster assignments.
    """
    logger.info(f"Loading scaler from {SCALER_PATH}")
    try:
        scaler = joblib.load(SCALER_PATH)
        logger.info("Scaler loaded successfully")
        return scaler
    except FileNotFoundError:
        logger.error(f"Scaler not found at {SCALER_PATH}")
        raise