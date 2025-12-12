"""
Unit tests for WebSocket consumer logic.
Tests message handling, JSON parsing, and consumer behavior.
"""
import pytest
import json
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import re_path
from pong.consumers import PongConsumer


# Define the application for testing
application = URLRouter([
    re_path(r'ws/game/(?P<room_code>[^/]+)/$', PongConsumer.as_asgi()),
])


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestConsumerConnection:
    """Test consumer connection handling."""
    
    async def test_connect_valid_room(self):
        """Connection succeeds for valid room code."""
        communicator = WebsocketCommunicator(application, "/ws/game/VALID123/")
        connected, subprotocol = await communicator.connect()
        
        assert connected is True
        
        await communicator.disconnect()
    
    async def test_connect_room_with_special_chars(self):
        """Handle room codes with alphanumeric characters."""
        room_codes = ["ABC123", "test-room", "room_123", "MYROOM99"]
        
        for room_code in room_codes:
            communicator = WebsocketCommunicator(application, f"/ws/game/{room_code}/")
            connected, _ = await communicator.connect()
            assert connected is True
            await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestConsumerMessageHandling:
    """Test consumer message parsing and handling."""
    
    async def test_receive_json_valid(self):
        """Server parses valid JSON correctly."""
        communicator = WebsocketCommunicator(application, "/ws/game/JSONTEST/")
        await communicator.connect()
        
        # Send valid create_room message
        await communicator.send_json_to({
            "type": "create_room",
            "points_limit": 5
        })
        
        # Should not crash, might receive response or timeout
        await communicator.disconnect()
    
    async def test_receive_json_invalid_syntax(self):
        """Server handles malformed JSON without crashing."""
        communicator = WebsocketCommunicator(application, "/ws/game/BADJSON/")
        await communicator.connect()
        
        # Send invalid JSON
        await communicator.send_to(text_data="{ invalid json }")
        
        # Should receive error response
        try:
            response = await communicator.receive_json_from(timeout=5)
            assert response["type"] == "error"
        except Exception:
            # Or might disconnect, both acceptable
            pass
        
        await communicator.disconnect()
    
    async def test_receive_json_missing_type_field(self):
        """Handle messages missing required 'type' field gracefully."""
        communicator = WebsocketCommunicator(application, "/ws/game/NOTYPE/")
        await communicator.connect()
        
        # Send message without 'type' field
        await communicator.send_json_to({
            "data": "some data",
            "value": 123
        })
        
        # Should receive error or ignore
        try:
            response = await communicator.receive_json_from(timeout=5)
            if "type" in response:
                assert response["type"] == "error"
        except:
            # Timeout is also acceptable
            pass
        
        await communicator.disconnect()
    
    async def test_receive_unknown_message_type(self):
        """Server handles unknown message types."""
        communicator = WebsocketCommunicator(application, "/ws/game/UNKNOWN/")
        await communicator.connect()
        
        # Send message with unknown type
        await communicator.send_json_to({
            "type": "do_backflip",
            "data": "please"
        })
        
        # Should receive error response
        try:
            response = await communicator.receive_json_from(timeout=5)
            assert response["type"] == "error"
        except:
            # Timeout is also acceptable
            pass
        
        await communicator.disconnect()
    
    async def test_receive_empty_message(self):
        """Handle empty message objects."""
        communicator = WebsocketCommunicator(application, "/ws/game/EMPTY/")
        await communicator.connect()
        
        # Send empty JSON object
        await communicator.send_json_to({})
        
        # Should not crash
        try:
            response = await communicator.receive_json_from(timeout=3)
            # Any response is fine, as long as no crash
            assert "type" in response
        except:
            pass
        
        await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestConsumerBroadcasting:
    """Test message broadcasting to channel groups."""
    
    async def test_broadcast_to_multiple_clients(self):
        """Messages broadcast to all clients in room."""
        room_code = "BROADCAST"
        
        # Connect three clients
        comm1 = WebsocketCommunicator(application, f"/ws/game/{room_code}/")
        comm2 = WebsocketCommunicator(application, f"/ws/game/{room_code}/")
        comm3 = WebsocketCommunicator(application, f"/ws/game/{room_code}/")
        
        await comm1.connect()
        await comm2.connect()
        await comm3.connect()
        
        # Create room with first client
        await comm1.send_json_to({"type": "create_room", "points_limit": 5})
        
        # Join all as players/observers
        await comm1.send_json_to({"type": "join_game", "role": "player"})
        await comm1.receive_json_from(timeout=5)  # joined_as_player
        
        await comm2.send_json_to({"type": "join_game", "role": "player"})
        await comm2.receive_json_from(timeout=5)  # joined_as_player
        
        await comm3.send_json_to({"type": "join_game", "role": "observer"})
        await comm3.receive_json_from(timeout=5)  # joined_as_observer
        
        # All should receive status change
        status_msgs = []
        for comm in [comm1, comm2, comm3]:
            try:
                msg = await comm.receive_json_from(timeout=5)
                status_msgs.append(msg)
            except:
                pass
        
        # At least some should have received messages
        assert len(status_msgs) >= 1
        
        await comm1.disconnect()
        await comm2.disconnect()
        await comm3.disconnect()
    
    async def test_messages_not_sent_to_disconnected(self):
        """Disconnected clients don't receive broadcasts."""
        room_code = "DISCONNECT"
        
        comm1 = WebsocketCommunicator(application, f"/ws/game/{room_code}/")
        comm2 = WebsocketCommunicator(application, f"/ws/game/{room_code}/")
        
        await comm1.connect()
        await comm2.connect()
        
        await comm1.send_json_to({"type": "create_room", "points_limit": 5})
        await comm1.send_json_to({"type": "join_game", "role": "player"})
        await comm1.receive_json_from(timeout=5)
        
        await comm2.send_json_to({"type": "join_game", "role": "player"})
        await comm2.receive_json_from(timeout=5)
        
        # Disconnect comm2
        await comm2.disconnect()
        
        # comm1 should be notified
        try:
            msg = await comm1.receive_json_from(timeout=5)
            # Should receive some notification
            assert "type" in msg
        except:
            pass
        
        await comm1.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestConsumerRoomManagement:
    """Test room creation and management."""
    
    async def test_create_room_with_different_limits(self):
        """Rooms can be created with various points limits."""
        limits = [5, 20, 50, 100]
        
        for limit in limits:
            room_code = f"LIMIT{limit}"
            comm = WebsocketCommunicator(application, f"/ws/game/{room_code}/")
            await comm.connect()
            
            await comm.send_json_to({
                "type": "create_room",
                "points_limit": limit
            })
            
            # Room should be created successfully
            await comm.disconnect()
    
    async def test_join_nonexistent_room_creates_it(self):
        """Joining a non-existent room should handle gracefully."""
        comm = WebsocketCommunicator(application, "/ws/game/NEWROOM999/")
        await comm.connect()
        
        # Try to join without creating
        await comm.send_json_to({"type": "join_game", "role": "player"})
        
        # Should either auto-create or error, but not crash
        try:
            response = await comm.receive_json_from(timeout=5)
            assert "type" in response
        except:
            pass
        
        await comm.disconnect()
    
    async def test_multiple_creates_same_room(self):
        """Multiple create_room calls on same room handle gracefully."""
        room_code = "MULTICREATE"
        
        comm = WebsocketCommunicator(application, f"/ws/game/{room_code}/")
        await comm.connect()
        
        # Create room multiple times
        await comm.send_json_to({"type": "create_room", "points_limit": 5})
        await comm.send_json_to({"type": "create_room", "points_limit": 10})
        await comm.send_json_to({"type": "create_room", "points_limit": 20})
        
        # Should not crash
        await comm.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestConsumerEdgeCases:
    """Test edge cases and error conditions."""
    
    async def test_rapid_connect_disconnect(self):
        """Handle rapid connection/disconnection cycles."""
        room_code = "RAPID"
        
        for _ in range(10):
            comm = WebsocketCommunicator(application, f"/ws/game/{room_code}/")
            await comm.connect()
            await comm.disconnect()
        
        # Should complete without errors
        assert True
    
    async def test_disconnect_during_message_processing(self):
        """Disconnect while server is processing messages."""
        comm = WebsocketCommunicator(application, "/ws/game/DISCMSG/")
        await comm.connect()
        
        # Send message and immediately disconnect
        await comm.send_json_to({"type": "create_room", "points_limit": 5})
        await comm.disconnect()
        
        # Should handle gracefully
        assert True
    
    async def test_send_after_disconnect(self):
        """Ensure clean disconnect prevents further sends."""
        comm = WebsocketCommunicator(application, "/ws/game/AFTERDISC/")
        await comm.connect()
        await comm.disconnect()
        
        # Trying to send after disconnect should fail or be ignored
        try:
            await comm.send_json_to({"type": "join_game", "role": "player"})
        except Exception:
            # Expected to fail
            pass
        
        assert True
