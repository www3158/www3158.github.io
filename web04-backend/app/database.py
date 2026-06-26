import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url, row_factory=dict_row)

    connect_options = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "row_factory": dict_row,
    }
    sslmode = os.getenv("DB_SSLMODE")
    if sslmode:
        connect_options["sslmode"] = sslmode
    return psycopg.connect(**connect_options)
