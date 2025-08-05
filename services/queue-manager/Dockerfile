FROM registry.dmz.home/kinga/stream-forge/base:v0.1.0

COPY app /app/app
COPY requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]