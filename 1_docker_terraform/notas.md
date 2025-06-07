# Rodando PostgreSql em um Container

## 1. Imagem de teste rodando script python com parâmetros 

Aquivo Docker File de exemplo (ainda não vai ser usado no projeto):


``` 
FROM python:3.12

RUN pip install pandas

#Local no container onde o arquivo será copiado
WORKDIR /app
COPY pipeline.py pipeline.py

ENTRYPOINT [ "python", "pipeline.py"]

```

Contruindo a imagem:
`docker build -t test:pandas .`

Rodando em modo iterativo passando os 2 parâmetros "2025-04-27" e "pedro" que serão usados no arquivo `pipeline.py`
`docker run -it test:pandas 2025-04-27 pedro`


No arquivo `pipeline.py` usamos a lib sys para passar os parâmetros como `day = sys.argv[1]` que são passados no `docker run` acima.

## 2. Postgres

### 2.1. Baixando os dados:
Baixando os dado em csv através do link [informado aqui no repositório](https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/01-docker-terraform/2_docker_sql): https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz

usando `wget https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz -OutFile yellow_tripdata_2021-01.csv.gz`
`

### 2.2. Configurando o container com postgres com um docker volume

Para o dockerfile do postgres vamos precisar de montar um volume com o database.


#### Forma que não deu certo por causa que o PostgreSql não conseguia acessar a pastar depois e dava um erro:

Similar ao que foi feito aqui: https://rest-apis-flask.teclado.com/docs/flask_smorest/reload_api_docker_container/


Comando para rodar no terminal:

- Rodando no modo iterativo uma imagem do postgres, passando as variaveis de ambiente necessárias para o postgres
- Criando um volume, que mapeia uma pasta do computador em uma pasta do container (mas sem ser somente quando vc roda docker build, e sim de forma continua)
- Mapeando a porta do pc e do container para o postgres porta 5432


```
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v /mnt/c/Users/pedro/Programming/de_zoomcamp/1_docker_terraform/2_docker_sql/ny_taxy_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```



#### Forma que deu certo usando um docker volume:


A solução foi essa https://docs.google.com/document/d/19bnYs80DwuUimHM65UV3sylsCn2j1vziPOwzBwQrebw/edit?tab=t.0#heading=h.okhwu85s6cwk


```docker volume create --name dtc_postgres_volume_local```



```
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v dtc_postgres_volume_local:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```


```docker volume inspect dtc_postgres_volume_local```

You can spin up a temporary container to look inside:

```
docker run -it --rm \
  -v dtc_postgres_volume_local:/data \
  alpine sh
```

Then inside:

```ls /data```

O conteúdo do volume também pode ser acessado na área `volume` do Docker Desktop.

#### Como "entrar" no container novamente:

```
docker run -d \
  --name pg_ny_taxi \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v dtc_postgres_volume_local:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```

Em uma segunda run (após já ter criado o container 1x com o comando acima), você pode rodar o camando abaixo para reinicià-lo:

`docker start pg_ny_taxi`

Acessando o container do postgresql (chamado pg_ny_taxi) em modo iterativo, uma vez que ele já está rodando em dettached mode:

`docker exec -it pg_ny_taxi bash`


### 2.3. Conectando-se à database com `pgcli`

Conectando-se à database usando a lib `pgcli` (instalada com pip install pgcli)

`pgcli --help` para ver os parâmetros necessários para conectar-se à uma database

```
pgcli -h localhost -p 5432 -u root -d ny_taxy

pgcli -h <host> -p <port> -u <username> -d <database>

```

Depois disso ele vai te pedir para inserir o password, que no caso é foi definido como "root.

Agora, a inicialização do container do postgresql deve ser feita no modo dettached para que o container fique rodando, e daí o comando `pgcli -h localhost -p 5432 -u root -d ny_taxy` pode ser rodado no terminal, com o docker rodando (vc pode verificar que está rodando com `docker ps`). 


Uma vez dentro do container (com comando `docker exec` mencionado acima), logando no PostgreSql:

```
psql -U root -d ny_taxi
```

Listando as tabelas dentro da database
```
\dt 
```
### 2.4. Ingerindo os dados em notebook usando pandas sqlalchemy e psycopg2

Essa parte está no arquivo `ingest_data.ipynb`

**Criando a conexão com o sqlalchemy**


```
import pandas as pd
from sqlalchemy import create_engine
from time import time

## postgresql://user:password@host:port_number/database_name
engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')

engine.connect()

```

**Lendo as primeiras linhas**

`df = pd.read_csv('yellow_tripdata_2021-01.csv', nrows = 100)`

**Comando que gera o DDL para criar a tabela (não vamos usar por enquanto, ver prox item)**


```print(pd.io.sql.get_schema(df, name = 'yellow_taxi_data', con = engine))```

Esse comando, está usando o objeto engine da database, mas não está alterando nada nela. Ele só usa a engine para saber o "flavor" da database, e considerá-lo na expressão DDL (data definitinon language). Nesse caso a expressão gerada foi:

```
CREATE TABLE yellow_taxi_data (
	"VendorID" BIGINT, 
	tpep_pickup_datetime TIMESTAMP WITHOUT TIME ZONE, 
	tpep_dropoff_datetime TIMESTAMP WITHOUT TIME ZONE, 
	passenger_count BIGINT, 
	trip_distance FLOAT(53), 
	"RatecodeID" BIGINT, 
	store_and_fwd_flag TEXT, 
	"PULocationID" BIGINT, 
	"DOLocationID" BIGINT, 
	payment_type BIGINT, 
	fare_amount FLOAT(53), 
	extra FLOAT(53), 
	mta_tax FLOAT(53), 
	tip_amount FLOAT(53), 
	tolls_amount FLOAT(53), 
	improvement_surcharge FLOAT(53), 
	total_amount FLOAT(53), 
	congestion_surcharge FLOAT(53)
)

```

**Criando o schema da tabela no postgresql**

`df.head(0).to_sql(name= 'yellow_taxi_data', con = engine, if_exists="replace")`

**Lendo os dados de forma iterativa com pandas e fazendo a ingestão de forma iterativa**

Como temos muita linhas a forma de leitura abaixo permite ler em batches de 100000 linhas:

```
# lendo de forma iterativa:
df_iter = (pd.read_csv('yellow_tripdata_2021-01.csv', iterator = True, chunksize = 100000))

while True:
    t_start = time()
    
    # Passando para o proximo step da iteração
    df = next(df_iter)

    # Alterando os tipos das colunas datetime
    df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

    # Escrevendo no PostgreSql
    df.to_sql(name= 'yellow_taxi_data', con = engine, if_exists="append")

    t_end = time()

    print('inserted_another_chunk, took %.3f' % (t_end - t_start))

```


### 2.5 Explorando os dados

Ver se o container do postgresql está rodando
`docker ps`

Iniciando o container:
`docker start pg_ny_taxi`

Acessando o container uma vez que ele estiver rodando:
`docker exec -it pg_ny_taxi bash`

Uma vez dentro do container, acessando o postgresql:
`psql -U root -d ny_taxi`

listando as tabelas:
`\dt`

Descrevendo o schema da tabela 
`\d yellow_taxi_data;`

Select
`select * from yello_taxi_data limit 10`

Sair do resultado de uma query:
`q`

Sair do psql e voltar para o terminal do container:
`exit`

Sair do container e voltar para o terminal
`exit`

Parando o container
`docker stop cff` (primeiras letras do CONTAINER ID)


