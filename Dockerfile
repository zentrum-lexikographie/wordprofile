FROM python:3.7

RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY requirements-api.txt /app/requirements-api.txt

RUN pip install --no-cache-dir --upgrade\
    -r /app/requirements.txt\
    -r /app/requirements-api.txt

COPY . /app

CMD ["python", "-m", "wordprofile.apps.rest_api"]
