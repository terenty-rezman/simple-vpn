FROM python:3.8

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/code

RUN mkdir /code
WORKDIR /code

RUN apt update && \
    apt install -y iptables iproute2 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8777

COPY . /code/
ENTRYPOINT python3 server.py
