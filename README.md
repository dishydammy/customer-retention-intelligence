# Customer Retention Intelligence

Customer Retention Intelligence is a FastAPI application for two practical retention workflows:

- predicting customer churn probability and assigning a recommended intervention
- classifying customers into RFM-based behavioral segments

The project includes trained model artifacts, a browser-based frontend for operators, and API endpoints for direct integration into dashboards, internal tools, or automation pipelines.

Alongside the application, the repository includes the exploratory notebooks, saved report figures, and a polished project presentation that turns the modeling work into business recommendations for stakeholders.

## What the project does

This application turns simple customer RFM inputs into business-ready outputs:

- `Churn prediction`: returns a churn probability, a binary churn flag, and an intervention label
- `Customer segmentation`: returns a cluster ID and a human-readable segment label
- `Batch scoring`: accepts a CSV upload and returns a scored CSV

The root route `/` serves the frontend, and the API remains available for programmatic use.

## Features

- FastAPI backend with typed request and response schemas
- Static frontend for single-customer analysis and CSV batch uploads
- Health endpoint for deployment monitoring
- Pretrained churn, segmentation, and scaler artifacts in `models/`
- Exploratory notebooks in `notebooks/` and report charts in `reports/figures/`
- Business presentation deck in `deliverables/customer-retention-presentation/output/output.pptx`
- Docker support for container deployments
- Ready for platforms like Render and Railway

## Project structure

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
├── models/
│   ├── churn_model.pkl
│   ├── segmentation_model.pkl
│   └── scaler.pkl
├── deliverables/
│   └── customer-retention-presentation/
│       ├── output/
│       │   └── output.pptx
│       └── scratch/
│           └── previews/
├── src/
│   ├── churn_model.py
│   ├── segmentation.py
│   ├── rfm.py
│   ├── data_processing.py
│   └── utils.py
├── notebooks/
├── reports/
├── requirements.txt
└── Dockerfile
```

## Tech stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- scikit-learn
- pandas
- NumPy
- joblib

## Local setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd customer-retention-intelligence
```

### 2. Create and activate a virtual environment

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

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
uvicorn app.main:app --reload
```

The application will be available at:

- Frontend: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## Frontend overview

The frontend at `/` is intentionally simple and operational. It supports:

- single-customer churn prediction
- single-customer segmentation
- CSV upload for batch churn scoring
- live API health display
- segment summary display from the backend

This makes the project usable both as an API and as a lightweight internal tool.

## Analysis and business story

The predictive services in this repo come from a broader retention analysis workflow captured in the notebooks and report visuals:

- `notebooks/eda.ipynb`: commercial footprint, seasonality, order timing, and revenue concentration
- `notebooks/rfm_analysis.ipynb`: customer value analysis, RFM segmentation heuristics, and cohort retention
- `notebooks/Segmentation.ipynb`: KMeans clustering, cluster profiling, and segment interpretation
- `notebooks/churn_prediction.ipynb`: churn labeling approach, model comparison, and final evaluation
- `reports/figures/`: exported charts used in the final presentation and business review

Key business takeaways from the analysis:

- the top 20% of customers contribute about `74.64%` of revenue
- the known-customer revenue base in the analysis is about `$8.88M`
- retention decays quickly after the first purchase month, making second-order conversion a critical lifecycle objective
- the largest customer group is not the most valuable; the highest value pool sits inside the best recent, frequent, high-spend customers
- the churn model is useful for prioritizing outreach and intervention, but should be used with business rules rather than as a fully automatic decision engine

## Presentation deliverable

The repository includes a stakeholder-ready PowerPoint presentation at:

- [output.pptx](/Users/damola/Desktop/customer-retention-intelligence/deliverables/customer-retention-presentation/output/output.pptx)

Supporting artifacts for the presentation build live here:

- deck source: [build_deck.mjs](/Users/damola/Desktop/customer-retention-intelligence/deliverables/customer-retention-presentation/src/build_deck.mjs)
- preview renders: `deliverables/customer-retention-presentation/scratch/previews/`
- packaged QA report: `deliverables/customer-retention-presentation/scratch/quality-report.json`

The presentation covers:

- business context and commercial concentration
- seasonality and demand timing
- cohort retention behavior
- RFM data preparation and why normalization matters
- customer segment economics and recommended retention plays
- churn model performance and how to use it operationally
- a 90-day action plan for activation, retention, and win-back

## API overview

### Health

`GET /health`

Response:

```json
{
  "status": "ok",
  "message": "Customer Retention Intelligence API is running"
}
```

### Churn prediction

`POST /churn/predict`

Request:

```json
{
  "customer_id": "12345",
  "recency": 14,
  "frequency": 8,
  "monetary": 420.5
}
```

Response:

```json
{
  "customer_id": "12345",
  "churn_probability": 0.36,
  "churn_predicted": 0,
  "intervention": "Protect"
}
```

### Batch churn prediction

`POST /churn/predict/batch`

Request:

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

### CSV churn scoring

`POST /churn/predict/csv`

Upload a `.csv` file with these required columns:

```text
customer_id,recency,frequency,monetary
```

The response is a downloadable CSV containing the original columns plus:

```text
churn_probability,churn_predicted,intervention
```

### Segmentation

`POST /segmentation/predict`

Request:

```json
{
  "customer_id": "12345",
  "recency": 14,
  "frequency": 8,
  "monetary": 420.5
}
```

Response:

```json
{
  "customer_id": "12345",
  "cluster": 2,
  "segment_label": "At Risk",
  "recency": 14,
  "frequency": 8,
  "monetary": 420.5
}
```

### Segment summaries

`GET /segmentation/segments`

Returns the available clusters and their summary statistics.

## Example curl commands

Single churn prediction:

```bash
curl -X POST "http://127.0.0.1:8000/churn/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "12345",
    "recency": 14,
    "frequency": 8,
    "monetary": 420.5
  }'
```

Single segmentation prediction:

```bash
curl -X POST "http://127.0.0.1:8000/segmentation/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "12345",
    "recency": 14,
    "frequency": 8,
    "monetary": 420.5
  }'
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Running with Docker

Build the image:

```bash
docker build -t customer-retention-intelligence .
```

Run the container:

```bash
docker run -p 8000:8000 customer-retention-intelligence
```

The Docker image now respects the platform-provided `PORT` environment variable, which is useful for managed deployments.

## Deploying to Render

### Option 1: Native Python service

Use this if you want a simple deploy without building a container.

- Create a new `Web Service`
- Connect your GitHub repository
- Environment: `Python 3`
- Build command:

```bash
pip install -r requirements.txt
```

- Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Health check path:

```text
/health
```

Recommended settings:

- Instance type: starter or above
- Auto deploy: on
- Root directory: leave blank unless this repo becomes a monorepo

### Option 2: Docker service

Use this if you want Render to build from the included `Dockerfile`.

- Create a new `Web Service`
- Choose `Docker`
- Point it to this repository
- Set health check path to `/health`

Render will provide `PORT`, and the container is already configured to use it.

## Deploying to Railway

### Option 1: Deploy from source

- Create a new project in Railway
- Link the repository
- Set the start command to:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Ensure the install step uses:

```bash
pip install -r requirements.txt
```

### Option 2: Deploy with Docker

- Create a new Railway project from the repository
- Let Railway detect the `Dockerfile`

Railway will inject `PORT`, and the app will bind correctly.

## Deployment checklist

Before pushing to Render or Railway, confirm:

- `models/` is committed and available in the repository
- `app/static/index.html` is present so the frontend can be served
- `requirements.txt` is up to date
- `GET /health` returns `200 OK`
- the repo size is acceptable for your deployment platform

## Known notes

- The saved model artifacts may emit scikit-learn version warnings if they were trained with a different version than the one installed at runtime. If that happens, the safest fix is to retrain or re-export the models under the same scikit-learn version used in production.
- The current segment summary endpoint returns static summary values. If you want live values from a scored dataset later, that can be added as a follow-up enhancement.

## Future improvements

- add authentication for internal deployments
- store batch scoring results in object storage
- add request logging and monitoring
- add model version metadata to responses
- expose richer analytics charts from the generated reports

## License

Add your preferred license here before publishing the repository.
