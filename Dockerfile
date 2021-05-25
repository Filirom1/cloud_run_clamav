FROM python:3.9-slim

RUN apt-get update \
 && apt-get install -y clamav clamav-daemon \
 && rm -rf /var/lib/apt/lists/*

COPY clamd.conf /etc/clamav/clamd.conf

RUN freshclam

ENV PYTHONUNBUFFERED True

EXPOSE 3310
EXPOSE 8080

ENV PORT 8080

ENV APP_HOME /app
WORKDIR $APP_HOME
ENV PATH=$PATH:/.local/bin

RUN mkdir -p /app && chown clamav. /app

USER clamav

COPY requirements.txt ./

RUN pip install -r requirements.txt --user

COPY main.py ./
ENV PATH=$PATH:/var/lib/clamav/.local/bin
CMD ["python3", "main.py"]
