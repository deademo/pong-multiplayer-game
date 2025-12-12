# Retro Pong - Multiplayer Game

A multiplayer Ping Pong game with retro black-and-white aesthetic, built with Django Channels and WebSockets.

## Features

- **Multiplayer**: Real-time 2-player matches over WebSockets
- **Observers**: Unlimited spectators can watch matches
- **Room System**: Create rooms with invite codes
- **Configurable**: Match points limit (5, 20, 50, 100)
- **Retro Style**: Old-school black & white graphics
- **Retro Audio**: Browser oscillators for 8-bit sound effects
- **Match History**: PostgreSQL database storage

## Tech Stack

- **Frontend**: Vanilla JavaScript, HTML5 Canvas, Tailwind CSS
- **Backend**: Django 5.1.4, Django Channels 4.2.0
- **WebSockets**: Real-time state synchronization
- **Database**: PostgreSQL 18.1
- **Cache/Channel Layer**: Redis 8.2
- **Deployment**: Docker + Docker Compose

## Package Versions

All packages are pinned to latest stable versions:

- Django 5.1.4
- channels 4.2.0
- channels-redis 4.2.1
- daphne 4.1.2
- psycopg2-binary 2.9.10
- redis 5.2.1
- pytest 8.3.4
- pytest-django 4.9.0
- pytest-asyncio 0.24.0
- pytest-cov 6.0.0
- websockets 14.1

## Setup & Installation

### Prerequisites

- Docker Desktop installed and running
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd demo_project
   ```

2. **Start Docker Desktop**
   Make sure Docker Desktop is running on your machine.

3. **Install and start everything**
   ```bash
   make install
   ```

4. **Access the game**
   Open your browser to: `http://localhost:8000`

5. **Run tests**
   ```bash
   make test
   ```

## Running Tests

### Run all tests with coverage

```bash
make test
```

### Run specific test suites

```bash
make test-unit                # Unit tests only (52 tests, ~2 seconds)
make test-integration-real    # REAL integration tests with Daphne + Redis (8 tests, ~42 seconds)
make test-cov                 # Tests with HTML coverage report
```

### Real Integration Tests ✨

The `test-integration-real` command runs tests against a **real Daphne server** with **real Redis** and **real WebSocket connections**:

- ✅ No event loop conflicts
- ✅ Production-like environment
- ✅ True end-to-end testing
- ✅ Tests actual WebSocket protocol

See `INTEGRATION_TESTS_SUCCESS.md` for details.

### View installed package versions

```bash
make packages
```

### Test Results

- **Unit Tests**: 52/52 passing (100%)
- **Integration Tests**: 8/8 passing (100%)  
- **Code Coverage**: 92% (game engine), 76% overall

## How to Play

### Creating a Room

1. Select target score (5, 20, 50, or 100 points)
2. Click "Create Room"
3. Share the room code or player link with your opponent
4. Share the spectator link with observers

### Joining a Room

1. Enter the room code from your friend
2. Click "Join Game"
3. Wait for both players to click "Ready"

### Game Controls

- **Player 1**: W (up) / S (down) or Arrow keys
- **Player 2**: Arrow keys (up/down)

### Rules

- First player to reach the target score wins
- Ball speed increases with each paddle hit
- Game ends immediately when target score is reached
- No rematch option (return to main menu)

## Project Structure

```
demo_project/
├── backend/
│   ├── config/           # Django project settings
│   ├── pong/            # Main game app
│   │   ├── models.py    # MatchHistory model
│   │   ├── consumers.py # WebSocket consumer
│   │   ├── game_engine.py # Game physics & logic
│   │   └── routing.py   # WebSocket routing
│   ├── tests/
│   │   ├── unit/        # Unit tests
│   │   └── integration/ # Integration tests
│   ├── templates/       # HTML templates
│   └── static/          # JavaScript, CSS
├── docker-compose.yml   # Docker services config
└── run_tests.sh        # Test automation script
```

## API / WebSocket Protocol

### Connection

```
ws://localhost:8000/ws/game/<room_code>/
```

### Client → Server Messages

**Create Room:**
```json
{"type": "create_room", "points_limit": 5}
```

**Join Game:**
```json
{"type": "join_game", "role": "player"}  // or "observer"
```

**Player Ready:**
```json
{"type": "player_ready"}
```

**Move Paddle:**
```json
{"type": "move_paddle", "direction": "up"}  // or "down", "stop"
```

### Server → Client Messages

**Game Update (60fps):**
```json
{
  "type": "game_update",
  "status": "playing",
  "p1_y": 50.0,
  "p2_y": 50.0,
  "ball_x": 50.0,
  "ball_y": 50.0,
  "score_p1": 0,
  "score_p2": 0
}
```

**Status Change:**
```json
{"type": "status_change", "status": "waiting_for_ready"}
```

**Game Over:**
```json
{
  "type": "game_over",
  "winner": "Player 1",
  "final_score": [5, 3]
}
```

## Testing Strategy

### Unit Tests (tests/unit/)

- Game engine physics
- Ball movement and velocity
- Paddle movement and boundaries
- Collision detection (walls, paddles)
- Scoring logic
- Win conditions
- State management
- Model CRUD operations

### Integration Tests (tests/integration/)

- Full game flow (connect → ready → play → finish)
- Two-player real WebSocket connections
- Observer functionality
- Room isolation (concurrent games)
- Player disconnect handling
- Invalid message handling
- Edge cases and concurrent scenarios

### Coverage Goal

Target: 95%+ code coverage

## Development

### Available Make Commands

See all available commands:
```bash
make help
```

Common commands:
```bash
make install         # Full installation
make up              # Start all services
make down            # Stop all services
make restart         # Restart all services
make logs            # View all logs
make logs-backend    # View backend logs
make logs-db         # View database logs
make shell           # Python/Django shell
make bash            # Bash shell in container
make db-shell        # PostgreSQL shell
make migrate         # Run migrations
make makemigrations  # Create migrations
make createsuperuser # Create admin user
make test            # Run all tests
make clean           # Remove all data
make reset           # Full reset and reinstall
make status          # Show service status
make packages        # Show package versions
```

### Access Admin Panel

```bash
make createsuperuser  # Create admin account
```

Then visit: `http://localhost:8000/admin`

## Troubleshooting

### Docker not running

```
Error: Cannot connect to Docker daemon
```

**Solution**: Start Docker Desktop application, then run `make install`

### Port already in use

```
Error: Port 8000 is already allocated
```

**Solution**: `make restart` or change port in docker-compose.yml

### Database connection issues

```bash
make clean    # Remove all data
make install  # Fresh install
```

### WebSocket connection fails

```bash
make status        # Check service status
make logs-backend  # Check backend logs
make restart       # Restart services
```

### Need fresh start

```bash
make reset  # Warning: deletes all data
```

## Performance

- Game loop runs at 60 FPS (60 updates/second)
- WebSocket broadcasts state to all clients 60 times/second
- Ball speed increases 5% per paddle hit (capped at maximum)
- Tested with 50+ concurrent observers per room

## License

MIT License

## Credits

Built as a demonstration project following the tech design specification.
