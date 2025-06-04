# iAvicenne

A real-time communication platform built with WebRTC and WebSocket protocols, enabling peer-to-peer connections and room-based messaging. iAvicenne provides a robust foundation for building real-time collaborative applications with direct peer-to-peer communication capabilities.

## Table of Contents
- [Features](#features)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
  - [System Overview](#system-overview)
  - [Components](#components)
  - [Protocol Documentation](#protocol-documentation)
- [Technical Decisions](#technical-decisions)
- [Development](#development)
  - [Project Structure](#project-structure)
  - [Adding New Features](#adding-new-features)
  - [Testing](#testing)


## Features

- Real-time communication using WebSocket and WebRTC
- Room-based messaging system
- Peer-to-peer direct messaging
- User presence tracking
- Automatic reconnection handling
- TypeScript support for better development experience
- Scalable architecture with Redis backend

## Setup Instructions

### Prerequisites

- Python 3.x
- Node.js 14+ and npm
- Redis server
- Modern web browser with WebRTC support
- Git (for version control)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# On Windows:
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the backend directory:
```ini
DJANGO_SECRET_KEY=django-insecure-development-key-change-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
REDIS_HOST=localhost
CORS_ALLOWED_ORIGINS=http://localhost:3001
```

5. Set up Redis:
```bash
# On macOS with Homebrew:
brew install redis
brew services start redis

# On Ubuntu:
sudo apt-get install redis-server
sudo systemctl start redis-server

# On Windows:
# Download and install from https://redis.io/download
```

6. Run migrations:
```bash
python3 manage.py migrate
```

7. Start the backend server:
```bash
uvicorn core.asgi:application --reload
```

The backend server will be available at `http://localhost:8000`.

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file:
```ini
REACT_APP_MCP_WS_URL=ws://localhost:8000/ws/mcp/
REACT_APP_SIGNALING_WS_URL=ws://localhost:8000/ws/signaling/
```

4. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3001`.

### Troubleshooting

1. **WebSocket Connection Issues**:
   - Ensure both backend and frontend servers are running
   - Check CORS settings in backend `.env`
   - Verify WebSocket URLs in frontend `.env.local`

2. **Redis Connection Issues**:
   - Verify Redis is running: `redis-cli ping`
   - Check Redis connection settings

3. **Python/Node.js Issues**:
   - Ensure correct versions are installed
   - Check virtual environment activation
   - Verify all dependencies are installed

## Architecture

### System Overview

The application implements a hybrid architecture combining traditional client-server communication with modern peer-to-peer connections:

1. **Client-Server Layer**:
   ```
   Frontend <-> WebSocket <-> Backend <-> Redis
   ```
   - WebSocket connections for signaling and room management
   - Redis for real-time message broadcasting
   - Django Channels for WebSocket handling
   - ASGI for asynchronous processing

2. **Peer-to-Peer Layer**:
   ```
   Frontend <-> WebRTC <-> Frontend
   ```
   - Direct communication between peers
   - ICE protocol for NAT traversal
   - Fallback to TURN servers when direct connection fails

### Components

1. **Backend Components**:
   - `core/`: Django project configuration and ASGI setup
   - `mcp/`: Model Context Protocol implementation
     - WebSocket consumers
     - Room management
     - Message broadcasting
   - `signaling/`: WebRTC signaling server
     - Peer discovery
     - SDP exchange
     - ICE candidate handling

2. **Frontend Components**:
   - `src/hooks/`:
     - `useMCP.ts`: MCP protocol hook
     - `useWebRTC.ts`: WebRTC connection hook
   - `src/components/`:
     - `MCPDemo.tsx`: Main demo component
     - UI components for chat and presence

### Protocol Documentation

1. **MCP (Model Context Protocol)**:

   Connection:
   ```json
   {
       "type": "connect",
       "payload": {
           "user_id": "user123"
       }
   }
   ```

   Room Management:
   ```json
   {
       "type": "join-room",
       "payload": {},
       "room": "room123"
   }
   ```

   Messaging:
   ```json
   {
       "type": "message",
       "payload": {
           "content": "Hello, room!"
       },
       "room": "room123"
   }
   ```

2. **WebRTC Signaling**:

   Offer:
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

   Answer:
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

## Technical Decisions

1. **Django Channels & ASGI**:
   - Chosen for robust WebSocket support
   - ASGI enables true asynchronous processing
   - Integrates well with Django's ecosystem
   - Provides built-in channel layers

2. **Redis**:
   - Perfect fit for real-time message broadcasting
   - Efficient presence tracking with pub/sub
   - Built-in support in Django Channels
   - Low latency and high throughput

3. **WebRTC**:
   - Enables direct peer-to-peer communication
   - Reduces server load significantly
   - Lower latency for real-time messaging
   - Built-in security with DTLS

4. **React with TypeScript**:
   - Strong type safety for complex protocols
   - Better developer experience
   - Custom hooks for protocol encapsulation
   - Improved maintainability

5. **Protocol Design**:
   - JSON for human readability
   - Room-based for scalability
   - Separate concerns (MCP vs WebRTC)
   - Extensible message format

## Development

### Project Structure
```
iAvicenne/
├── backend/
│   ├── core/           # Django settings
│   ├── mcp/            # MCP implementation
│   ├── signaling/      # WebRTC signaling
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── App.tsx
│   └── package.json
└── README.md
```

### Adding New Features

1. Backend Extensions:
   - Add new consumer in appropriate app
   - Update protocol documentation
   - Add tests for new functionality

2. Frontend Features:
   - Create new components in `components/`
   - Add custom hooks if needed
   - Update TypeScript interfaces

### Testing

1. Backend Tests:
```bash
cd backend
pytest
```

2. Frontend Tests:
```bash
cd frontend
npm test
```
