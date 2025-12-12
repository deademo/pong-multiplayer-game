"""
Unit tests for the game engine logic.
Tests physics, collisions, scoring, and state management.
"""
import pytest
import math
from pong.game_engine import GameEngine


class TestInitialization:
    """Test game initialization."""
    
    def test_ball_initial_position(self):
        """Verify ball starts exactly at (50, 50)."""
        engine = GameEngine("TEST001", 5)
        # Ball position is set when game starts
        engine.start_game()
        assert engine.ball_x == 50.0
        assert engine.ball_y == 50.0
    
    def test_paddle_initial_positions(self):
        """Verify paddles start at (50, 50) relative height."""
        engine = GameEngine("TEST002", 5)
        assert engine.p1_y == 50.0
        assert engine.p2_y == 50.0
    
    def test_initial_scores(self):
        """Verify scores start at 0."""
        engine = GameEngine("TEST003", 5)
        assert engine.score_p1 == 0
        assert engine.score_p2 == 0


class TestPhysicsAndMovement:
    """Test physics and movement mechanics."""
    
    def test_ball_movement_tick(self):
        """Verify ball moves exactly by velocity in one tick."""
        engine = GameEngine("TEST004", 5)
        engine.start_game()
        
        # Set known velocity
        initial_x = engine.ball_x
        initial_y = engine.ball_y
        engine.ball_velocity_x = 1.0
        engine.ball_velocity_y = 0.5
        
        # Update one tick
        engine.update()
        
        assert engine.ball_x == pytest.approx(initial_x + 1.0, abs=0.01)
        assert engine.ball_y == pytest.approx(initial_y + 0.5, abs=0.01)
    
    def test_paddle_move_up(self):
        """Verify p1_y decreases when moving up."""
        engine = GameEngine("TEST005", 5)
        engine.start_game()  # Start game so paddles can move
        initial_y = engine.p1_y
        
        engine.set_paddle_direction(1, "up")
        engine.update()
        
        assert engine.p1_y < initial_y
    
    def test_paddle_move_down(self):
        """Verify p1_y increases when moving down."""
        engine = GameEngine("TEST006", 5)
        engine.start_game()  # Start game so paddles can move
        initial_y = engine.p1_y
        
        engine.set_paddle_direction(1, "down")
        engine.update()
        
        assert engine.p1_y > initial_y
    
    def test_paddle_stop(self):
        """Verify paddle stays still when stop command is sent."""
        engine = GameEngine("TEST007", 5)
        engine.start_game()  # Start game
        initial_y = engine.p1_y
        
        engine.set_paddle_direction(1, "stop")
        engine.update()
        
        assert engine.p1_y == initial_y
    
    def test_paddle_boundary_top(self):
        """Verify paddle cannot go below 0 (top edge)."""
        engine = GameEngine("TEST008", 5)
        engine.start_game()  # Start game
        engine.p1_y = 15.0  # Near top (just above boundary)
        
        # Try to move up beyond boundary
        engine.set_paddle_direction(1, "up")
        for _ in range(20):
            engine.update()
        
        # Paddle should be clamped at half paddle height (10.0)
        assert engine.p1_y == engine.PADDLE_HEIGHT / 2
        assert engine.p1_y == 10.0
    
    def test_paddle_boundary_bottom(self):
        """Verify paddle cannot go above 100 (bottom edge)."""
        engine = GameEngine("TEST009", 5)
        engine.start_game()  # Start game
        engine.p1_y = 85.0  # Near bottom (just below boundary)
        
        # Try to move down beyond boundary
        engine.set_paddle_direction(1, "down")
        for _ in range(20):
            engine.update()
        
        # Paddle should be clamped at field height minus half paddle height (90.0)
        assert engine.p1_y == engine.FIELD_HEIGHT - engine.PADDLE_HEIGHT / 2
        assert engine.p1_y == 90.0


class TestCollisions:
    """Test collision detection logic."""
    
    def test_collision_wall_top(self):
        """Ball at y=0 should invert vertical velocity."""
        engine = GameEngine("TEST010", 5)
        engine.start_game()
        
        # Position ball at top
        engine.ball_y = 0.5
        engine.ball_velocity_y = -1.0
        engine.ball_velocity_x = 1.0
        
        engine.update()
        
        # Velocity Y should be inverted
        assert engine.ball_velocity_y > 0
    
    def test_collision_wall_bottom(self):
        """Ball at y=100 should invert vertical velocity."""
        engine = GameEngine("TEST011", 5)
        engine.start_game()
        
        # Position ball at bottom
        engine.ball_y = 99.5
        engine.ball_velocity_y = 1.0
        engine.ball_velocity_x = 1.0
        
        engine.update()
        
        # Velocity Y should be inverted
        assert engine.ball_velocity_y < 0
    
    def test_collision_paddle1_front(self):
        """Ball hitting P1 front face should bounce."""
        engine = GameEngine("TEST012", 5)
        engine.start_game()
        
        # Position ball just to the right of P1 paddle, moving left
        engine.ball_x = engine.PADDLE_WIDTH + 2
        engine.ball_y = 50.0
        engine.p1_y = 50.0
        engine.ball_velocity_x = -0.5
        engine.ball_velocity_y = 0.0
        
        initial_speed = abs(engine.ball_velocity_x)
        
        # Update until collision
        for _ in range(10):
            engine.update()
            if engine.ball_velocity_x > 0:  # Bounced
                break
        
        # Ball should have bounced (velocity X inverted)
        assert engine.ball_velocity_x > 0
        
        # Speed should have increased
        current_speed = math.sqrt(engine.ball_velocity_x**2 + engine.ball_velocity_y**2)
        assert current_speed > initial_speed
    
    def test_collision_paddle2_front(self):
        """Ball hitting P2 front face should bounce."""
        engine = GameEngine("TEST013", 5)
        engine.start_game()
        
        # Position ball closer to P2 paddle, moving right
        paddle2_x = engine.FIELD_WIDTH - engine.PADDLE_WIDTH
        engine.ball_x = paddle2_x - 4.0  # Further away
        engine.ball_y = 50.0
        engine.p2_y = 50.0
        engine.ball_velocity_x = 1.5  # Faster to ensure collision
        engine.ball_velocity_y = 0.0
        
        initial_speed = math.sqrt(engine.ball_velocity_x**2 + engine.ball_velocity_y**2)
        
        # Update until collision or max iterations
        bounced = False
        for _ in range(15):
            engine.update()
            if engine.ball_velocity_x < 0:  # Bounced
                bounced = True
                break
        
        # Ball should have bounced (velocity X inverted)
        assert bounced, f"Ball did not bounce. Final velocity_x: {engine.ball_velocity_x}, ball_x: {engine.ball_x}"
        assert engine.ball_velocity_x < 0
        
        # Speed should have increased
        current_speed = math.sqrt(engine.ball_velocity_x**2 + engine.ball_velocity_y**2)
        assert current_speed > initial_speed
    
    def test_speed_increase_on_hit(self):
        """Verify velocity magnitude increases by ~5% after paddle hit."""
        engine = GameEngine("TEST014", 5)
        engine.start_game()
        
        # Position ball near P1 paddle
        engine.ball_x = engine.PADDLE_WIDTH + 1
        engine.ball_y = 50.0
        engine.p1_y = 50.0
        engine.ball_velocity_x = -0.5
        engine.ball_velocity_y = 0.0
        
        initial_speed = math.sqrt(engine.ball_velocity_x**2 + engine.ball_velocity_y**2)
        
        # Update until collision
        for _ in range(10):
            engine.update()
            if engine.ball_velocity_x > 0:  # Bounced
                break
        
        final_speed = math.sqrt(engine.ball_velocity_x**2 + engine.ball_velocity_y**2)
        
        # Speed should increase by approximately 5%
        expected_speed = initial_speed * engine.SPEED_INCREASE_FACTOR
        assert final_speed == pytest.approx(expected_speed, rel=0.01)
    
    def test_no_collision_pass_through(self):
        """Verify ball passes near paddle without colliding if Y-coordinates don't match."""
        engine = GameEngine("TEST015", 5)
        engine.start_game()
        
        # Position ball near P1 paddle but Y is far away
        engine.ball_x = engine.PADDLE_WIDTH + 3
        engine.ball_y = 10.0  # Paddle is at 50, ball is far away
        engine.p1_y = 50.0
        engine.ball_velocity_x = -1.5  # Fast enough to pass quickly
        engine.ball_velocity_y = 0.0
        
        initial_velocity_x = engine.ball_velocity_x
        
        # Update several times
        for _ in range(10):
            engine.update()
            if engine.score_p2 > 0:  # Ball scored
                break
        
        # Ball should have scored (passed through without hitting paddle)
        assert engine.score_p2 == 1
        # And velocity X should have been negative (moving left) until score
        assert initial_velocity_x < 0


class TestScoringAndRules:
    """Test scoring mechanics and win conditions."""
    
    def test_score_p1(self):
        """Ball passing P2's wall (x=100) increments P1 score."""
        engine = GameEngine("TEST016", 5)
        engine.start_game()
        
        # Position ball to score on P2's side (avoid paddle by being off-center vertically)
        engine.ball_x = 95.0
        engine.ball_y = 10.0  # Far from P2 paddle at Y=50
        engine.p2_y = 50.0  # Paddle at center
        engine.ball_velocity_x = 1.5
        engine.ball_velocity_y = 0.0
        
        initial_score = engine.score_p1
        
        # Update until score
        for _ in range(15):
            engine.update()
            if engine.score_p1 > initial_score:
                break
        
        assert engine.score_p1 == initial_score + 1
    
    def test_score_p2(self):
        """Ball passing P1's wall (x=0) increments P2 score."""
        engine = GameEngine("TEST017", 5)
        engine.start_game()
        
        # Position ball to score on P1's side (away from paddle vertically)
        engine.ball_x = 3.0
        engine.ball_y = 10.0  # Far from P1 paddle at Y=50
        engine.p1_y = 50.0  # Make sure paddle is at default position
        engine.ball_velocity_x = -1.5  # Moving left towards P1 wall
        engine.ball_velocity_y = 0.0
        
        initial_score = engine.score_p2
        
        # Update until score
        for _ in range(15):
            engine.update()
            if engine.score_p2 > initial_score:
                break
        
        assert engine.score_p2 == initial_score + 1
    
    def test_ball_reset_after_score(self):
        """Ball should return to center after scoring."""
        engine = GameEngine("TEST018", 5)
        engine.start_game()
        
        # Make P1 score (ball goes past P2 side)
        engine.ball_x = 95.0
        engine.ball_y = 10.0  # Away from P2 paddle
        engine.p2_y = 50.0
        engine.ball_velocity_x = 1.5
        engine.ball_velocity_y = 0.0
        
        for _ in range(15):
            engine.update()
            if engine.score_p1 > 0:
                break
        
        # Ball should be reset to center
        assert engine.ball_x == 50.0
        assert engine.ball_y == 50.0
    
    def test_winning_condition_5(self):
        """Game ends exactly when score reaches 5."""
        engine = GameEngine("TEST019", 5)
        engine.start_game()
        
        # Manually set score to 4 and make one more point
        engine.score_p1 = 4
        engine.ball_x = 95.0
        engine.ball_y = 10.0  # Away from P2 paddle
        engine.p2_y = 50.0
        engine.ball_velocity_x = 1.5
        engine.ball_velocity_y = 0.0
        
        for _ in range(15):
            engine.update()
            if engine.status == "finished":
                break
        
        assert engine.score_p1 == 5
        assert engine.status == "finished"
        assert engine.winner == "Player 1"
    
    def test_winning_condition_20(self):
        """Game ends exactly when score reaches 20."""
        engine = GameEngine("TEST020", 20)
        engine.start_game()
        
        # Manually set score to 19 and make one more point
        engine.score_p2 = 19
        engine.ball_x = 3.0
        engine.ball_y = 10.0  # Away from paddle
        engine.p1_y = 50.0
        engine.ball_velocity_x = -1.5
        engine.ball_velocity_y = 0.0
        
        for _ in range(15):
            engine.update()
            if engine.status == "finished":
                break
        
        assert engine.score_p2 == 20
        assert engine.status == "finished"
        assert engine.winner == "Player 2"
    
    def test_winning_condition_custom(self):
        """Game ends at arbitrary limit if set."""
        engine = GameEngine("TEST021", 50)
        engine.start_game()
        
        engine.score_p1 = 49
        engine.ball_x = 95.0
        engine.ball_y = 10.0  # Away from P2 paddle
        engine.p2_y = 50.0
        engine.ball_velocity_x = 1.5
        engine.ball_velocity_y = 0.0
        
        for _ in range(15):
            engine.update()
            if engine.status == "finished":
                break
        
        assert engine.score_p1 == 50
        assert engine.status == "finished"
    
    def test_game_over_state_freeze(self):
        """No further updates/movement allowed after game over."""
        engine = GameEngine("TEST022", 5)
        engine.start_game()
        
        # Set game to finished
        engine.score_p1 = 5
        engine.status = "finished"
        engine.winner = "Player 1"
        
        # Try to update
        ball_x_before = engine.ball_x
        events = engine.update()
        
        # Ball should not move
        assert engine.ball_x == ball_x_before


class TestGameStateManagement:
    """Test game state and player management."""
    
    def test_player_join_logic_p1(self):
        """0 players -> Add as P1."""
        engine = GameEngine("TEST023", 5)
        result = engine.player_join(1)
        
        assert result == True
        assert engine.player1_connected == True
        assert engine.status == "waiting_for_opponent"
    
    def test_player_join_logic_p2(self):
        """1 player -> Add as P2."""
        engine = GameEngine("TEST024", 5)
        engine.player_join(1)
        result = engine.player_join(2)
        
        assert result == True
        assert engine.player2_connected == True
        assert engine.status == "waiting_for_ready"
    
    def test_ready_state_single_player(self):
        """Game does not start if only 1 player is ready."""
        engine = GameEngine("TEST025", 5)
        engine.player_join(1)
        engine.player_join(2)
        
        engine.player_ready(1)
        
        assert engine.status == "waiting_for_ready"
    
    def test_ready_state_both_players(self):
        """Game starts when both players are ready."""
        engine = GameEngine("TEST026", 5)
        engine.player_join(1)
        engine.player_join(2)
        
        engine.player_ready(1)
        engine.player_ready(2)
        
        assert engine.status == "playing"
    
    def test_double_ready(self):
        """Sending ready twice shouldn't break state."""
        engine = GameEngine("TEST027", 5)
        engine.player_join(1)
        engine.player_join(2)
        
        engine.player_ready(1)
        engine.player_ready(1)  # Send again
        engine.player_ready(2)
        
        assert engine.status == "playing"
    
    def test_state_serialization(self):
        """Verify get_state() returns correct JSON structure for broadcast."""
        engine = GameEngine("TEST028", 5)
        engine.start_game()
        
        state = engine.get_state()
        
        assert state["type"] == "game_update"
        assert "p1_y" in state
        assert "p2_y" in state
        assert "ball_x" in state
        assert "ball_y" in state
        assert "score_p1" in state
        assert "score_p2" in state
        assert "status" in state


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_ball_max_speed_cap(self):
        """Ball speed should not exceed MAX_BALL_SPEED."""
        engine = GameEngine("TEST029", 5)
        engine.start_game()
        
        # Simulate many paddle hits to increase speed
        for _ in range(50):
            # Position ball for collision
            engine.ball_x = engine.PADDLE_WIDTH + 1
            engine.ball_y = 50.0
            engine.p1_y = 50.0
            engine.ball_velocity_x = -0.5
            engine.ball_velocity_y = 0.0
            
            engine.update()
        
        # Check speed doesn't exceed max
        speed = math.sqrt(engine.ball_velocity_x**2 + engine.ball_velocity_y**2)
        assert speed <= engine.MAX_BALL_SPEED
    
    def test_paddle_edge_collision(self):
        """Ball hitting top/bottom edge of paddle should be handled."""
        engine = GameEngine("TEST030", 5)
        engine.start_game()
        
        # Position ball at edge of paddle
        engine.ball_x = engine.PADDLE_WIDTH + 1
        engine.ball_y = 50.0 + engine.PADDLE_HEIGHT / 2 - 1  # Near edge
        engine.p1_y = 50.0
        engine.ball_velocity_x = -0.5
        engine.ball_velocity_y = 0.0
        
        # Should handle without crash
        try:
            for _ in range(10):
                engine.update()
            success = True
        except Exception:
            success = False
        
        assert success
    
    def test_simultaneous_wall_and_paddle_collision(self):
        """Handle case where ball could hit wall and paddle in same frame."""
        engine = GameEngine("TEST031", 5)
        engine.start_game()
        
        # Position ball at corner
        engine.ball_x = engine.PADDLE_WIDTH + 1
        engine.ball_y = 1.0  # Near top wall
        engine.p1_y = 5.0  # Paddle near top
        engine.ball_velocity_x = -0.5
        engine.ball_velocity_y = -0.5
        
        # Should handle without crash
        try:
            for _ in range(10):
                engine.update()
            success = True
        except Exception:
            success = False
        
        assert success
