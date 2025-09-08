# syntax=docker/dockerfile:1.7-labs
# Pinned base image by tag; for full determinism, replace with digest in your registry
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    DB_PATH=/app/data/urlshort.db

WORKDIR /app

# System deps (none required beyond base)

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY src ./src
COPY README.md ./

# Create non-root user
RUN useradd -m appuser && mkdir -p /app/logs /app/data && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
CMD ["python", "-m", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080"]
