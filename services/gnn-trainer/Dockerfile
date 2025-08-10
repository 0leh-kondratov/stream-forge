FROM registry.dmz.home/kinga/stream-forge/base:v0.1.3

WORKDIR /app

# Install system dependencies for PyTorch Geometric (if any, usually handled by base image or pip)
# For example, if using a non-slim base image, you might need: 
# RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Copy and install service-specific Python dependencies
COPY services/gnn-trainer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/gnn-trainer/app ./app

# Default command to run the application
CMD ["python", "-m", "app.main"]
