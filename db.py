import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, date, time

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DB_URL)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMPTZ DEFAULT now()
                );
            ''')
            conn.commit()

def save_message(user_id, role, content):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO messages (user_id, role, content) VALUES (%s, %s, %s)
            ''', (user_id, role, content))
            conn.commit()

def get_last_messages(user_id, limit=10):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT role, content FROM messages
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            ''', (user_id, limit * 2))  # user + assistant
            rows = cur.fetchall()
            return list(reversed([{"role": r[0], "content": r[1]} for r in rows]))

def clear_history(user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM messages WHERE user_id = %s', (user_id,))
            conn.commit()


def add_question_to_db(dpt: str, question: str, chunk: str):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS questions (
                        id SERIAL PRIMARY KEY,
                        department TEXT,
                        question TEXT,
                        chunk TEXT,
                        date DATE,
                        time TIME,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )""")
                cur.execute("""
                    INSERT INTO questions (department, question, chunk, date, time)
                    VALUES (%s, %s, %s, %s, %s)
                    """, (dpt, question, chunk, date.today(), datetime.now().time()))
                conn.commit()
    except Exception as e:
        print("ошибка при записи:", e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()