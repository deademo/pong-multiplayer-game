# Frontend Unit Tests for Pong Online

This directory contains comprehensive unit tests for the frontend JavaScript code using Vitest.

## Technology Stack

- **Vitest** - Modern, fast testing framework (10-20x faster than Jest)
- **jsdom** - DOM environment for testing
- **Vitest UI** - Interactive test UI
- **Coverage** - Built-in code coverage with V8

## Why Vitest?

Based on 2024-2025 research, Vitest is the best choice because:
- 10-20x faster test execution than Jest
- Native ES modules support
- Better developer experience with watch mode
- Built-in TypeScript and JSX support
- Compatible with Jest API for easy migration
- Modern tooling with Vite

## Running Tests

### Local (with Node.js installed)

```bash
cd frontend-tests
npm install
npm test              # Run all tests
npm run test:watch    # Watch mode
npm run test:ui       # Interactive UI
npm run test:coverage # With coverage report
```

### Docker (recommended)

```bash
# From project root
make test-frontend           # Run frontend tests in Docker
make test-frontend-watch     # Watch mode in Docker
make test-frontend-coverage  # With coverage
```

Or directly with docker-compose:

```bash
docker-compose -f frontend-tests/docker-compose.frontend-tests.yml up
```

## Test Structure

```
frontend-tests/
├── tests/
│   ├── setup.js              # Test environment setup
│   ├── game.test.js          # Comprehensive game.js tests
│   └── bug-visibility.test.js # Specific bug reproduction tests
├── package.json
├── vitest.config.js
├── Dockerfile
└── docker-compose.frontend-tests.yml
```

## Test Coverage

Tests cover:

### Core Functionality
- ✅ Game state management
- ✅ WebSocket message handling
- ✅ Canvas rendering
- ✅ Input handling (keyboard)
- ✅ Audio system
- ✅ Screen navigation
- ✅ Lobby functionality
- ✅ Game over screen
- ✅ Utility functions

### Bug Fixes
- ✅ Player/ball visibility bug (case mismatch)
- ✅ Rendering coordinate calculations
- ✅ Screen transition edge cases

### Test Count
- **90+ unit tests** covering all major functionality
- **10+ bug-specific tests** for the visibility issue
- **Target: 80%+ code coverage** for game.js

## Bug Fix: Player and Ball Visibility

### The Problem
Players and ball were not visible when everyone was connected and playing.

### Root Cause
Case mismatch in `currentScreen` variable:
- `showGameScreen()` set `currentScreen = 'gameScreen'` (camelCase)
- `render()` checked `currentScreen !== 'game-screen'` (kebab-case)
- Render function thought it wasn't on game screen and stopped rendering

### The Fix
Changed line 250 in `game.js`:
```javascript
// BEFORE (broken)
function showGameScreen() {
    showScreen('gameScreen');  // Wrong case
}

// AFTER (fixed)
function showGameScreen() {
    showScreen('game-screen');  // Correct case
}
```

### Verification
Multiple tests verify the fix:
- `REPRODUCE BUG`: Tests currentScreen value after showGameScreen()
- `VERIFY FIX`: Tests render continues on game-screen
- `INTEGRATION`: Tests complete WebSocket flow with rendering
- `REGRESSION`: Ensures fix doesn't break other screens

## Adding New Tests

1. Create a new test file in `tests/` directory
2. Import necessary dependencies:
   ```javascript
   import { describe, it, expect, beforeEach, vi } from 'vitest';
   ```
3. Follow the existing test patterns
4. Run tests to verify: `npm test`

## CI/CD Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run Frontend Tests
  run: make test-frontend
```

## Coverage Reports

After running `npm run test:coverage`, check:
- Terminal output for summary
- `coverage/index.html` for detailed interactive report

## Troubleshooting

### Tests fail with "Cannot find module"
- Ensure `node_modules` is installed: `npm install`
- Check that `game.js` path in tests is correct

### Canvas-related test failures
- jsdom provides mock canvas context
- Some canvas features may have limited support

### Test timeout
- Increase timeout in `vitest.config.js` if needed
- Default is 10000ms (10 seconds)

## Performance

Typical test run times:
- All tests: ~2-3 seconds
- With coverage: ~4-5 seconds
- Watch mode: <500ms per change

Much faster than Jest equivalent! 🚀
