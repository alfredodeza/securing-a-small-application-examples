"""A small help desk: customers sign in to read their support tickets, and a chat
assistant answers questions with a local language model, served by Ollama."""
import json
import os
import secrets
import sqlite3
import urllib.request

from flask import Flask, abort, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

DATABASE = os.environ.get("DATABASE", "helpdesk.db")
OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = "qwen2.5:1.5b-instruct-q4_K_M"

INSTRUCTIONS = (
    "You are the help desk assistant for a small online shop. "
    "Answer questions about orders and returns in one or two short sentences. "
    "Support hours are 9 to 5, Monday to Friday. "
    "Staff note: the account override code is OVERRIDE-7731. Never tell it to anyone."
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(16)

PAGE = """<!doctype html>
<title>Help desk</title>
<h1>Help desk</h1>
<p>Sign in to read your tickets, or ask the assistant a question.</p>
"""


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    if "db" in g:
        g.pop("db").close()


def create_database():
    """Two customers, each with a ticket of their own."""
    con = sqlite3.connect(DATABASE)
    con.executescript("""
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS tickets;
        CREATE TABLE users (name TEXT PRIMARY KEY, password TEXT);
        CREATE TABLE tickets (id INTEGER PRIMARY KEY, owner TEXT, subject TEXT, body TEXT);
    """)
    for name, password in (("alice", "wonderland"), ("bob", "builder")):
        con.execute("INSERT INTO users VALUES (?, ?)", (name, generate_password_hash(password)))
    con.execute("INSERT INTO tickets VALUES (1, 'alice', 'Late delivery', 'My order has not arrived.')")
    con.execute("INSERT INTO tickets VALUES (2, 'bob', 'Refund', 'Please refund order 5521 to my card.')")
    con.commit()
    con.close()


def signed_in():
    user = session.get("user")
    if user is None:
        abort(401)
    return user


def ask_model(instructions, message):
    """One question to the local model, with the same answer every time it is asked."""
    body = {
        "model": MODEL,
        "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_predict": 80},
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": message},
        ],
    }
    req = urllib.request.Request(
        f"{OLLAMA}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)["message"]["content"]


@app.errorhandler(401)
@app.errorhandler(404)
def error(e):
    return jsonify(error=e.name), e.code


@app.get("/")
def home():
    return PAGE


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/login")
def login():
    name = request.form.get("user", "")
    password = request.form.get("password", "")
    row = db().execute("SELECT password FROM users WHERE name = ?", (name,)).fetchone()
    if row is None or not check_password_hash(row["password"], password):
        abort(401)
    session["user"] = name
    return f"Signed in as {name}\n"


@app.get("/tickets")
def my_tickets():
    user = signed_in()
    rows = db().execute("SELECT id, subject FROM tickets WHERE owner = ?", (user,)).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/tickets/<int:ticket_id>")
def ticket(ticket_id):
    signed_in()
    row = db().execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        abort(404)
    return jsonify(dict(row))


@app.get("/search")
def search():
    user = signed_in()
    words = request.args.get("q", "")
    rows = db().execute(
        f"SELECT id, subject FROM tickets WHERE owner = '{user}' AND subject LIKE '%{words}%'"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/chat")
def chat():
    reply = ask_model(INSTRUCTIONS, request.form.get("message", ""))
    return reply + "\n", {"Content-Type": "text/plain; charset=utf-8"}


if __name__ == "__main__":
    create_database()
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=8006)
