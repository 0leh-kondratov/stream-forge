import logging
import json
import os
import time
import random
from flask import Flask, request, jsonify
from pythonjsonlogger import jsonlogger
from urllib.parse import urlparse, parse_qs

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Prometheus imports
from prometheus_client import generate_latest, Counter, Histogram, Gauge

# Get trace context from environment (propagated by GCP)
TRACE_HEADER = "x-cloud-trace-context"

# Configure logger
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
logHandler = logging.StreamHandler()

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['severity'] = record.levelname
        log_record['serviceContext'] = {
            'service': os.getenv('K_SERVICE', 'sample-logger-py'),
            'version': os.getenv('K_REVISION', '1.0.0')
        }
        log_record['env'] = os.getenv('APP_ENV', 'dev')
        log_record['tenant'] = os.getenv('TENANT', 'default')
        
        # Add trace context for Cloud Trace correlation
        tracer = trace.get_tracer(__name__)
        current_span = tracer.current_span()
        if current_span.get_context().is_valid:
            trace_id = current_span.get_context().trace_id
            span_id = current_span.get_context().span_id
            project_id = os.getenv('GCP_PROJECT_ID')
            if project_id:
                log_record['logging.googleapis.com/trace'] = f"projects/{project_id}/traces/{trace.format_trace_id(trace_id)}"
                log_record['logging.googleapis.com/spanId'] = trace.format_span_id(span_id)
                log_record['logging.googleapis.com/trace_sampled'] = current_span.get_context().trace_flags & 0x01

        # Rename fields to match GCP conventions
        if 'levelname' in log_record:
            del log_record['levelname']
        if 'message' not in log_record and 'msg' in log_record:
            log_record['message'] = log_record['msg']

formatter = CustomJsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
logHandler.setFormatter(formatter)
log.addHandler(logHandler)

# OpenTelemetry setup
resource = Resource.create({
    "service.name": os.getenv('K_SERVICE', 'sample-logger-py'),
    "service.version": os.getenv('K_REVISION', '1.0.0'),
    "env": os.getenv('APP_ENV', 'dev'),
    "tenant": os.getenv('TENANT', 'default'),
    "project_id": os.getenv('GCP_PROJECT_ID', 'unknown')
})

trace.set_tracer_provider(
    TracerProvider(resource=resource)
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(CloudTraceSpanExporter())
)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# Prometheus Metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 'Total HTTP Requests',
    ['method', 'endpoint', 'status_code']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 'HTTP Request Latency',
    ['method', 'endpoint']
)
ERROR_COUNT = Counter(
    'http_errors_total', 'Total HTTP Errors',
    ['method', 'endpoint']
)
ACTIVE_REQUESTS = Gauge(
    'http_active_requests', 'Number of active HTTP requests'
)

@app.before_request
def before_request():
    ACTIVE_REQUESTS.inc()
    request.start_time = time.time()

@app.after_request
def after_request(response):
    ACTIVE_REQUESTS.dec()
    latency = time.time() - request.start_time
    method = request.method
    endpoint = request.path
    status_code = response.status_code

    REQUEST_COUNT.labels(method, endpoint, status_code).inc()
    REQUEST_LATENCY.labels(method, endpoint).observe(latency)

    if status_code >= 400:
        ERROR_COUNT.labels(method, endpoint).inc()
    
    return response

@app.route('/healthz')
def healthz():
    log.debug("Health check successful", extra={"http_path": "/healthz"})
    return "ok", 200

@app.route('/metrics')
def metrics():
    return generate_latest(), 200

@app.route('/')
def index():
    is_error = request.args.get("error", None)
    
    with trace.get_tracer(__name__).start_as_current_span("index-request-processing") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.path", request.path)
        span.set_attribute("request_id", request.headers.get("x-request-id", "N/A"))

        if is_error:
            log.error("Simulated internal server error", extra={"http_path": request.path, "status": 500})
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Simulated error"))
            return "Internal Server Error", 500
        else:
            log.info("Request processed successfully", extra={"http_path": request.path, "status": 200})
            return "Work done successfully", 200

if __name__ == "__main__":
    if not os.getenv('GCP_PROJECT_ID'):
        log.warning("GCP_PROJECT_ID environment variable not set. Trace correlation will be affected.")
    
    app.run(host='0.0.0.0', port=8080)