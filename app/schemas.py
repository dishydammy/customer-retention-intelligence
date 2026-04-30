"""
schemas.py — Pydantic request and response models.

What Pydantic does:
    It validates data automatically. When a request arrives at an endpoint,
    FastAPI feeds it through the matching Pydantic model. If a field is missing,
    the wrong type, or fails a constraint (like ge=0), FastAPI returns a 422
    error BEFORE your code ever runs. Your model only sees clean, valid data.

Two categories here:
    - Request schemas  → shape of data coming INTO your endpoints
    - Response schemas → shape of data going OUT of your endpoints

response_model= in your route decorators uses these response schemas
to validate and serialise what your endpoint returns.
"""

from pydantic import BaseModel, Field


# REQUEST SCHEMAS — Data coming INTO endpoints

class CustomerFeatures(BaseModel):
    """
    Input schema for a single customer prediction.
    Used by both /churn/predict and /segmentation/predict.
    
    Field(...) means the field is REQUIRED — no default value.
    ge=0 means >= 0. gt=0 means > 0. These are enforced automatically.
    """
    customer_id              : str
    recency                  : float = Field(..., ge=0,  description="Days since last purchase")
    frequency                : float = Field(..., gt=0,  description="Number of unique invoices")
    monetary                 : float = Field(..., gt=0,  description="Total spend in GBP")


    class Config:
        # This populates the example in /docs Swagger UI
        # Makes testing your API much easier — one click to fill the form
        json_schema_extra = {
            "example": {
                "customer_id": "12345",
                "recency": 14.0,
                "frequency": 8.0,
                "monetary": 420.50,
            }
        }


class BatchRequest(BaseModel):
    """
    Input schema for batch predictions.
    Wraps a list of CustomerFeatures — send multiple customers at once.
    """
    customers: list[CustomerFeatures]

    class Config:
        json_schema_extra = {
            "example": {
                "customers": [
                    {
                        "customer_id": "12345",
                        "recency": 14.0,
                        "frequency": 8.0,
                        "monetary": 420.50,
                    },
                    {
                        "customer_id": "67890",
                        "recency": 200.0,
                        "frequency": 1.0,
                        "monetary": 35.0,
                    }
                ]
            }
        }


# =============================================================================
# RESPONSE SCHEMAS — Data going OUT of endpoints
# =============================================================================

class HealthCheck(BaseModel):
    """Response for GET / health check endpoint."""
    status  : str
    message : str


class ChurnResponse(BaseModel):
    """
    Response for single churn prediction.
    churn_predicted is 0 (not churned) or 1 (churned).
    intervention is one of: Save, Lost Cause, Protect, Maintain.
    """
    customer_id        : str
    churn_probability  : float
    churn_predicted    : int
    intervention       : str


class BatchChurnResponse(BaseModel):
    """
    Response for batch churn prediction.
    Returns total count + list of individual ChurnResponse objects.
    """
    total_customers : int
    predictions     : list[ChurnResponse]


class SegmentResponse(BaseModel):
    """Response for single customer segmentation."""
    customer_id   : str
    cluster       : int
    segment_label : str
    recency       : float
    frequency     : float
    monetary      : float


class SegmentSummary(BaseModel):
    """
    Response for GET /segmentation/segments.
    Summarises each cluster — avg RFM stats + customer count.
    """
    cluster         : int
    segment_label   : str
    total_customers : int
    avg_recency     : float
    avg_frequency   : float
    avg_monetary    : float