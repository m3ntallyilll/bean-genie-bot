from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
import threading
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bean_genie_bot import process_command, MODEL
from dotenv import load_dotenv
import sys

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

DATABASE = 'chat_memory.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            sender TEXT NOT NULL,
            message_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            credit INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            entry_fee TEXT,
            participants TEXT,
            duration TEXT,
            prize TEXT,
            scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'username' in session:
        return render_template('chat.html', username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password"
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            error = "Username already exists"
            conn.close()
            return render_template('register.html', error=error)
        password_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        conn.close()
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

def save_message(username, sender, message_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO messages (username, sender, message_text, timestamp) VALUES (?, ?, ?, ?)',
        (username, sender, message_text, datetime.utcnow())
    )
    conn.commit()
    conn.close()

def get_recent_messages(username, limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT sender, message_text FROM messages WHERE username = ? ORDER BY timestamp DESC LIMIT ?',
        (username, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows[::-1]

@app.route('/api/message', methods=['POST'])
def message():
    if 'username' not in session:
        return jsonify({'reply': 'Please log in to chat.'})
    username = session['username']
    user_message = request.json.get('message', '')
    selected_model = request.json.get('model', MODEL)

    save_message(username, 'user', user_message)

    history_rows = get_recent_messages(username)
    conversation_history = []
    for row in history_rows:
        conversation_history.append({'sender': row['sender'], 'message': row['message_text']})

    context_text = ''
    for msg in conversation_history:
        prefix = 'User: ' if msg['sender'] == 'user' else 'Bot: '
        context_text += prefix + msg['message'] + '\n'
    context_text += 'User: ' + user_message + '\n'

    response = process_command(user_message, conversation_history=context_text, model=selected_model)

    save_message(username, 'bot', response)

    try:
        response_data = json.loads(response)
        if 'response' in response_data:
            bot_reply = response_data['response']
        elif 'error' in response_data:
            bot_reply = f"Error: {response_data['error']}"
        else:
            bot_reply = response
    except Exception:
        bot_reply = response
    return jsonify({'reply': bot_reply})

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/restart', methods=['POST'])
def restart():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    def restart_server():
        shutdown_server()
        os._exit(0)
    threading.Thread(target=restart_server).start()
    return jsonify({'message': 'Server is restarting...'})

from flask import current_app

@app.route('/api/scrape_events', methods=['POST'])
def scrape_events():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    from bean_genie_bot import get_events
    import datetime

    events_json = get_events()
    try:
        events_data = json.loads(events_json)
    except Exception as e:
        return jsonify({'error': f'Failed to parse events data: {str(e)}'}), 500

    if 'error' in events_data:
        return jsonify({'error': events_data['error']}), 500

    events_list = events_data.get('events', [])
    if not events_list:
        return jsonify({'message': 'No events found'}), 200

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM events')

    for event in events_list:
        cursor.execute('''
            INSERT INTO events (name, type, entry_fee, participants, duration, prize, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.get('name'),
            event.get('type'),
            event.get('entry_fee'),
            event.get('participants'),
            event.get('duration'),
            event.get('prize'),
            datetime.datetime.utcnow()
        ))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Successfully scraped and saved {len(events_list)} events.'})

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/api/agentic_command', methods=['POST'])
def agentic_command():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_command = request.json.get('command', '')
    if not user_command:
        return jsonify({'error': 'No command provided'}), 400

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    payload = {
        "model": "compound-beta",
        "messages": [
            {
                "role": "user",
                "content": user_command
            }
        ]
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return jsonify({'reply': content})
    except Exception as e:
        return jsonify({'error': f'Failed to get response from Groq API: {str(e)}'}), 500

if __name__ == '__main__':
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    app.run(host='0.0.0.0', port=port)
