# Production Dockerfile for SpeakSharp Core API
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
# Using psycopg-binary (pure Python) - no system dependencies needed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy database migrations
COPY database/ ./database/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.api2:app", "--host", "0.0.0.0", "--port", "8000"]
