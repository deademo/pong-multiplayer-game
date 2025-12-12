#!/usr/bin/env python3
"""Manual test script to simulate Player 2 joining a room"""
import asyncio
import websockets
import json
import sys

async def join_as_player2(room_code):
    """Join a room as Player 2"""
    uri = f"ws://localhost:8000/ws/game/{room_code}/"
    
    print(f"Connecting to {uri}")
    
    async with websockets.connect(uri) as websocket:
        print("Connected! Sending join_game message...")
        
        # Join as player
        await websocket.send(json.dumps({
            "type": "join_game",
            "role": "player"
        }))
        
        # Listen for responses
        print("\nWaiting for messages from server...")
        try:
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"\nReceived: {json.dumps(data, indent=2)}")
                
                # If we joined successfully, send ready
                if data.get("type") == "joined_as_player":
                    print("\n✅ Joined as Player 2!")
                    print("Sending player_ready message...")
                    await websocket.send(json.dumps({
                        "type": "player_ready"
                    }))
                
                # If status changed to playing, we're good!
                if data.get("type") == "status_change" and data.get("status") == "playing":
                    print("\n🎮 GAME STARTED!")
                    break
                    
        except asyncio.TimeoutError:
            print("\nTimeout waiting for messages")
        except KeyboardInterrupt:
            print("\nDisconnecting...")

if __name__ == "__main__":
    room_code = sys.argv[1] if len(sys.argv) > 1 else "1TXQBU"
    print(f"Joining room: {room_code}")
    asyncio.run(join_as_player2(room_code))
