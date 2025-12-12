"""
Server-authoritative game engine for Pong.
Handles physics, collisions, scoring, and state management.
"""
import math
import random
from typing import Dict, Any, Optional, Literal


class GameEngine:
    """
    Core game logic for Pong.
    Uses 0-100 coordinate system for field dimensions.
    """
    
    # Constants
    FIELD_WIDTH = 100
    FIELD_HEIGHT = 100
    PADDLE_WIDTH = 2
    PADDLE_HEIGHT = 20
    BALL_SIZE = 2
    INITIAL_BALL_SPEED = 0.8
    SPEED_INCREASE_FACTOR = 1.05  # 5% speed increase per hit
    MAX_BALL_SPEED = 3.0
    PADDLE_SPEED = 1.5
    TICK_RATE = 60  # Updates per second
    
    def __init__(self, room_code: str, points_limit: int = 5):
        self.room_code = room_code
        self.points_limit = points_limit
        
        # Game state
        self.status: Literal["waiting_for_opponent", "waiting_for_ready", "playing", "finished"] = "waiting_for_opponent"
        
        # Players
        self.player1_ready = False
        self.player2_ready = False
        self.player1_connected = False
        self.player2_connected = False
        
        # Scores
        self.score_p1 = 0
        self.score_p2 = 0
        self.winner: Optional[str] = None
        
        # Paddle positions (Y coordinate, 0-100 scale)
        self.p1_y = 50.0
        self.p2_y = 50.0
        
        # Paddle movement direction
        self.p1_direction: Literal["up", "down", "stop"] = "stop"
        self.p2_direction: Literal["up", "down", "stop"] = "stop"
        
        # Ball state
        self.ball_x = 50.0
        self.ball_y = 50.0
        self.ball_velocity_x = 0.0
        self.ball_velocity_y = 0.0
        self.ball_speed = self.INITIAL_BALL_SPEED
        
    def player_join(self, player_num: int) -> bool:
        """Register a player joining. Returns True if successful."""
        if player_num == 1:
            self.player1_connected = True
            if self.player2_connected:
                self.status = "waiting_for_ready"
            return True
        elif player_num == 2:
            self.player2_connected = True
            if self.player1_connected:
                self.status = "waiting_for_ready"
            return True
        return False
    
    def player_ready(self, player_num: int):
        """Mark a player as ready."""
        if player_num == 1:
            self.player1_ready = True
        elif player_num == 2:
            self.player2_ready = True
        
        # Start game if both ready
        if self.player1_ready and self.player2_ready and self.status == "waiting_for_ready":
            self.start_game()
    
    def start_game(self):
        """Initialize game state and start playing."""
        self.status = "playing"
        self.reset_ball(serve_to_player=random.choice([1, 2]))
    
    def reset_ball(self, serve_to_player: int = 1):
        """Reset ball to center with initial velocity."""
        self.ball_x = 50.0
        self.ball_y = 50.0
        self.ball_speed = self.INITIAL_BALL_SPEED
        
        # Serve towards the specified player
        direction = 1 if serve_to_player == 2 else -1
        angle = random.uniform(-math.pi/4, math.pi/4)  # Random angle within 45 degrees
        
        self.ball_velocity_x = direction * self.ball_speed * math.cos(angle)
        self.ball_velocity_y = self.ball_speed * math.sin(angle)
    
    def set_paddle_direction(self, player_num: int, direction: Literal["up", "down", "stop"]):
        """Set paddle movement direction."""
        if player_num == 1:
            self.p1_direction = direction
        elif player_num == 2:
            self.p2_direction = direction
    
    def update(self, delta_time: float = 1/60) -> Dict[str, Any]:
        """
        Update game state for one tick.
        Returns dict with events that occurred (collisions, scores, etc.)
        """
        events = {
            "paddle_hit": False,
            "wall_hit": False,
            "score": None,  # None or {"player": 1 or 2}
            "game_over": False
        }
        
        if self.status != "playing":
            return events
        
        # Update paddles
        self._update_paddles(delta_time)
        
        # Update ball
        self._update_ball(delta_time, events)
        
        return events
    
    def _update_paddles(self, delta_time: float):
        """Update paddle positions based on current directions."""
        # Player 1 paddle
        if self.p1_direction == "up":
            self.p1_y -= self.PADDLE_SPEED
        elif self.p1_direction == "down":
            self.p1_y += self.PADDLE_SPEED
        
        # Player 2 paddle
        if self.p2_direction == "up":
            self.p2_y -= self.PADDLE_SPEED
        elif self.p2_direction == "down":
            self.p2_y += self.PADDLE_SPEED
        
        # Constrain paddles to field boundaries
        paddle_half_height = self.PADDLE_HEIGHT / 2
        self.p1_y = max(paddle_half_height, min(self.FIELD_HEIGHT - paddle_half_height, self.p1_y))
        self.p2_y = max(paddle_half_height, min(self.FIELD_HEIGHT - paddle_half_height, self.p2_y))
    
    def _update_ball(self, delta_time: float, events: Dict[str, Any]):
        """Update ball position and handle collisions."""
        # Move ball
        self.ball_x += self.ball_velocity_x
        self.ball_y += self.ball_velocity_y
        
        # Check wall collisions (top and bottom)
        ball_half_size = self.BALL_SIZE / 2
        if self.ball_y - ball_half_size <= 0:
            self.ball_y = ball_half_size
            self.ball_velocity_y = abs(self.ball_velocity_y)
            events["wall_hit"] = True
        elif self.ball_y + ball_half_size >= self.FIELD_HEIGHT:
            self.ball_y = self.FIELD_HEIGHT - ball_half_size
            self.ball_velocity_y = -abs(self.ball_velocity_y)
            events["wall_hit"] = True
        
        # Check paddle collisions
        self._check_paddle_collision(1, events)
        self._check_paddle_collision(2, events)
        
        # Check scoring (ball passed paddles)
        if self.ball_x <= 0:
            # Player 2 scores
            self.score_p2 += 1
            events["score"] = {"player": 2}
            self._handle_score()
        elif self.ball_x >= self.FIELD_WIDTH:
            # Player 1 scores
            self.score_p1 += 1
            events["score"] = {"player": 1}
            self._handle_score()
    
    def _check_paddle_collision(self, player_num: int, events: Dict[str, Any]):
        """Check collision with a specific paddle."""
        if player_num == 1:
            paddle_x = self.PADDLE_WIDTH
            paddle_y = self.p1_y
            ball_moving_towards_paddle = self.ball_velocity_x < 0  # Moving left towards P1
        else:
            paddle_x = self.FIELD_WIDTH - self.PADDLE_WIDTH
            paddle_y = self.p2_y
            ball_moving_towards_paddle = self.ball_velocity_x > 0  # Moving right towards P2
        
        # Only check collision if ball is moving towards this paddle
        if not ball_moving_towards_paddle:
            return
        
        ball_half_size = self.BALL_SIZE / 2
        paddle_half_height = self.PADDLE_HEIGHT / 2
        paddle_half_width = self.PADDLE_WIDTH / 2
        
        # Check if ball overlaps with paddle
        ball_left = self.ball_x - ball_half_size
        ball_right = self.ball_x + ball_half_size
        ball_top = self.ball_y - ball_half_size
        ball_bottom = self.ball_y + ball_half_size
        
        paddle_left = paddle_x - paddle_half_width
        paddle_right = paddle_x + paddle_half_width
        paddle_top = paddle_y - paddle_half_height
        paddle_bottom = paddle_y + paddle_half_height
        
        # AABB collision detection
        if (ball_right >= paddle_left and ball_left <= paddle_right and
            ball_bottom >= paddle_top and ball_top <= paddle_bottom):
            
            # Collision detected!
            events["paddle_hit"] = True
            
            # Bounce ball horizontally
            self.ball_velocity_x = -self.ball_velocity_x
            
            # Add vertical spin based on where ball hit paddle
            hit_pos = (self.ball_y - paddle_y) / paddle_half_height  # -1 to 1
            self.ball_velocity_y += hit_pos * 0.5
            
            # Increase ball speed
            current_speed = math.sqrt(self.ball_velocity_x**2 + self.ball_velocity_y**2)
            new_speed = min(current_speed * self.SPEED_INCREASE_FACTOR, self.MAX_BALL_SPEED)
            
            # Normalize and apply new speed
            if current_speed > 0:
                self.ball_velocity_x = (self.ball_velocity_x / current_speed) * new_speed
                self.ball_velocity_y = (self.ball_velocity_y / current_speed) * new_speed
            
            # Move ball outside paddle to prevent multiple collisions
            if player_num == 1:
                self.ball_x = paddle_right + ball_half_size + 0.1
            else:
                self.ball_x = paddle_left - ball_half_size - 0.1
    
    def _handle_score(self):
        """Handle scoring event."""
        # Check win condition
        if self.score_p1 >= self.points_limit:
            self.winner = "Player 1"
            self.status = "finished"
        elif self.score_p2 >= self.points_limit:
            self.winner = "Player 2"
            self.status = "finished"
        else:
            # Continue game - serve to the player who was scored on
            serve_to = 1 if self.score_p2 > self.score_p1 else 2
            self.reset_ball(serve_to_player=serve_to)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current game state for broadcasting."""
        return {
            "type": "game_update",
            "status": self.status,
            "p1_y": round(self.p1_y, 2),
            "p2_y": round(self.p2_y, 2),
            "ball_x": round(self.ball_x, 2),
            "ball_y": round(self.ball_y, 2),
            "score_p1": self.score_p1,
            "score_p2": self.score_p2,
            "winner": self.winner
        }
    
    def get_game_over_data(self) -> Dict[str, Any]:
        """Get game over data."""
        return {
            "type": "game_over",
            "winner": self.winner,
            "final_score": [self.score_p1, self.score_p2],
            "room_code": self.room_code,
            "points_limit": self.points_limit
        }
