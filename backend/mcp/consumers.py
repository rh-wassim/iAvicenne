import json
from typing import Dict, Any, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MCPConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.user_id = None

    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        logger.info(f"New WebSocket connection established: {self.channel_name}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.room_group_name:
            await self.leave_room()
        logger.info(f"WebSocket connection closed: {self.channel_name}, code: {close_code}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            payload = data.get('payload', {})
            room = data.get('room')

            if not message_type:
                await self.send_error("Message type is required")
                return

            # Handle different message types
            handlers = {
                'connect': self.handle_connect,
                'disconnect': self.handle_disconnect,
                'join-room': self.handle_join_room,
                'leave-room': self.handle_leave_room,
                'message': self.handle_message,
            }

            handler = handlers.get(message_type)
            if handler:
                await handler(payload, room)
            else:
                await self.send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_error(f"Internal error: {str(e)}")

    async def handle_connect(self, payload: Dict[str, Any], room: Optional[str] = None):
        """Handle initial connection setup."""
        self.user_id = payload.get('user_id')
        if not self.user_id:
            await self.send_error("user_id is required for connection")
            return

        await self.send_json({
            'type': 'connect',
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
        })

    async def handle_disconnect(self, payload: Dict[str, Any], room: Optional[str] = None):
        """Handle graceful disconnection."""
        if self.room_group_name:
            await self.leave_room()
        await self.close()

    async def handle_join_room(self, payload: Dict[str, Any], room: str):
        """Handle room joining."""
        if not room:
            await self.send_error("Room ID is required")
            return

        if self.room_group_name:
            await self.leave_room()

        self.room_group_name = f"room_{room}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.send_json({
            'type': 'room-joined',
            'room': room,
            'timestamp': datetime.utcnow().isoformat(),
        })

        # Notify other users in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user_id,
                'timestamp': datetime.utcnow().isoformat(),
            }
        )

    async def handle_leave_room(self, payload: Dict[str, Any], room: Optional[str] = None):
        """Handle room leaving."""
        if self.room_group_name:
            await self.leave_room()
            await self.send_json({
                'type': 'room-left',
                'timestamp': datetime.utcnow().isoformat(),
            })

    async def handle_message(self, payload: Dict[str, Any], room: Optional[str] = None):
        """Handle generic messages within a room."""
        if not self.room_group_name:
            await self.send_error("Not connected to any room")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message',
                'message': payload,
                'user_id': self.user_id,
                'timestamp': datetime.utcnow().isoformat(),
            }
        )

    async def leave_room(self):
        """Helper method to leave the current room."""
        if self.room_group_name:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user_id,
                    'timestamp': datetime.utcnow().isoformat(),
                }
            )
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            self.room_group_name = None

    async def send_error(self, message: str):
        """Helper method to send error messages."""
        await self.send_json({
            'type': 'error',
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
        })

    async def send_json(self, content: Dict[str, Any]):
        """Helper method to send JSON messages."""
        await self.send(text_data=json.dumps(content))

    # Channel layer message handlers
    async def broadcast_message(self, event):
        """Handle broadcast messages."""
        await self.send_json({
            'type': 'message',
            'user_id': event['user_id'],
            'message': event['message'],
            'timestamp': event['timestamp'],
        })

    async def user_joined(self, event):
        """Handle user joined notifications."""
        await self.send_json({
            'type': 'user-joined',
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
        })

    async def user_left(self, event):
        """Handle user left notifications."""
        await self.send_json({
            'type': 'user-left',
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
        }) 