#  Must be the first line if we use it in FROM
ARG BASE_IMAGE

FROM ${BASE_IMAGE}

# Optionally redeclare if you use BASE_IMAGE later
ARG BASE_IMAGE

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app app
CMD ["python", "main.py"]
