FROM python:3.10.4-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8080

ENV PORT 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 run:app