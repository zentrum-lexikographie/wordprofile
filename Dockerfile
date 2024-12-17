FROM python:3.12

RUN mkdir /app
WORKDIR /app

COPY Pipfile Pipfile.lock /app/

RUN pip install pipenv
RUN pipenv requirements --categories="packages api" > requirements.txt
RUN pip install -r requirements.txt
COPY . /app

CMD ["python", "-m", "wordprofile.apps.rest_api"]
