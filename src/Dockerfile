FROM image-newrelic:latest

WORKDIR /code

COPY requirements.txt /code/requirements.txt

RUN pip install --upgrade -r /code/requirements.txt

COPY .env /code/.env
COPY . /code/src

CMD ["python3", "src/main.py"]

