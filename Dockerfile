FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /gamexbackend

WORKDIR /gamexbackend

COPY ./ ./
RUN pip install -r requirements.txt

