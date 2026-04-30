"""
routers/segmentation.py — Customer segmentation endpoints.

Same router pattern as churn.py — read those comments first if you haven't.

Key difference here:
    Segmentation requires TWO loaded objects — the KMeans model AND the scaler.
    Both are injected via Depends(). FastAPI handles multiple dependencies
    cleanly — just add them as separate function arguments.
    
    The scaler MUST be the same one fitted during training. Applying a fresh 
    scaler would produce different scaled values → wrong cluster assignments.
"""

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from app.schemas import CustomerFeatures, SegmentResponse, SegmentSummary
from app.dependencies import get_segmentation_model, get_scaler
from src.utils import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Cluster label mapping — update these based on what you observed 
# when profiling your clusters in notebook 03.
# The numbers (0, 1, 2, 3) are what KMeans assigns.
# The strings are your human-readable business labels.
CLUSTER_LABELS = {
    0: "Champions",
    1: "Loyal Customers",
    2: "At Risk",
    3: "Lost / Inactive"
}

# Features used during segmentation training — must match notebook 03
SEGMENT_FEATURES = ['recency_log', 'frequency_log', 'monetary_log']


def prepare_segment_features(customer: CustomerFeatures) -> np.ndarray:
    """
    Transforms raw customer values into scaled features for KMeans.
    
    Steps:
    1. Log transform (same as training)
    2. Scale using the SAME fitted scaler from training
    
    Returns a numpy array ready for model.predict()
    """
    recency_log   = np.log1p(customer.recency)
    frequency_log = np.log1p(customer.frequency)
    monetary_log  = np.log1p(customer.monetary)

    return np.array([[recency_log, frequency_log, monetary_log]])


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/predict", response_model=SegmentResponse)
def predict_segment(
    customer : CustomerFeatures,
    model    = Depends(get_segmentation_model),   # KMeans model injected
    scaler   = Depends(get_scaler)                # Scaler injected
):
    """
    Classify a single customer into a segment.
    
    Returns:
    - cluster: integer cluster ID (0-3)
    - segment_label: human-readable label e.g. "Champions"
    - recency, frequency, monetary: the raw values for context
    
    How it works:
        1. Log transform raw RFM values
        2. Scale using the fitted scaler — scaler.transform()
        3. KMeans assigns the nearest cluster — model.predict()
        4. Map cluster integer to a business label
    """
    logger.info(f"Segmentation requested for customer {customer.customer_id}")

    try:
        X_raw    = prepare_segment_features(customer)
        X_scaled = scaler.transform(X_raw)          # scale AFTER log transform

        cluster       = int(model.predict(X_scaled)[0])
        segment_label = CLUSTER_LABELS.get(cluster, "Unknown")

        logger.info(
            f"Customer {customer.customer_id} → "
            f"Cluster {cluster} ({segment_label})"
        )

        return SegmentResponse(
            customer_id   = customer.customer_id,
            cluster       = cluster,
            segment_label = segment_label,
            recency       = customer.recency,
            frequency     = customer.frequency,
            monetary      = customer.monetary
        )

    except Exception as e:
        logger.error(f"Segmentation failed for customer {customer.customer_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")


@router.get("/segments", response_model=list[SegmentSummary])
def get_segments():
    """
    Returns a summary of all segments — labels, descriptions, and 
    what action to take for each.
    
    This is a static endpoint — it doesn't need a model, just returns
    the segment definitions you established from notebook 03 profiling.
    
    Useful for: dashboards, frontend dropdowns, business documentation.
    """
    logger.info("Segment summary requested")

    # Update avg_recency, avg_frequency, avg_monetary with the actual
    # values from your cluster profiling in notebook 03
    segments = [
        SegmentSummary(
            cluster=0, segment_label="Champions",
            total_customers=0,     # update from your actual data
            avg_recency=15.0,
            avg_frequency=12.0,
            avg_monetary=850.0
        ),
        SegmentSummary(
            cluster=1, segment_label="Loyal Customers",
            total_customers=0,
            avg_recency=45.0,
            avg_frequency=6.0,
            avg_monetary=400.0
        ),
        SegmentSummary(
            cluster=2, segment_label="At Risk",
            total_customers=0,
            avg_recency=120.0,
            avg_frequency=3.0,
            avg_monetary=180.0
        ),
        SegmentSummary(
            cluster=3, segment_label="Lost / Inactive",
            total_customers=0,
            avg_recency=280.0,
            avg_frequency=1.0,
            avg_monetary=45.0
        ),
    ]

    return segments