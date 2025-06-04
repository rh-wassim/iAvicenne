# MCP Server Backend

This is the backend component of the MCP (Model Context Protocol) server with WebRTC signaling support.

## Setup Instructions

1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a `.env` file in the backend directory with the following content:
```
DJANGO_SECRET_KEY=django-insecure-development-key-change-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
REDIS_HOST=localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

3. Install and start Redis:
```bash
# On macOS with Homebrew:
brew install redis
brew services start redis

# On Ubuntu:
sudo apt-get install redis-server
sudo systemctl start redis-server
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
uvicorn core.asgi:application --reload
```

The server will be available at `http://localhost:8000`.

## WebSocket Endpoints

1. MCP Protocol: `ws://localhost:8000/ws/mcp/`
2. WebRTC Signaling: `ws://localhost:8000/ws/signaling/`

## Protocol Documentation

### MCP Protocol Messages

1. Connection:
```json
{
    "type": "connect",
    "payload": {
        "user_id": "user123"
    }
}
```

2. Join Room:
```json
{
    "type": "join-room",
    "payload": {},
    "room": "room123"
}
```

3. Leave Room:
```json
{
    "type": "leave-room",
    "payload": {},
    "room": "room123"
}
```

4. Send Message:
```json
{
    "type": "message",
    "payload": {
        "content": "Hello, room!"
    },
    "room": "room123"
}
```

### WebRTC Signaling Messages

1. Join:
```json
{
    "type": "join",
    "payload": {
        "peer_id": "peer123"
    },
    "room": "room123"
}
```

2. Offer:
```json
{
    "type": "offer",
    "payload": {
        "target_peer_id": "peer456",
        "offer": {
            "type": "offer",
            "sdp": "..."
        }
    },
    "room": "room123"
}
```

3. Answer:
```json
{
    "type": "answer",
    "payload": {
        "target_peer_id": "peer123",
        "answer": {
            "type": "answer",
            "sdp": "..."
        }
    },
    "room": "room123"
}
```

4. ICE Candidate:
```json
{
    "type": "ice-candidate",
    "payload": {
        "target_peer_id": "peer123",
        "candidate": {
            "candidate": "...",
            "sdpMLineIndex": 0,
            "sdpMid": "0"
        }
    },
    "room": "room123"
}
```

## Development Guidelines

1. All code must be asynchronous and use ASGI from end to end
2. Follow proper error handling practices
3. Use type hints and docstrings
4. Keep the code modular and maintainable 