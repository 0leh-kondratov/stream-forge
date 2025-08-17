FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN cat requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir opentelemetry-instrumentation-flask

COPY structured_logger.py .

CMD ["python", "structured_logger.py"]
