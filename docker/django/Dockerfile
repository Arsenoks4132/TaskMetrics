FROM python:3.12

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY .env ./

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
