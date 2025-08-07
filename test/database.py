import sqlite3
import uuid
from werkzeug.utils import secure_filename
import os
import time

DB_PATH='users.db'

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            id TEXT PRIMARY KEY,
            User TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    user_id = str(uuid.uuid4())
    try:
        cursor.execute('INSERT INTO User (id, User, password) VALUES (?, ?, ?)', (user_id, username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM User WHERE User = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def image_post(username,img):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT avatars FROM User WHERE User = ? AND avatars = ?',(username,None))
    bool_fetchall= cursor.fetchall()
    if bool_fetchall:
        img = secure_filename(img)
        img_path = os.path.join('/static/',img)
        img_url = f'/static/{img}'
        cursor.execute('UPDATE Users SET avatars WHERE User = ?', (img_url, 'newuser'))
    print(bool_fetchall)

def image_get(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT avatars FROM User WHERE User = ?',(username,))
    row = cursor.fetchall()
    cursor.execute('SELECT Sign FROM User WHERE User = ?', (username,))
    low = cursor.fetchall()
    return row,low
def init_db1():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_message(sender, receiver, message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)', (sender, receiver, message))
    conn.commit()
    conn.close()

def get_chat_between_users(user1, user2):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT sender, message FROM messages
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
        ORDER BY timestamp ASC
    ''', (user1, user2, user2, user1))
    rows = c.fetchall()
    conn.close()
    return [f"{sender}: {msg}" for sender, msg in rows]

def add_img_friend(friend):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    placeholders = ','.join('?' for _ in friend)
    query = f"SELECT User, avatars FROM User WHERE User IN ({placeholders})"
    c.execute(query, friend)
    results = c.fetchall()
    conn.close()
    return {username:avatar for username,avatar in results}