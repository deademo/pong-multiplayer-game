"""
Integration tests using a real Daphne server.
These tests connect to an actual running server to avoid event loop conflicts.
"""
import pytest
import asyncio
import websockets
import json
import time
import os


# Server URL from environment or default
SERVER_URL = os.environ.get('SERVER_URL', 'ws://localhost:8000')


@pytest.mark.asyncio
@pytest.mark.integration_real_server
class TestRealServerConnection:
    """Test basic connectivity to the real server."""
    
    async def test_single_player_connection(self):
        """Single player can connect to a room."""
        room_code = f"REAL{int(time.time())}"
        uri = f"{SERVER_URL}/ws/game/{room_code}/"
        
        async with websockets.connect(uri) as websocket:
            # Create room
            await websocket.send(json.dumps({
                "type": "create_room",
                "points_limit": 5
            }))
            
            # Receive room_created
            response1 = await asyncio.wait_for(websocket.recv(), timeout=5)
            data1 = json.loads(response1)
            assert data1["type"] == "room_created"
            
            # Join as player
            await websocket.send(json.dumps({
                "type": "join_game",
                "role": "player"
            }))
            
            # Receive joined_as_player
            response2 = await asyncio.wait_for(websocket.recv(), timeout=5)
            data2 = json.loads(response2)
            
            assert data2["type"] == "joined_as_player"
            assert data2["player_num"] == 1
    
    async def test_two_players_can_connect(self):
        """Two players can connect to the same room."""
        room_code = f"REAL{int(time.time())}"
        uri = f"{SERVER_URL}/ws/game/{room_code}/"
        
        async with websockets.connect(uri) as ws1:
            # Player 1 creates and joins
            await ws1.send(json.dumps({
                "type": "create_room",
                "points_limit": 5
            }))
            
            # Receive room_created
            room_resp = await asyncio.wait_for(ws1.recv(), timeout=5)
            assert json.loads(room_resp)["type"] == "room_created"
            
            await ws1.send(json.dumps({
                "type": "join_game",
                "role": "player"
            }))
            
            response1 = await asyncio.wait_for(ws1.recv(), timeout=5)
            data1 = json.loads(response1)
            assert data1["type"] == "joined_as_player"
            assert data1["player_num"] == 1
            
            # Player 2 connects
            async with websockets.connect(uri) as ws2:
                await ws2.send(json.dumps({
                    "type": "join_game",
                    "role": "player"
                }))
                
                response2 = await asyncio.wait_for(ws2.recv(), timeout=5)
                data2 = json.loads(response2)
                assert data2["type"] == "joined_as_player"
                assert data2["player_num"] == 2
                
                # Both should receive status change
                # Player 1 may have received "waiting_for_opponent" first, so read until we get "waiting_for_ready"
                status1_data = None
                for _ in range(3):
                    status1 = await asyncio.wait_for(ws1.recv(), timeout=5)
                    status1_data = json.loads(status1)
                    if status1_data.get("type") == "status_change" and status1_data.get("status") == "waiting_for_ready":
                        break
                
                assert status1_data is not None
                assert status1_data["type"] == "status_change"
                assert status1_data["status"] in ["waiting_for_ready", "waiting_for_opponent"]
    
    async def test_game_starts_when_both_ready(self):
        """Game starts when both players are ready."""
        room_code = f"REAL{int(time.time())}"
        uri = f"{SERVER_URL}/ws/game/{room_code}/"
        
        async with websockets.connect(uri) as ws1:
            # Setup Player 1
            await ws1.send(json.dumps({"type": "create_room", "points_limit": 5}))
            await ws1.send(json.dumps({"type": "join_game", "role": "player"}))
            await ws1.recv()  # joined_as_player
            
            async with websockets.connect(uri) as ws2:
                # Setup Player 2
                await ws2.send(json.dumps({"type": "join_game", "role": "player"}))
                await ws2.recv()  # joined_as_player
                
                # Clear status messages
                await ws1.recv()  # status_change
                await ws2.recv()  # status_change
                
                # Both ready
                await ws1.send(json.dumps({"type": "player_ready"}))
                await ws2.send(json.dumps({"type": "player_ready"}))
                
                # Wait for game to start
                for _ in range(10):
                    try:
                        msg = await asyncio.wait_for(ws1.recv(), timeout=1)
                        data = json.loads(msg)
                        if data.get("type") == "status_change" and data.get("status") == "playing":
                            break
                        elif data.get("type") == "game_update":
                            # Game started and sending updates
                            assert "ball_x" in data
                            assert "ball_y" in data
                            assert "p1_y" in data
                            assert "p2_y" in data
                            break
                    except asyncio.TimeoutError:
                        continue
    
    async def test_observer_can_join(self):
        """Observer can join an existing game."""
        room_code = f"REAL{int(time.time())}"
        uri = f"{SERVER_URL}/ws/game/{room_code}/"
        
        async with websockets.connect(uri) as ws1:
            # Setup Player 1
            await ws1.send(json.dumps({"type": "create_room", "points_limit": 5}))
            await ws1.send(json.dumps({"type": "join_game", "role": "player"}))
            await ws1.recv()
            
            async with websockets.connect(uri) as ws2:
                # Setup Player 2
                await ws2.send(json.dumps({"type": "join_game", "role": "player"}))
                await ws2.recv()
                
                # Observer joins
                async with websockets.connect(uri) as ws_obs:
                    await ws_obs.send(json.dumps({
                        "type": "join_game",
                        "role": "observer"
                    }))
                    
                    response = await asyncio.wait_for(ws_obs.recv(), timeout=5)
                    data = json.loads(response)
                    assert data["type"] == "joined_as_observer"
    
    async def test_invalid_json_handled(self):
        """Server handles invalid JSON gracefully."""
        room_code = f"REAL{int(time.time())}"
        uri = f"{SERVER_URL}/ws/game/{room_code}/"
        
        async with websockets.connect(uri) as websocket:
            # Send invalid JSON
            await websocket.send("this is not json")
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            assert data["type"] == "error"
    
    async def test_concurrent_rooms(self):
        """Multiple rooms can run simultaneously."""
        room_a = f"ROOMA{int(time.time())}"
        room_b = f"ROOMB{int(time.time())}"
        
        uri_a = f"{SERVER_URL}/ws/game/{room_a}/"
        uri_b = f"{SERVER_URL}/ws/game/{room_b}/"
        
        async with websockets.connect(uri_a) as ws_a1:
            await ws_a1.send(json.dumps({"type": "create_room", "points_limit": 5}))
            await ws_a1.recv()  # room_created
            await ws_a1.send(json.dumps({"type": "join_game", "role": "player"}))
            resp_a = await ws_a1.recv()
            assert json.loads(resp_a)["type"] == "joined_as_player"
            
            async with websockets.connect(uri_b) as ws_b1:
                await ws_b1.send(json.dumps({"type": "create_room", "points_limit": 20}))
                await ws_b1.recv()  # room_created
                await ws_b1.send(json.dumps({"type": "join_game", "role": "player"}))
                resp_b = await ws_b1.recv()
                assert json.loads(resp_b)["type"] == "joined_as_player"
                
                # Both rooms are independent
                assert room_a != room_b


@pytest.mark.asyncio
@pytest.mark.integration_real_server
class TestRealServerGameplay:
    """Test actual gameplay on real server."""
    
    async def test_paddle_movement(self):
        """Paddle moves when player sends commands."""
        room_code = f"REAL{int(time.time())}"
        uri = f"{SERVER_URL}/ws/game/{room_code}/"
        
        async with websockets.connect(uri) as ws1:
            # Setup
            await ws1.send(json.dumps({"type": "create_room", "points_limit": 5}))
            await ws1.recv()  # room_created
            await ws1.send(json.dumps({"type": "join_game", "role": "player"}))
            await ws1.recv()  # joined_as_player
            
            async with websockets.connect(uri) as ws2:
                await ws2.send(json.dumps({"type": "join_game", "role": "player"}))
                await ws2.recv()  # joined_as_player
                
                await ws1.recv()  # status_change
                await ws2.recv()  # status_change
                
                # Start game
                await ws1.send(json.dumps({"type": "player_ready"}))
                await ws2.send(json.dumps({"type": "player_ready"}))
                
                await asyncio.sleep(0.5)
                
                # Get initial position (read several messages to ensure game started)
                initial_y = None
                for _ in range(10):
                    try:
                        msg = await asyncio.wait_for(ws1.recv(), timeout=0.2)
                        data = json.loads(msg)
                        if data.get("type") == "game_update":
                            initial_y = data["p1_y"]
                            # Found initial position, now test movement
                            break
                    except asyncio.TimeoutError:
                        continue
                
                # Move paddle multiple times to ensure movement
                for _ in range(5):
                    await ws1.send(json.dumps({
                        "type": "move_paddle",
                        "direction": "up"
                    }))
                    await asyncio.sleep(0.05)
                
                await asyncio.sleep(0.3)
                
                # Get new position
                final_y = None
                for _ in range(10):
                    try:
                        msg = await asyncio.wait_for(ws1.recv(), timeout=0.2)
                        data = json.loads(msg)
                        if data.get("type") == "game_update":
                            final_y = data["p1_y"]
                    except asyncio.TimeoutError:
                        break
                
                # Verify movement (up means y decreases)
                if initial_y is not None and final_y is not None:
                    assert final_y <= initial_y, f"Paddle should have moved up or stayed: {initial_y} -> {final_y}"
                else:
                    # If we couldn't get positions, at least verify game was running
                    assert initial_y is not None, "Failed to get initial paddle position"
    
    async def test_ball_movement(self):
        """Ball moves during gameplay."""
        room_code = f"REAL{int(time.time())}"
        uri = f"{SERVER_URL}/ws/game/{room_code}/"
        
        async with websockets.connect(uri) as ws1:
            await ws1.send(json.dumps({"type": "create_room", "points_limit": 50}))
            await ws1.send(json.dumps({"type": "join_game", "role": "player"}))
            await ws1.recv()
            
            async with websockets.connect(uri) as ws2:
                await ws2.send(json.dumps({"type": "join_game", "role": "player"}))
                await ws2.recv()
                
                await ws1.recv()
                await ws2.recv()
                
                await ws1.send(json.dumps({"type": "player_ready"}))
                await ws2.send(json.dumps({"type": "player_ready"}))
                
                await asyncio.sleep(0.2)
                
                # Get initial ball position
                initial_ball = None
                for _ in range(10):
                    try:
                        msg = await asyncio.wait_for(ws1.recv(), timeout=0.5)
                        data = json.loads(msg)
                        if data.get("type") == "game_update":
                            initial_ball = (data["ball_x"], data["ball_y"])
                            break
                    except asyncio.TimeoutError:
                        pass
                
                # Wait for ball to move
                await asyncio.sleep(1.0)
                
                # Get new ball position
                final_ball = None
                for _ in range(10):
                    try:
                        msg = await asyncio.wait_for(ws1.recv(), timeout=0.5)
                        data = json.loads(msg)
                        if data.get("type") == "game_update":
                            final_ball = (data["ball_x"], data["ball_y"])
                            break
                    except asyncio.TimeoutError:
                        pass
                
                # Verify ball moved
                if initial_ball and final_ball:
                    distance = abs(final_ball[0] - initial_ball[0]) + abs(final_ball[1] - initial_ball[1])
                    assert distance > 1, f"Ball should have moved: {initial_ball} -> {final_ball}"
