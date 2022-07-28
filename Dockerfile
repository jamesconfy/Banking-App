FROM python:3.10.4-slim

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 5008

CMD [ "gunicorn", "--bind",  "0.0.0.0:5008", "run:app"]