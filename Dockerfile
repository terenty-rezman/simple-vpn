FROM python:3.8

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/code

RUN mkdir /code
WORKDIR /code

COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8777

COPY . /code/
ENTRYPOINT python3 server.py
