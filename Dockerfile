FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY app/ ./app/
COPY src/ ./src/
COPY models/ ./models/
COPY data/processed/ ./data/processed/

# Expose port
EXPOSE 8000

# Run the API
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
