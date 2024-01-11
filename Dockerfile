FROM python:3.9.18-alpine

WORKDIR rss-handler-hack

COPY main.py requirements.txt .
RUN pip install -r requirements.txt

USER 1000
CMD ["python3", "main.py"]
