FROM python:3.10

WORKDIR /workers

COPY requirements.txt requirements.txt

RUN pip install -U pip

RUN pip install -r requirements.txt 

ADD . /workers

CMD celery  -A project worker --loglevel=info --pool=gevent -Q semantic --concurrency=25