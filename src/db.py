from decouple import config

from sqlalchemy import create_engine


def connect_db():
    #_load_db_vars()
    # create db create_engine

    DB_USER = config("POSTGRES_USER")
    DB_PASS = config("POSTGRES_PASSWORD")
    DB_IP = config("POSTGRES_HOST")
    DB_PORT = config("POSTGRES_PORT")
    DB_NAME = config("POSTGRES_DB")

    db = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_IP}:{DB_PORT}/{DB_NAME}')
    return db