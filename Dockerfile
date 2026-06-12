# FastAPI backend image for Trendy Topic.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

# Only the pieces the API needs at runtime (frontend + tests excluded via .dockerignore).
COPY src ./src
COPY api ./api
COPY data ./data
COPY sql ./sql

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
