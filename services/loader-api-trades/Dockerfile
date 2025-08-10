FROM registry.dmz.home/kinga/stream-forge/base:v0.1.3

WORKDIR /app

# Copy and install service-specific Python dependencies
COPY services/loader-api-trades/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/loader-api-trades/app ./app

# Default command to run the application
CMD ["python", "-m", "app.main"]