import json
from typing import Dict, Any, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SignalingConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.peer_id = None

    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        logger.info(f"New signaling connection established: {self.channel_name}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.room_group_name:
            await self.leave_room()
        logger.info(f"Signaling connection closed: {self.channel_name}, code: {close_code}")

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

            # Handle different signaling message types
            handlers = {
                'join': self.handle_join,
                'leave': self.handle_leave,
                'offer': self.handle_offer,
                'answer': self.handle_answer,
                'ice-candidate': self.handle_ice_candidate,
            }

            handler = handlers.get(message_type)
            if handler:
                await handler(payload, room)
            else:
                await self.send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error processing signaling message: {str(e)}")
            await self.send_error(f"Internal error: {str(e)}")

    async def handle_join(self, payload: Dict[str, Any], room: str):
        """Handle peer joining a room."""
        if not room:
            await self.send_error("Room ID is required")
            return

        self.peer_id = payload.get('peer_id')
        if not self.peer_id:
            await self.send_error("peer_id is required")
            return

        self.room_name = room
        self.room_group_name = f"webrtc_{room}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.send_json({
            'type': 'joined',
            'room': room,
            'peer_id': self.peer_id,
            'timestamp': datetime.utcnow().isoformat(),
        })

        # Notify others in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'peer_joined',
                'peer_id': self.peer_id,
                'timestamp': datetime.utcnow().isoformat(),
            }
        )

    async def handle_leave(self, payload: Dict[str, Any], room: Optional[str] = None):
        """Handle peer leaving a room."""
        if self.room_group_name:
            await self.leave_room()

    async def handle_offer(self, payload: Dict[str, Any], room: Optional[str] = None):
        """Handle WebRTC offer."""
        if not self.room_group_name:
            await self.send_error("Not connected to any room")
            return

        target_peer_id = payload.get('target_peer_id')
        if not target_peer_id:
            await self.send_error("target_peer_id is required for offer")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'relay_offer',
                'offer': payload.get('offer'),
                'source_peer_id': self.peer_id,
                'target_peer_id': target_peer_id,
                'timestamp': datetime.utcnow().isoformat(),
            }
        )

    async def handle_answer(self, payload: Dict[str, Any], room: Optional[str] = None):
        """Handle WebRTC answer."""
        if not self.room_group_name:
            await self.send_error("Not connected to any room")
            return

        target_peer_id = payload.get('target_peer_id')
        if not target_peer_id:
            await self.send_error("target_peer_id is required for answer")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'relay_answer',
                'answer': payload.get('answer'),
                'source_peer_id': self.peer_id,
                'target_peer_id': target_peer_id,
                'timestamp': datetime.utcnow().isoformat(),
            }
        )

    async def handle_ice_candidate(self, payload: Dict[str, Any], room: Optional[str] = None):
        """Handle ICE candidate."""
        if not self.room_group_name:
            await self.send_error("Not connected to any room")
            return

        target_peer_id = payload.get('target_peer_id')
        if not target_peer_id:
            await self.send_error("target_peer_id is required for ICE candidate")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'relay_ice',
                'candidate': payload.get('candidate'),
                'source_peer_id': self.peer_id,
                'target_peer_id': target_peer_id,
                'timestamp': datetime.utcnow().isoformat(),
            }
        )

    async def leave_room(self):
        """Helper method to leave the current room."""
        if self.room_group_name:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'peer_left',
                    'peer_id': self.peer_id,
                    'timestamp': datetime.utcnow().isoformat(),
                }
            )
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            self.room_group_name = None
            self.room_name = None

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
    async def peer_joined(self, event):
        """Handle peer joined notifications."""
        if event['peer_id'] != self.peer_id:
            await self.send_json({
                'type': 'peer-joined',
                'peer_id': event['peer_id'],
                'timestamp': event['timestamp'],
            })

    async def peer_left(self, event):
        """Handle peer left notifications."""
        if event['peer_id'] != self.peer_id:
            await self.send_json({
                'type': 'peer-left',
                'peer_id': event['peer_id'],
                'timestamp': event['timestamp'],
            })

    async def relay_offer(self, event):
        """Relay WebRTC offer to target peer."""
        if event['target_peer_id'] == self.peer_id:
            await self.send_json({
                'type': 'offer',
                'offer': event['offer'],
                'source_peer_id': event['source_peer_id'],
                'timestamp': event['timestamp'],
            })

    async def relay_answer(self, event):
        """Relay WebRTC answer to target peer."""
        if event['target_peer_id'] == self.peer_id:
            await self.send_json({
                'type': 'answer',
                'answer': event['answer'],
                'source_peer_id': event['source_peer_id'],
                'timestamp': event['timestamp'],
            })

    async def relay_ice(self, event):
        """Relay ICE candidate to target peer."""
        if event['target_peer_id'] == self.peer_id:
            await self.send_json({
                'type': 'ice-candidate',
                'candidate': event['candidate'],
                'source_peer_id': event['source_peer_id'],
                'timestamp': event['timestamp'],
            }) 