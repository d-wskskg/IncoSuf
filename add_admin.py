import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

conn = sqlite3.connect("admin.db")
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS admin (
	id	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	username	TEXT NOT NULL UNIQUE,
	password	TEXT NOT NULL);""")

def password_setter(password):
    password_hash = generate_password_hash(password, "sha256")
    return password_hash

def insert_data(username, password_hash):
    cur.execute("INSERT INTO admin (username, password) VALUES (?, ?)", (username, password_hash))
    conn.commit()
    conn.close()

username = input("Username: ")
password = input("Password: ")
password_hash = password_setter(password)
insert_data(username, password_hash)