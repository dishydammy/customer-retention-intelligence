import io
import csv
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from app.schemas import CustomerFeatures, BatchRequest, ChurnResponse, BatchChurnResponse
from app.dependencies import get_churn_model
from src.utils import get_logger, assign_intervention

logger = get_logger(__name__)

router = APIRouter()

FEATURES = [
    'recency_log', 'frequency_log', 'monetary_log',
    'r_score', 'f_score', 'm_score', 'rfm_score'
]


def prepare_features(customer: CustomerFeatures) -> pd.DataFrame:
    """
    Converts a CustomerFeatures Pydantic object into a DataFrame
    the model can predict on.
    
    Log transforms are applied here — same transformation used during training.
    RFM scores are derived from the raw values using simple rules.
    """
    recency_log   = np.log1p(customer.recency)
    frequency_log = np.log1p(customer.frequency)
    monetary_log  = np.log1p(customer.monetary)

    # Simple score assignment — mirrors training logic
    # In production you'd load the fitted score bins from disk
    r_score = max(1, min(5, int(5 - (customer.recency / 100))))
    f_score = max(1, min(5, int(customer.frequency / 2)))
    m_score = max(1, min(5, int(customer.monetary / 200)))
    rfm_score = r_score + f_score + m_score

    data = {
        'recency_log'              : [recency_log],
        'frequency_log'            : [frequency_log],
        'monetary_log'             : [monetary_log],
        'r_score'                  : [r_score],
        'f_score'                  : [f_score],
        'm_score'                  : [m_score],
        'rfm_score'                : [rfm_score],
    }

    return pd.DataFrame(data)[FEATURES]


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/predict", response_model=ChurnResponse)
def predict_churn(
    customer : CustomerFeatures,
    model    = Depends(get_churn_model)   # FastAPI injects the cached model here
):
    """
    Predict churn probability for a single customer.
    
    Returns:
    - churn_probability: float between 0 and 1
    - churn_predicted: 0 (not churned) or 1 (churned)
    - intervention: Save | Protect | Lost Cause | Maintain
    
    How it works:
        1. Pydantic validates the incoming JSON against CustomerFeatures
        2. FastAPI calls get_churn_model() via Depends — returns cached model
        3. prepare_features() transforms raw values into model-ready format
        4. model.predict_proba() returns [prob_not_churn, prob_churn]
        5. assign_intervention() maps probability + monetary to a segment
        6. Response is validated against ChurnResponse schema before returning
    """
    logger.info(f"Churn prediction requested for customer {customer.customer_id}")

    try:
        X = prepare_features(customer)

        churn_proba     = model.predict_proba(X)[0][1]    # probability of class 1 (churned)
        churn_predicted = int(model.predict(X)[0])

        intervention = assign_intervention(
            churn_probability=churn_proba,
            monetary=customer.monetary
        )

        logger.info(
            f"Customer {customer.customer_id} | "
            f"Churn prob: {churn_proba:.3f} | "
            f"Intervention: {intervention}"
        )

        return ChurnResponse(
            customer_id       = customer.customer_id,
            churn_probability = round(float(churn_proba), 4),
            churn_predicted   = churn_predicted,
            intervention      = intervention
        )

    except Exception as e:
        logger.error(f"Prediction failed for customer {customer.customer_id}: {e}")
        # HTTPException sends a proper HTTP error response with status code
        # Without this, FastAPI would return a 500 with no useful message
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict/batch", response_model=BatchChurnResponse)
def predict_churn_batch(
    batch : BatchRequest,
    model = Depends(get_churn_model)
):
    """
    Predict churn for multiple customers in one request.
    Loops over the customers list and calls the same prediction logic.
    
    Returns total count + list of individual predictions.
    """
    logger.info(f"Batch churn prediction requested for {len(batch.customers)} customers")

    predictions = []

    for customer in batch.customers:
        try:
            X = prepare_features(customer)

            churn_proba     = model.predict_proba(X)[0][1]
            churn_predicted = int(model.predict(X)[0])
            intervention    = assign_intervention(
                churn_probability=churn_proba,
                monetary=customer.monetary
            )

            predictions.append(ChurnResponse(
                customer_id       = customer.customer_id,
                churn_probability = round(float(churn_proba), 4),
                churn_predicted   = churn_predicted,
                intervention      = intervention
            ))

        except Exception as e:
            logger.error(f"Batch prediction failed for customer {customer.customer_id}: {e}")
            # We skip failed customers rather than failing the whole batch
            continue

    logger.info(f"Batch complete. {len(predictions)}/{len(batch.customers)} successful")

    return BatchChurnResponse(
        total_customers = len(predictions),
        predictions     = predictions
    )


@router.post("/predict/csv")
async def predict_churn_csv(
    file  : UploadFile = File(...),
    model = Depends(get_churn_model)
):
    """
    Batch churn prediction from a CSV file upload.

    How it works:
        1. Client uploads a CSV file via multipart/form-data
        2. FastAPI receives it as an UploadFile object
        3. We read the raw bytes, decode to string, parse with csv.DictReader
        4. Each row is validated and transformed into model features
        5. Predictions are written to a new in-memory CSV
        6. StreamingResponse sends the CSV back as a downloadable file

    Expected CSV columns (header row required):
        customer_id, recency, frequency, monetary

    Returns:
        A CSV file download with original columns + churn_probability,
        churn_predicted, intervention appended.

    UploadFile vs File:
        UploadFile gives you metadata (filename, content_type) + async read.
        File(...) means the field is required — no default.
        The `async` on the function is needed because file.read() is async.
    """
    # Validate file type before reading
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported. Please upload a .csv file."
        )

    logger.info(f"CSV batch prediction requested. File: {file.filename}")

    try:
        # Read file bytes and decode to string
        contents = await file.read()
        decoded  = contents.decode('utf-8')
        reader   = csv.DictReader(io.StringIO(decoded))

        # Validate required columns exist
        required_cols = {
            'customer_id', 'recency', 'frequency', 'monetary'
        }
        if not required_cols.issubset(set(reader.fieldnames or [])):
            missing = required_cols - set(reader.fieldnames or [])
            raise HTTPException(
                status_code=422,
                detail=f"CSV missing required columns: {missing}"
            )

        results  = []
        failures = 0

        for row in reader:
            try:
                customer = CustomerFeatures(
                    customer_id = row['customer_id'],
                    recency = float(row['recency']),
                    frequency = float(row['frequency']),
                    monetary = float(row['monetary']),
                )

                X = prepare_features(customer)
                churn_proba     = model.predict_proba(X)[0][1]
                churn_predicted = int(model.predict(X)[0])
                intervention    = assign_intervention(
                    churn_probability=churn_proba,
                    monetary=customer.monetary
                )

                results.append({
                    **row,                                          # original columns preserved
                    'churn_probability' : round(float(churn_proba), 4),
                    'churn_predicted'   : churn_predicted,
                    'intervention'      : intervention,
                })

            except Exception as e:
                logger.warning(f"Skipping row for customer {row.get('customer_id', '?')}: {e}")
                failures += 1
                continue

        logger.info(
            f"CSV batch complete. "
            f"{len(results)} successful, {failures} failed. "
            f"File: {file.filename}"
        )

        # Write results to an in-memory CSV string
        # StringIO is an in-memory file-like object — no disk writes needed
        output     = io.StringIO()
        if results:
            fieldnames = list(results[0].keys())
            writer     = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        output.seek(0)  # rewind to start before reading

        # StreamingResponse sends the CSV as a downloadable file
        # media_type tells the browser what kind of file it is
        # Content-Disposition: attachment triggers a file download
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=churn_predictions.csv"
            }
        )

    except HTTPException:
        raise   # re-raise our own validation errors unchanged
    except Exception as e:
        logger.error(f"CSV batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"CSV processing failed: {str(e)}")
