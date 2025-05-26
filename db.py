# import sqlite3
# from datetime import datetime

# DB_FILE = "chat_history.db"

# def init_db():
#     with sqlite3.connect(DB_FILE) as conn:
#         cursor = conn.cursor()
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS messages (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 user_id INTEGER,
#                 role TEXT,
#                 content TEXT,
#                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
#         conn.commit()

# def save_message(user_id, role, content):
#     with sqlite3.connect(DB_FILE) as conn:
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO messages (user_id, role, content)
#             VALUES (?, ?, ?)
#         ''', (user_id, role, content))
#         conn.commit()
#         print(f'  {user_id} {role} {content} saved')

# def get_last_messages(user_id, limit=10):
#     with sqlite3.connect(DB_FILE) as conn:
#         cursor = conn.cursor()
#         cursor.execute('''
#             SELECT role, content FROM messages
#             WHERE user_id = ?
#             ORDER BY timestamp DESC
#             LIMIT ?
#         ''', (user_id, limit * 2))  # *2 потому что и user, и assistant
#         rows = cursor.fetchall()
#         # Обратный порядок для GPT
#         return list(reversed([{"role": r[0], "content": r[1]} for r in rows]))

import psycopg2
import os
from dotenv import load_dotenv

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
