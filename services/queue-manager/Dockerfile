ARG SERVICE_PATH=services/queue-manager
FROM registry.dmz.home/kinga/stream-forge/base:v0.1.0

COPY $SERVICE_PATH/app /app/app
COPY $SERVICE_PATH/requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]