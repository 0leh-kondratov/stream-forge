FROM registry.dmz.home/kinga/stream-forge/base:v0.1.2

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

CMD ["python", "-m", "app.main"]