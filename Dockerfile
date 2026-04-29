FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose port
EXPOSE 8080

# Cloud Run requires PORT env variable
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
