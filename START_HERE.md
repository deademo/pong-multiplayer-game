# 🎮 Quick Start Guide

## Prerequisites Check

Before starting, ensure you have:

- ✅ Docker Desktop installed
- ✅ Docker Desktop is **RUNNING** (check system tray/menu bar)

## Step 1: Start Docker Desktop

**Important**: Docker must be running before executing any commands.

### Mac
Look for the Docker whale icon in your menu bar (top right)

### Windows
Look for the Docker whale icon in your system tray (bottom right)

### Verify Docker is running
```bash
docker info
```
If you see output without errors, Docker is running!

## Step 2: Build & Start the Game

```bash
cd /Users/dea/Documents/intel471/demo_project

# One command to install everything
make install

# Or step by step:
make build    # Build containers
make up       # Start services (includes migrations)
```

## Step 3: Access the Game

Open your browser to: **http://localhost:8000**

## Step 4: Run Tests

```bash
# Run all tests with coverage
make test

# Or run specific test suites:
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-cov          # Tests with HTML coverage report
```

## Troubleshooting

### "Cannot connect to Docker daemon"

**Solution**: Start Docker Desktop application first, then retry.

### Port 8000 already in use

```bash
# Stop services and restart
make restart
```

### Need to reset everything

```bash
# Reset everything (deletes all data)
make reset
```

## Quick Commands

```bash
# View all available commands
make help

# Common commands:
make up              # Start services
make down            # Stop services
make restart         # Restart services
make logs            # View all logs
make logs-backend    # View backend logs only
make test            # Run all tests
make shell           # Python shell
make bash            # Bash shell
make db-shell        # PostgreSQL shell
make clean           # Remove everything
make packages        # Show installed versions
```

## What's Running?

After `docker compose up -d`:

- **Backend (Django + Channels)**: http://localhost:8000
- **PostgreSQL Database**: localhost:5432
- **Redis**: localhost:6379

## Next Steps

1. Play the game at http://localhost:8000
2. Create a room and share the code with a friend
3. Check the tests are passing
4. View the README.md for detailed documentation

## Need Help?

Check the full README.md for:
- Detailed API documentation
- WebSocket protocol
- Development guide
- Full troubleshooting section
