# Customer Retention Intelligence

Customer Retention Intelligence is a FastAPI application for retention operations: churn prediction, customer segmentation, and CSV batch scoring. It combines pretrained machine learning artifacts with a lightweight browser frontend so the same service can be used as an API, an internal analyst tool, or a public demo.

Live deployment: https://customer-retention-intelligence-1.onrender.com/

## What It Does

The app turns simple RFM inputs into operational outputs:

- churn prediction returns a churn probability, a binary churn flag, and a recommended intervention
- segmentation returns a cluster ID and a human-readable segment label
- batch scoring accepts a CSV upload and returns a scored CSV for download

The root route serves the frontend, while the API remains available for programmatic use.

## Highlights

- FastAPI backend with typed request and response schemas
- cached model loading through `joblib` and `functools.lru_cache`
- single-customer churn and segmentation prediction endpoints
- batch CSV churn scoring endpoint
- static frontend served from `/` with health, prediction, and upload workflows
- pre-trained artifacts in `models/` for churn, segmentation, and scaling
- notebooks, charts, and presentation assets for the broader analysis story
- Docker support and a Render-friendly startup command

## Project Structure

```text
customer-retention-intelligence/
├── app/
│   ├── main.py
│   ├── dependencies.py
│   ├── schemas.py
│   ├── routers/
│   │   ├── churn.py
│   │   └── segmentation.py
│   └── static/
│       └── index.html
├── data/
│   ├── raw/
│   │   └── OnlineRetail.csv
│   └── processed/
│       ├── customer_clean.csv
│       ├── customers_scored_churn.csv
│       ├── rfm.csv
│       └── rfm_segmented.csv
├── models/
│   ├── churn_model.pkl
│   ├── segmentation_model.pkl
│   └── scaler.pkl
├── notebooks/
│   ├── eda.ipynb
│   ├── rfm_analysis.ipynb
│   ├── Segmentation.ipynb
│   └── churn_prediction.ipynb
├── reports/
│   └── figures/
├── customer-retention-presentation/
│   └── slide-presentation.pptx
├── src/
│   ├── data_processing.py
│   ├── rfm.py
│   ├── segmentation.py
│   ├── churn_model.py
│   └── utils.py
├── tests/
├── requirements.txt
└── Dockerfile
```

## How It Works

The runtime API is built around a simple RFM feature set:

- `recency` = days since last purchase
- `frequency` = number of purchases or invoices
- `monetary` = total spend

For churn prediction, the service log-transforms the inputs, derives simple R/F/M scores, and feeds the features into the saved classifier. It then maps the churn probability and monetary value into an action label:

- Save
- Lost Cause
- Protect
- Maintain

For segmentation, the service log-transforms the same raw inputs, scales them with the saved scaler, and predicts the customer cluster with the saved KMeans model. The cluster is then translated into a business label:

- Champions
- Loyal Customers
- At Risk
- Lost / Inactive

## API Reference

### Health

`GET /health`

Returns a simple service status payload used by deployment health checks and the frontend status chip.

### Single Churn Prediction

`POST /churn/predict`

Request body:

```json
{
  "customer_id": "12345",
  "recency": 14,
  "frequency": 8,
  "monetary": 420.5
}
```

Response includes:

- `customer_id`
- `churn_probability`
- `churn_predicted`
- `intervention`

### Batch Churn Prediction

`POST /churn/predict/batch`

Request body:

```json
{
  "customers": [
    {
      "customer_id": "12345",
      "recency": 14,
      "frequency": 8,
      "monetary": 420.5
    },
    {
      "customer_id": "67890",
      "recency": 120,
      "frequency": 2,
      "monetary": 75
    }
  ]
}
```

Returns `total_customers` plus a list of individual churn responses.

### CSV Churn Scoring

`POST /churn/predict/csv`

Upload a CSV with these required columns:

```text
customer_id,recency,frequency,monetary
```

The response is a downloadable CSV with these extra columns appended:

```text
churn_probability,churn_predicted,intervention
```

### Single Segmentation Prediction

`POST /segmentation/predict`

Request body:

```json
{
  "customer_id": "12345",
  "recency": 14,
  "frequency": 8,
  "monetary": 420.5
}
```

Response includes:

- `customer_id`
- `cluster`
- `segment_label`
- `recency`
- `frequency`
- `monetary`

### Segment Reference

`GET /segmentation/segments`

Returns the current segment labels plus summary statistics used by the frontend.

## Frontend

The browser frontend at `/` is intentionally operational rather than decorative. It supports:

- live service health checks
- single-customer churn prediction
- single-customer segmentation
- CSV upload for batch churn scoring
- downloadable scored CSV output
- a segment reference panel sourced from `/segmentation/segments`

## Local Setup

### 1. Create and activate a virtual environment

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
uvicorn app.main:app --reload
```

The app will be available at:

- Frontend: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Docker

Build the image:

```bash
docker build -t customer-retention-intelligence .
```

Run the container:

```bash
docker run -p 8000:8000 customer-retention-intelligence
```

The container listens on the platform-provided `PORT` when it is set, which makes it compatible with managed platforms such as Render.

## Deployment

### Render

The project is already deployed on Render at:

https://customer-retention-intelligence-1.onrender.com/

For a source-based Render service, use:

```bash
pip install -r requirements.txt
```

as the build command and:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

as the start command, with `/health` as the health check path.

You can also deploy the repository as a Docker service and let Render build from the included `Dockerfile`.

## Analysis Assets

The application is backed by the broader retention analysis workflow in the repository:

- `notebooks/eda.ipynb` explores revenue concentration, seasonality, and customer behavior
- `notebooks/rfm_analysis.ipynb` covers RFM construction and segmentation heuristics
- `notebooks/Segmentation.ipynb` profiles clusters and maps them to business labels
- `notebooks/churn_prediction.ipynb` documents the churn modeling workflow
- `reports/figures/` contains exported charts used in the reporting narrative
- `customer-retention-presentation/output/output.pptx` is the packaged presentation deck

## Data and Model Artifacts

- `data/raw/OnlineRetail.csv` is the raw retail transaction source
- `data/processed/customer_clean.csv` is the cleaned transaction dataset
- `data/processed/rfm.csv` and `data/processed/rfm_segmented.csv` are the downstream analysis outputs
- `models/churn_model.pkl`, `models/segmentation_model.pkl`, and `models/scaler.pkl` are required at runtime

## Notes

- The segment summary endpoint currently returns static cluster summaries rather than live aggregates from a database.
- The saved model artifacts may emit version warnings if they were trained with a different scikit-learn release than the one installed at runtime.
- The `tests/` folder is currently empty, so there is no automated test suite documented in this repository yet.
