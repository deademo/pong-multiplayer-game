## Phase 6: Testing Strategy (EXTREME)
Since AI implementations can be prone to logic bugs and simpler LLMs make mistakes, we require a **95%+ Code Coverage** test suite. This goes beyond happy paths into every possible edge case.

### 10.1 Unit Tests (`tests/unit/`)
These tests check individual components in isolation.

#### A. Game Engine Logic (`test_engine.py`)
**1. Physics & Movement**
- `test_ball_initial_position`: Verify ball starts exactly at (50, 50).
- `test_paddle_initial_positions`: Verify paddles start at (50, 50) relative height.
- `test_ball_movement_tick`: Verify ball moves exactly (velocity_x, velocity_y) in one tick.
- `test_ball_velocity_normalization`: Ensure velocity doesn't exceed maximum caps (if implemented) or drop to zero.
- `test_paddle_move_up`: Verify `p1_y` decreases when moving up.
- `test_paddle_move_down`: Verify `p1_y` increases when moving down.
- `test_paddle_stop`: Verify paddle stays still when "stop" command is sent.
- `test_paddle_boundary_top`: Verify paddle cannot go below 0 (top edge).
- `test_paddle_boundary_bottom`: Verify paddle cannot go above 100 (bottom edge).

**2. Collisions (The Hard Stuff)**
- `test_collision_wall_top`: Ball at y=0 should invert vertical velocity.
- `test_collision_wall_bottom`: Ball at y=100 should invert vertical velocity.
- `test_collision_paddle1_front`: Ball hitting P1 front face should bounce.
- `test_collision_paddle1_back`: Ball hitting P1 from behind (if possible by glitch) should be handled or ignored.
- `test_collision_paddle2_front`: Ball hitting P2 front face should bounce.
- `test_collision_paddle_edge_cases`:
    - Ball hitting exact corner of paddle.
    - Ball hitting top/bottom edge of paddle (should it bounce or pass?).
- `test_speed_increase_on_hit`: Verify velocity magnitude increases by exactly 5% after paddle hit.
- `test_no_collision_pass_through`: Verify ball passes *near* paddle without colliding if Y-coordinates don't match.

**3. Scoring & Rules**
- `test_score_p1`: Ball passing P2's wall (x=100) increments P1 score.
- `test_score_p2`: Ball passing P1's wall (x=0) increments P2 score.
- `test_ball_reset_after_score`: Ball should return to center after scoring.
- `test_ball_direction_after_reset`: Ball should serve towards the loser (or random).
- `test_winning_condition_5`: Game ends exactly when score reaches 5.
- `test_winning_condition_20`: Game ends exactly when score reaches 20.
- `test_winning_condition_custom`: Game ends at arbitrary limit if set.
- `test_game_over_state_freeze`: No further updates/movement allowed after game over.

**4. Game State Management**
- `test_player_join_logic`:
    - 0 players -> Add as P1.
    - 1 player -> Add as P2.
    - 2 players -> Reject or Add as Observer.
- `test_ready_state`: Game does not start if only 1 player is ready.
- `test_double_ready`: Sending "ready" twice shouldn't break state.
- `test_disconnect_during_game`: Game state handles player dropout (pause? abort? auto-win?).
- `test_state_serialization`: Verify `to_dict()` returns correct JSON structure for broadcast.

#### B. Consumer/Socket Logic (`test_consumers.py`)
- `test_connect_valid_room`: Connection succeeds for valid room code.
- `test_connect_invalid_room`: Handling of weird characters in room code.
- `test_receive_json_valid`: Server parses valid JSON correctly.
- `test_receive_json_invalid_syntax`: Server handles malformed JSON without crashing.
- `test_receive_json_missing_fields`: Handle missing "type" or "data" fields gracefully.
- `test_receive_unknown_message_type`: Ignore or log unknown message types.
- `test_broadcast_efficiency`: (Mock) Ensure update is sent to group, not just sender.

#### C. Models (`test_models.py`)
- `test_match_creation`: Save a match.
- `test_match_retrieval`: Read a match.
- `test_score_integrity`: Ensure scores cannot be negative (if constrained).
- `test_timestamp_auto_add`: `created_at` is automatically set.

### 10.2 Integration Tests (`tests/integration/`)
These run against a live Daphne server.

**1. The "Happy Path" (Full Simulation)**
- Connect P1, Connect P2.
- Both send Ready.
- Simulate 100 ticks of game loop.
- Verify ball has moved.
- Verify score updates if we manually force ball position near edge.
- Verify Game Over message is received by both.

**2. The "Bad Actor" Scenarios**
- **Spamming:** Send 100 "move_paddle" requests in 1 second. Server should handle load.
- **Illegal Moves:** Send "move_paddle" with invalid direction ("diagonal", "teleport"). Should be ignored.
- **Role Spoofing:** Observer tries to send "move_paddle". Should be ignored.
- **Premature Start:** Send "move_paddle" before game starts. Should be ignored.

**3. Concurrent Rooms**
- Create Room A and Room B.
- P1 and P2 in Room A. P3 and P4 in Room B.
- Verify Room A events do NOT leak into Room B.
- Verify scores track separately.

**4. Latency/Disconnects (Simulated)**
- P1 disconnects mid-game. P2 should receive "Opponent Disconnected" or Win.
- Reconnect: (If feature supported) P1 rejoins and resumes. (If not) P1 blocked or new game.

**5. Observer Scaling**
- Connect 2 Players.
- Connect 50 Observers.
- Verify all 50 receive updates. (Performance check).
