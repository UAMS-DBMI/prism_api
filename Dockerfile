FROM python:3

COPY ./app/requirements.txt /
RUN pip install -r /requirements.txt

COPY app/start.sh /
COPY ./app /app

WORKDIR /app
CMD ["/start.sh"]
