"""
WebSocket consumer for real-time Pong game.
Handles player connections, game loop, and state broadcasting.
"""
import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .game_engine import GameEngine
from .models import MatchHistory


# Global dictionary to store active game rooms
# Format: {room_code: {"engine": GameEngine, "task": asyncio.Task, "players": {}, "observers": []}}
ACTIVE_ROOMS = {}


class PongConsumer(AsyncWebsocketConsumer):
    """Handle WebSocket connections for Pong game."""
    
    async def connect(self):
        """Handle new WebSocket connection."""
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'pong_{self.room_code}'
        self.role = None  # Will be set to "player" or "observer"
        self.player_num = None  # Will be set to 1 or 2 for players
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Initialize room if it doesn't exist
        if self.room_code not in ACTIVE_ROOMS:
            ACTIVE_ROOMS[self.room_code] = {
                "engine": None,  # Will be created when we know points_limit
                "task": None,
                "players": {},  # {1: channel_name, 2: channel_name}
                "observers": []
            }
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Clean up player/observer from room
        if self.room_code in ACTIVE_ROOMS:
            room = ACTIVE_ROOMS[self.room_code]
            
            if self.role == "player" and self.player_num:
                # Remove player
                if self.player_num in room["players"]:
                    del room["players"][self.player_num]
                
                # Cancel game loop if a player disconnects
                if room["task"] and not room["task"].done():
                    room["task"].cancel()
                
                # Notify others
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "player_disconnected",
                        "player_num": self.player_num
                    }
                )
            
            elif self.role == "observer":
                if self.channel_name in room["observers"]:
                    room["observers"].remove(self.channel_name)
            
            # Clean up empty rooms (check again in case another disconnect already removed it)
            if self.room_code in ACTIVE_ROOMS and not room["players"] and not room["observers"]:
                if room["task"] and not room["task"].done():
                    room["task"].cancel()
                del ACTIVE_ROOMS[self.room_code]
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'create_room':
                await self.handle_create_room(data)
            elif message_type == 'join_game':
                await self.handle_join_game(data)
            elif message_type == 'player_ready':
                await self.handle_player_ready()
            elif message_type == 'move_paddle':
                await self.handle_move_paddle(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_create_room(self, data):
        """Handle room creation with points limit."""
        points_limit = data.get('points_limit', 5)
        
        if self.room_code in ACTIVE_ROOMS:
            room = ACTIVE_ROOMS[self.room_code]
            if room["engine"] is None:
                # Initialize engine with points limit
                room["engine"] = GameEngine(self.room_code, points_limit)
                
                await self.send(text_data=json.dumps({
                    'type': 'room_created',
                    'room_code': self.room_code,
                    'points_limit': points_limit
                }))
    
    async def handle_join_game(self, data):
        """Handle player or observer joining."""
        role = data.get('role', 'player')
        
        if self.room_code not in ACTIVE_ROOMS:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Room does not exist'
            }))
            return
        
        room = ACTIVE_ROOMS[self.room_code]
        
        # If engine doesn't exist yet, create with default points
        if room["engine"] is None:
            room["engine"] = GameEngine(self.room_code, 5)
        
        engine = room["engine"]
        
        if role == 'player':
            # Assign player number
            if 1 not in room["players"]:
                self.player_num = 1
                room["players"][1] = self.channel_name
                engine.player_join(1)
            elif 2 not in room["players"]:
                self.player_num = 2
                room["players"][2] = self.channel_name
                engine.player_join(2)
            else:
                # Room full, make them an observer
                role = 'observer'
        
        if role == 'observer':
            self.role = 'observer'
            room["observers"].append(self.channel_name)
            await self.send(text_data=json.dumps({
                'type': 'joined_as_observer',
                'room_code': self.room_code
            }))
        else:
            self.role = 'player'
            await self.send(text_data=json.dumps({
                'type': 'joined_as_player',
                'player_num': self.player_num,
                'room_code': self.room_code
            }))
        
        # Broadcast status change
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'status_change',
                'status': engine.status
            }
        )
    
    async def handle_player_ready(self):
        """Handle player ready signal."""
        if self.role != 'player' or not self.player_num:
            return
        
        if self.room_code not in ACTIVE_ROOMS:
            return
        
        room = ACTIVE_ROOMS[self.room_code]
        engine = room["engine"]
        
        engine.player_ready(self.player_num)
        
        # Broadcast status change
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'status_change',
                'status': engine.status
            }
        )
        
        # Start game loop if game is now playing
        if engine.status == "playing" and (room["task"] is None or room["task"].done()):
            room["task"] = asyncio.create_task(self.game_loop())
    
    async def handle_move_paddle(self, data):
        """Handle paddle movement command."""
        if self.role != 'player' or not self.player_num:
            return
        
        if self.room_code not in ACTIVE_ROOMS:
            return
        
        room = ACTIVE_ROOMS[self.room_code]
        engine = room["engine"]
        
        if engine.status != "playing":
            return
        
        direction = data.get('direction', 'stop')
        if direction not in ['up', 'down', 'stop']:
            return
        
        engine.set_paddle_direction(self.player_num, direction)
    
    async def game_loop(self):
        """Main game loop running at 60 FPS."""
        if self.room_code not in ACTIVE_ROOMS:
            return
        
        room = ACTIVE_ROOMS[self.room_code]
        engine = room["engine"]
        
        tick_rate = 1 / 60  # 60 FPS
        
        try:
            while engine.status == "playing":
                # Update game state
                events = engine.update(tick_rate)
                
                # Broadcast game state
                state = engine.get_state()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    state
                )
                
                # Check for game over
                if engine.status == "finished":
                    # Save match history
                    await self.save_match_history(engine)
                    
                    # Broadcast game over
                    game_over_data = engine.get_game_over_data()
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        game_over_data
                    )
                    break
                
                # Wait for next tick
                await asyncio.sleep(tick_rate)
        
        except asyncio.CancelledError:
            # Game loop cancelled (player disconnected)
            pass
    
    @database_sync_to_async
    def save_match_history(self, engine: GameEngine):
        """Save completed match to database."""
        MatchHistory.objects.create(
            room_code=engine.room_code,
            player1_score=engine.score_p1,
            player2_score=engine.score_p2,
            winner=engine.winner,
            points_limit=engine.points_limit
        )
    
    # Channel layer message handlers
    async def game_update(self, event):
        """Send game state update to WebSocket."""
        await self.send(text_data=json.dumps(event))
    
    async def status_change(self, event):
        """Send status change to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'status_change',
            'status': event['status']
        }))
    
    async def game_over(self, event):
        """Send game over message to WebSocket."""
        await self.send(text_data=json.dumps(event))
    
    async def player_disconnected(self, event):
        """Send player disconnected message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'player_disconnected',
            'player_num': event['player_num']
        }))
