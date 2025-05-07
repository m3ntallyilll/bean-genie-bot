import pytest
import json
from web_ui import app, init_db, get_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def test_database_schema():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    assert 'users' in tables
    assert 'messages' in tables

def test_register_login_logout(client):
    # Register new user
    response = client.post('/register', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    assert b'Bean-Genie Chat' in response.data or response.status_code == 200

    # Attempt to register same user again
    response = client.post('/register', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    assert b'Username already exists' in response.data

    # Login with correct credentials
    response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    assert b'Bean-Genie Chat' in response.data

    # Login with incorrect credentials
    response = client.post('/login', data={'username': 'testuser', 'password': 'wrongpass'}, follow_redirects=True)
    assert b'Invalid username or password' in response.data

    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert b'Bean-Genie Login' in response.data

def test_chat_message(client):
    # Register and login user
    client.post('/register', data={'username': 'chatuser', 'password': 'chatpass'}, follow_redirects=True)
    client.post('/login', data={'username': 'chatuser', 'password': 'chatpass'}, follow_redirects=True)

    # Send chat message
    response = client.post('/api/message', json={'message': 'Hello'}, follow_redirects=True)
    data = json.loads(response.data)
    assert 'reply' in data
    assert isinstance(data['reply'], str)

def test_restart_unauthorized(client):
    response = client.post('/restart')
    assert response.status_code == 401

def test_restart_authorized(client):
    # Register and login user
    client.post('/register', data={'username': 'restartuser', 'password': 'restartpass'}, follow_redirects=True)
    client.post('/login', data={'username': 'restartuser', 'password': 'restartpass'}, follow_redirects=True)

    response = client.post('/restart')
    data = json.loads(response.data)
    assert 'message' in data
    assert 'restarting' in data['message'].lower()

def test_frontend_pages(client):
    response = client.get('/login')
    assert response.status_code == 200
    response = client.get('/register')
    assert response.status_code == 200
    # Login first to access chat page
    client.post('/register', data={'username': 'frontuser', 'password': 'frontpass'}, follow_redirects=True)
    client.post('/login', data={'username': 'frontuser', 'password': 'frontpass'}, follow_redirects=True)
    response = client.get('/')
    assert response.status_code == 200

def test_bot_command_processing():
    from bean_genie_bot import process_command
    response = process_command("!track 15000 85")
    # Accept either JSON response with tier or conversational response containing 'progress'
    try:
        import json
        data = json.loads(response)
        assert "response" in data
        assert "tier" in data["response"].lower()
    except Exception:
        assert "progress" in response.lower()
