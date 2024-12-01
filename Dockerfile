FROM python:3.11-alpine

WORKDIR /code

COPY requirements.txt /code/requirements.txt

RUN pip install --upgrade -r /code/requirements.txt

COPY .env /code/.env
COPY newrelic.ini /code/newrelic.ini
COPY /src /code/src

CMD ["python3", "src/main.py"]