# Hospital Management - Django web app container
FROM python:3.12-slim AS web

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy Django app
COPY . .

# Create non-root user
RUN useradd -r -u 1001 appuser
RUN chown -R appuser:appuser /app

USER appuser

# Environment
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=hospitalmanagement.settings

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/admin/')" || exit 1

# Run Django with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "hospitalmanagement.wsgi:application"]
