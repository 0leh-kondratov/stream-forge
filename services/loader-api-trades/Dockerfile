ARG SERVICE_PATH=services/loader-api-trades
FROM registry.dmz.home/kinga/stream-forge/base:v0.1.0

COPY $SERVICE_PATH/app /app/app
COPY $SERVICE_PATH/requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["python", "-m", "app.main"]
