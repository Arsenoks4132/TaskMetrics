FROM python:3.12

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY .env ./
COPY docker/django/entrypoint.sh /usr/src/app/entrypoint.sh

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x /usr/src/app/entrypoint.sh
