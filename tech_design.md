# Technical Design Document: Retro Ping Pong Multiplayer

## 1. Project Overview
A multiplayer Ping Pong game with a retro black-and-white aesthetic.
- **Stack:** Vanilla JavaScript (Frontend), Python Django 6.0 + Django Channels (Backend), PostgreSQL 18.1 (Database), Redis 8.2 (Channel Layer).
- **Communication:** WebSockets for real-time state sync.
- **Deployment:** Docker + Docker Compose.

## 2. Architecture
- **Frontend:** Single Page Application (SPA) serving HTML/CSS/JS. Connects to Backend via WebSocket.
- **Backend:** Django application hosting HTTP endpoints (for serving the app) and WebSocket consumers (for game logic).
- **Database:** PostgreSQL to store finalized match history.
- **Channel Layer:** Redis to enable communication between WebSocket instances.

## 3. Database Schema (PostgreSQL)
We need one main model for storing match results.

### Table: `MatchHistory`
| Column | Type | Description |
|---|---|---|
| `id` | UUID/Auto Inc | Primary Key |
| `room_code` | String | Unique code for the room |
| `player1_score` | Integer | Final score for Player 1 |
| `player2_score` | Integer | Final score for Player 2 |
| `winner` | String | "Player 1" or "Player 2" |
| `created_at` | DateTime | Timestamp of match completion |
| `points_limit` | Integer | Configuration used (5, 20, 50, 100) |

*Note: Since auth is anonymous, we do not store user IDs.*

## 4. WebSocket Protocol
Communication happens via JSON messages.

### Connection URL
`ws://<host>/ws/game/<room_code>/`

### Client -> Server Messages
1.  **Join Room:**
    ```json
    { "type": "join_game", "role": "player" } // or "observer"
    ```
2.  **Player Ready:**
    ```json
    { "type": "player_ready" }
    ```
3.  **Paddle Movement:**
    ```json
    { "type": "move_paddle", "direction": "up" } // or "down", or "stop"
    ```
    *Simpler LLM Note: You might send raw key states (pressed/released) or position updates if trusting client, but "direction" is safer for server-authoritative logic.*

### Server -> Client Messages
1.  **Room State Update (Broadcast Loop - 60fps or similar):**
    ```json
    {
      "type": "game_update",
      "p1_y": 50, // Player 1 paddle Y percentage (0-100)
      "p2_y": 50, // Player 2 paddle Y percentage
      "ball_x": 50, // Ball X percentage
      "ball_y": 50, // Ball Y percentage
      "score_p1": 0,
      "score_p2": 0
    }
    ```
2.  **Game Status Change:**
    ```json
    { "type": "status_change", "status": "waiting_for_opponent" }
    // Statuses: "waiting_for_opponent", "waiting_for_ready", "playing", "finished"
    ```
3.  **Game Over:**
    ```json
    { "type": "game_over", "winner": "Player 1", "final_score": [5, 3] }
    ```
4.  **Error / Notification:**
    ```json
    { "type": "error", "message": "Room full" }
    ```

## 5. Implementation Plan (Step-by-Step for AI)

### Phase 1: Environment & Docker Setup
1.  **Create Directory Structure:**
    - `/backend`: Django project.
    - `/frontend`: Static HTML/JS files.
    - `docker-compose.yml`.
2.  **Setup `docker-compose.yml`:**
    - Service `db`: Postgres (image: `postgres:18-alpine`). Environment variables for DB name, user, password. **Crucial:** Add volume mounting for persistence.
    - Service `redis`: Redis (image: `redis:8-alpine`).
    - Service `backend`: Python container. Should depend on `db` and `redis`. Mount `/backend` volume.
3.  **Backend Dockerfile:**
    - Base image: `python:3.12-slim` (or 3.13 if available).
    - Install dependencies: `django`, `channels`, `channels_redis`, `psycopg2-binary`, `daphne`.
    - Command: Run `daphne` for ASGI support.

### Phase 2: Backend Core (Django)
1.  **Initialize Project:**
    - Run `django-admin startproject config .` inside backend container.
    - Run `python manage.py startapp pong`.
2.  **Configure `settings.py`:**
    - Add `daphne`, `channels`, `pong` to `INSTALLED_APPS`.
    - Set `ASGI_APPLICATION = 'config.asgi.application'`.
    - Configure `CHANNEL_LAYERS` to point to the `redis` service.
    - Configure `DATABASES` to point to the `db` service.
3.  **Create Model:**
    - Define `MatchHistory` in `pong/models.py`.
    - Run migrations (`makemigrations`, `migrate`).

### Phase 3: Backend Game Logic (Consumers)
1.  **Create Consumer:**
    - Create `pong/consumers.py`.
    - Create `PongConsumer` inheriting from `AsyncWebsocketConsumer`.
2.  **Handle Connection:**
    - Parse `room_code` from URL route.
    - Check room occupancy in memory (or Redis).
    - If room has < 2 players, allow connection as "player".
    - If room has 2 players, allow connection as "observer".
    - Reject if logic requires (e.g., specific observer link format), though requirements say "observer link" just joins as observer. *Design Decision: Use query param `?role=observer` or separate URL path.*
3.  **Game Loop & State:**
    - **Crucial:** Game state (ball position, paddle positions, scores) must be managed on the server to sync players and observers.
    - Store state in a Python dictionary or Class instance associated with the `room_code`.
    - Use `asyncio.create_task` to run a game loop (60 ticks/sec) when both players are "Ready".
4.  **Physics Logic (Server-Side):**
    - **Update Ball:** `ball_x += velocity_x`, `ball_y += velocity_y`.
    - **Collision:**
        - Top/Bottom walls: Invert `velocity_y`.
        - Paddles: If ball overlaps paddle coordinates, invert `velocity_x` and increase speed slightly.
        - Left/Right walls: Score update. Reset ball to center.
    - **Paddle Movement:** Update paddle Y position based on "up"/"down" messages received from clients. Constrain to 0-100%.
5.  **Broadcasting:**
    - On every tick, send `game_update` to the channel group for that room.

### Phase 4: Frontend (Vanilla JS)
1.  **Project Structure:**
    - `index.html`: The single page.
    - `style.css`: Retro styles (black background, white text, monospace font).
    - `game.js`: Main logic.
2.  **UI Implementation (SPA):**
    - Create `div` containers for: `MainMenu`, `Lobby`, `GameArena`, `PostGame`.
    - By default, show `MainMenu`, hide others.
    - **Main Menu:**
        - Dropdown: Points (5, 20, 50, 100).
        - Button: "Create Room".
        - Input: "Room Code".
        - Button: "Join".
    - **Lobby:**
        - Text: "Room Code: XXXXX".
        - Text: "Share this link for players...".
        - Text: "Share this link for observers...".
        - Button: "Ready" (Disabled until opponent joins? Or toggleable).
    - **Game Arena:**
        - `<canvas>` element (4:3 aspect ratio).
        - Scoreboard display (Player 1 : Player 2).
    - **Post Game:**
        - Winner text.
        - "Return to Main Menu" button.
3.  **WebSocket Integration (`game.js`):**
    - `ws = new WebSocket(...)`
    - `ws.onmessage`: Parse JSON and update local variables.
4.  **Rendering Loop:**
    - `requestAnimationFrame(render)`.
    - `render()` function clears canvas and draws rects for paddles and ball based on *latest received server state*.
    - **Interpolation (Optional for simpler implementation):** Just draw raw coordinates.
5.  **Input Handling:**
    - `document.addEventListener('keydown', ...)`
    - Send `move_paddle` messages to server.
6.  **Audio (Oscillators):**
    - Create `AudioContext`.
    - Function `playSound(type)`:
        - `collision`: Short square wave beep.
        - `score`: Longer, lower pitch beep.
    - Trigger sounds based on game state updates (e.g., if ball velocity changes direction).

## 6. Detailed Physics Specs
- **Field:** 0 to 100 coordinate system for simplicity.
- **Paddle Size:** Height 20, Width 2.
- **Ball Size:** 2x2.
- **Start Speed:** X=0.5, Y=0.5 (Adjust based on tick rate).
- **Speed Increase:** 5% increase on paddle hit.

## 7. Configuration Details
- **Points Limit:**
  - Sent to server upon Room Creation.
  - Server stores this in the room's state.
  - Checks score against limit after every point.

## 8. Observers
- Observers join the same WebSocket channel group.
- They receive all `game_update` messages.
- They send NO input messages.
- UI hides "Ready" buttons and controls for them.

## 9. Docker Compose Example Snippet
```yaml
version: '3.8'
services:
  db:
    image: postgres:18-alpine
    environment:
      POSTGRES_DB: pong
      POSTGRES_USER: pong
      POSTGRES_PASSWORD: pongpassword
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
  redis:
    image: redis:8-alpine
  backend:
    build: ./backend
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
```

## 10. Phase 6: Testing Strategy (CRITICAL)
Since AI implementations can be prone to logic bugs, we require a comprehensive test suite using `pytest` and `django-channels` testing tools.

### 10.1 Unit Tests (`tests/unit/`)
These tests check individual components in isolation.
*   **Game Engine Logic (`test_engine.py`):**
    *   **Physics:** Test `update_ball_position()` ensures the ball moves correctly based on velocity.
    *   **Collision (Walls):** Test ball bouncing off top/bottom walls (velocity Y inversion).
    *   **Collision (Paddles):** Test ball bouncing off paddles (velocity X inversion + speed increase).
    *   **Scoring:** Test that when ball passes left/right bounds, the correct player score increments and ball resets.
    *   **Victory Condition:** Test that game state transitions to "finished" when score limit is reached.
*   **Models (`test_models.py`):**
    *   Create a `MatchHistory` entry and verify all fields are saved correctly.
    *   Test any custom model methods (if added).

### 10.2 Integration Tests (`tests/integration/`)
These tests run against a **real** Daphne server instance using `ChannelsLiveServerTestCase`. **No mocks for the network layer.**
*   **Full Game Flow (`test_game_flow.py`):**
    1.  **Connect:** Open two WebSocket connections (Player 1, Player 2) to the same room code.
    2.  **Handshake:** Send "join_game" messages. Verify server acknowledges roles.
    3.  **Ready Up:** Send "player_ready" from both clients. Verify server sends "status_change: playing".
    4.  **State Sync:** Wait for `game_update` messages. Verify that initial positions are correct (50, 50).
    5.  **Movement:** Send "move_paddle" (up) from Player 1. Wait 100ms. Verify in next `game_update` that `p1_y` has decreased (moved up).
    6.  **Disconnect:** Close connection. Verify handled gracefully.
*   **Observer Flow:**
    1.  Connect P1 and P2.
    2.  Connect Observer 1.
    3.  Verify Observer receives `game_update` messages but sending input messages does NOT affect game state.
*   **Room Limits:**
    1.  Connect P1, P2.
    2.  Try to connect P3 as "player". Verify server rejects or forces role to "observer" (depending on design).

**Note:** Use `asyncio` within tests to manage concurrent WebSocket connections.
