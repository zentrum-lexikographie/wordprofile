FROM python:3.7

RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

CMD ["python", "-m", "wordprofile.apps.xmlrpc_api"]
