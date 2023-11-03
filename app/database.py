import psycopg2
from psycopg2 import sql
import config.config as config

def connect_to_database(connection):
   # Establish a database connection
    try:
        cursor = connection.cursor()
        return cursor
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def close_database_connection(cursor,connection):
    cursor.close()
    connection.close()

def get_cursor_connection():
    connection = psycopg2.connect(
    dbname= config.DATABASE_NAME,
    user= config.DATABASE_USER,
    password= config.DATABASE_PASSWORD,
    host= config.DATABASE_HOST,
    port= config.DATABASE_PORT
    )
    cursor = connection.cursor()
    return cursor,connection