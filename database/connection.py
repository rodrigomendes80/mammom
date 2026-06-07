import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        return conn
    except Exception as e:
        raise ConnectionError(f"Erro ao conectar ao banco: {e}")

def execute_query(query: str, params=None, fetch=False):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetch:
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()