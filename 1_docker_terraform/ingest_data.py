import os
import argparse
from time import time

import pandas as pd
from sqlalchemy import create_engine

import requests



def main(params):

    user = params.user
    password = params.password
    host = params.host
    port = params.port
    database = params.db
    table_name = params.table_name
    url = params.url

    csv_name = 'output.csv'

    response = requests.get(url)
    with open(csv_name, 'wb') as f:
        f.write(response.content)

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')


    df_iter = (pd.read_csv(csv_name, compression='gzip', iterator = True, chunksize = 100000))

    df = next(df_iter)

    df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)


    df.head(0).to_sql(name= table_name, con = engine, if_exists="replace")

    df.to_sql(name= table_name, con = engine, if_exists="append")

    while True:
        t_start = time()
    
        df = next(df_iter)

        df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
        df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

        df.to_sql(name= table_name, con = engine, if_exists="append")

        t_end = time()

        print('inserted_another_chunk, took %.3f' % (t_end - t_start))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest CSV data into Postgres container')

    parser.add_argument('--user', help='user name for postgres such as root')
    parser.add_argument('--password', help = 'password for postgres')
    parser.add_argument('--host', help = 'host for postgres')
    parser.add_argument('--port', help = 'port for postgres')
    parser.add_argument('--db', help = 'database name for postgres')
    parser.add_argument('--table_name', help = 'name of the table where will write data to')
    parser.add_argument('--url', help = 'url of the .csv file to be downloaded')

    args = parser.parse_args()

    main(args)
