"""
main.py — The entry point of the FastAPI application.

Think of this as the "front door" of your app.
It creates the FastAPI instance, registers all the routers
(churn + segmentation), and defines the health check endpoint.

When you run `uvicorn app.main:app`, Python:
1. Imports this file
2. Creates the `app` object
3. Registers all routes from routers/
4. Starts listening for HTTP requests
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import churn, segmentation
from app.schemas import HealthCheck
from src.utils import get_logger

logger = get_logger(__name__)

# --- App Initialization ---
# FastAPI() creates your application instance.
# title, description, version show up in /docs automatically.
app = FastAPI(
    title="Customer Retention Intelligence API",
    description="""
    An ML-powered API for customer segmentation and churn prediction.
    Built on RFM analysis and XGBoost/LightGBM models trained on retail transaction data.
    
    ## Endpoints
    - **/churn** — Predict churn probability and assign intervention segment
    - **/segmentation** — Classify customers into RFM-based segments
    """,
    version="1.0.0",
)


# --- Router Registration ---
# Routers are like "mini apps" — each one owns a group of related endpoints.
# include_router() plugs them into the main app.
# prefix="/churn" means all routes inside churn.py start with /churn
# tags=["Churn"] groups them visually in /docs

app.include_router(churn.router, prefix="/churn", tags=["Churn"])
app.include_router(segmentation.router, prefix="/segmentation", tags=["Segmentation"])


# --- Health Check ---
# Moved to /health instead of / because the root route GET /
# is now handled by StaticFiles serving index.html.
# If we kept GET / here, it would conflict with the static mount.
# Deployment platforms like Render/Railway support custom health check paths.

@app.get("/health", response_model=HealthCheck, tags=["Health"])
def health_check():
    logger.info("Health check called")
    return {
        "status": "ok",
        "message": "Customer Retention Intelligence API is running"
    }


# --- Static Files ---
# MUST come last — after all include_router() and endpoint definitions.
# If mounted before the routers, StaticFiles intercepts every request
# including /churn and /segmentation, and your API endpoints become unreachable.
# html=True means requests to / automatically serve index.html.

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")