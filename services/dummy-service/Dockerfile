# Declare a build argument for base image
ARG BASE_IMAGE

# Use the base image dynamically provided via build args
FROM ${BASE_IMAGE}

# Set working directory inside the container
WORKDIR /app

# Copy Python dependency file
COPY services/dummy-service/requirements.txt .

# Install dependencies with pip
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy service source code
COPY services/dummy-service .

# Default command to run when container starts
CMD ["python", "main.py"]
