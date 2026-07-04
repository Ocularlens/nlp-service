# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system dependencies required for building Python packages and spaCy
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy language model
RUN python -m spacy download en_core_web_sm


# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:server", "--host", "0.0.0.0", "--port", "8000"]