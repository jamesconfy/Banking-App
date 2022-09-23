FROM python:3.10.4-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5000

CMD [ "gunicorn" "--bind" "0.0.0.0:5000" "run:app" ]