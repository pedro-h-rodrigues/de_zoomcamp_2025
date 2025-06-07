FROM python:3.12

RUN pip install pandas

#Local no container onde o arquivo será copiado
WORKDIR /app
COPY pipeline.py pipeline.py

ENTRYPOINT [ "python", "pipeline.py"]
