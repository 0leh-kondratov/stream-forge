FROM registry.dmz.home/kinga/stream-forge/base:v0.1.3

WORKDIR /app

# Copy and install service-specific Python dependencies
COPY services/queue-manager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/queue-manager/app ./app

# Default command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
