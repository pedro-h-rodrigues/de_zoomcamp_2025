FROM python:3.12

RUN pip install pandas sqlalchemy psycopg2 requests
#Local no container onde o arquivo será copiado
WORKDIR /app
COPY ingest_data.py ingest_data.py

ENTRYPOINT [ "python", "ingest_data.py"]
