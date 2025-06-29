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
pgcli -h localhost -p 5432 -u root -d ny_taxi

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

### 2.5 Integrando o banco com o pgAdmin

`pgAdmin` é uma ferramenta com um GUI que permite interagir com uma base Postegres de forma mais intuitiva do que usando o `pgcli` ou `psql` na CLI. (Link do site do pgAdmin)[https://www.pgadmin.org/]

Vamos baixar a imagem do pgAdmin no docker e usar um container para rodá-lo.


**comando para rodar o pgAdmin no docker**

Port mapping: Mapeia a porta 8080 da host machine com porta 80 do container.
O pgAdmin vai escutar a porta 80 e todas requisições que fizermos para a porta 8080 vão para a porta 80 do container.

Esse é o comando para rodar o container do pgAdmin

```
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  dpage/pgadmin4
```

Porém, é preciso fazer com que esse container se conecte com o container contendo a database postgres. É possível fazer essa conexão de duas formas, usando `network` ou `docker compose`.

Para acessar o pgAdmin basta acessar a porta 8080: `http://localhost:8080/`

#### 2.5.1 Integrando o pgAdmin com o banco usando network

https://docs.docker.com/reference/cli/docker/network/create/

`docker network create pg-network`

Agora o container do postgres deve ser alterado para informarmos que ele deve rodar nesta rede:

Precisamos de incluir duas informações:
- o nome da network a ser usada (a `pg-network` criada anteriormente)
- um nome para esse container (no caso defini `pg-database`, para passar no outro container do pgAdmin que vai se conectar com esse)

```
docker run -d \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v dtc_postgres_volume_local:/var/lib/postgresql/data \
  -p 5432:5432 \
  --network=pg-network \
  --name pg-database \
  postgres:13
```

```
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -p 8080:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4
```
Comando para saber as networks existentes: `docker network ls`

Uma vez criado os containers, para rodá-los de novo, bastaria rodar `docker start pg-database` e `docker start pgadmin`

### 2.6 Fazendo a ingestão via Docker 

### 2.6.1 Criando o script python de ingestão 

Vamos fazer a ingestão com um script python rodando em um container, ao invés de usar um notebook como feito no item 4.

Comando na CLI para converter um notebook em um script python `jupyter nbconvert --to=script ingest_data.ipynb`

Vamos usar uma lib default do python chamada [argparse](https://docs.python.org/3/library/argparse.html) para passar os parâmetros pra o script python.

Para rodar o script com os parâmetros direto na CLI, seria assim:

```
python ingest_data.py \
    --user=root \
    --password=root \
    --host=localhost \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_data \
    --url=https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz
```

Ver o script `ingest_data.py`

### 2.6.2 Dockerizando o script python de ingestão 

Para isso será necessário alterar o Dockerfile para:

```
FROM python:3.12

RUN pip install pandas sqlalchemy psycopg2 requests

#Local no container onde o arquivo será copiado
WORKDIR /app
COPY ingest_data.py ingest_data.py

ENTRYPOINT [ "python", "ingest_data.py"]
```

E o comando para criar o container `docker build -t taxi_ingest:v01 .`

E o comando para rodar o container:
- network=pg-network: informando a rede usada para relacionar os containers (é um parâmetro do container)
- host=pg-database: informa o host para o script se conectar (um parâmetro do script)

"This puts both containers (pg-database and taxi_ingest) on the same Docker bridge network. When containers are on the same network, they can talk to each other via container name."

```
docker run -it \
  --network=pg-network \
  taxi_ingest:v01 \
    --user=root \
    --password=root \
    --host=pg-database \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_data \
    --url=https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz
```

## 2.7 Integrando os containers com Docker Compose

É mais prático utilizar o docker-compose do que rodar 2 containers seperados e criar uma rede entre eles. Link desta etapa do projeto: https://www.youtube.com/watch?v=hKI6PkPhpa0&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=9

Comando para verificar que você possui o docker compose instalado `docker-compose`

Documentação do docker compose: https://docs.docker.com/compose/intro/compose-application-model/

Os mesmos parâmetros que foram passados para criar os containers "separados" são passados no yaml compose.yaml.
- Variáveis de ambiente (usuário, senha)
- Volume
- Portas

No volume, foi necessário especificar o parâmetro "external" para o docker-compose usar o volume que já havia sido criado anteriormente, ao invés de tentar criar um novo.

Cada container é um serviço no docker-compose, e pelo fato de já estarem no mesmo arquivo compose, eles já estão na mesma rede e não é necessário criar uma network.

Comando para rodar o arquivo compose em detached mode `docker compose up -d`.

Comando para ver os serviços rodando `docker-compose stats`

Comando para parar os serviços `docker-compose down`

