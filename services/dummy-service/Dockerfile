FROM registry.dmz.home/kinga/stream-forge/base:v0.1.3

WORKDIR /app

COPY services/dummy-service/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY services/dummy-service/app ./app

CMD ["python", "-m", "app.main"]