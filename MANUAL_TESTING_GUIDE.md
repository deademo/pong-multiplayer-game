# Manual Testing Guide - Player/Ball Visibility Fix

## Quick Start

### 1. Access the Application
Open your browser to: **http://localhost:8000**

### 2. Test the Bug Fix

#### Single Browser Test (Quick Check)
1. Click **"Create Room"**
2. **Expected**: You should see the lobby with room code
3. Note: Game won't start with only 1 player (need 2 players to test rendering)

#### Two Player Test (Full Verification)
You need **2 browser windows** or **1 browser + 1 incognito window**:

##### Window 1 (Player 1):
1. Go to http://localhost:8000
2. Click **"Create Room"**
3. Copy the **Room Code** (e.g., ABC123)
4. Copy the **Player Link** 
5. Keep this window open

##### Window 2 (Player 2):
1. Open a new browser window or incognito window
2. Go to http://localhost:8000
3. Either:
   - Paste the Player Link directly, OR
   - Enter the Room Code and click "Join Game"
4. Both windows should now be in the lobby

##### Start the Game:
1. **Window 1**: Click "Ready" button
2. **Window 2**: Click "Ready" button
3. Game should start immediately

##### ✅ Verify the Fix:
**YOU SHOULD NOW SEE**:
- ✅ **Two paddles** (one on left, one on right) - GREEN with neon glow
- ✅ **The ball** (white/green square) - moving between paddles
- ✅ **Scores** at the top (00 : 00)
- ✅ **Center dashed line**

**BEFORE THE FIX** (what was broken):
- ❌ Black screen with only scores visible
- ❌ No paddles visible
- ❌ No ball visible
- ❌ Game logic running but nothing rendering

### 3. Test Gameplay

#### Player 1 Controls:
- **W** or **Arrow Up**: Move paddle up
- **S** or **Arrow Down**: Move paddle down

#### Player 2 Controls:
- **Arrow Up**: Move paddle up
- **Arrow Down**: Move paddle down

#### What to Test:
1. ✅ Paddles move smoothly when you press keys
2. ✅ Ball bounces off paddles
3. ✅ Ball bounces off top/bottom walls
4. ✅ Score increases when ball passes paddle (goes off left/right edge)
5. ✅ Ball resets to center after score
6. ✅ Game ends when someone reaches target score (default: 5 points)
7. ✅ Game Over screen shows winner and final score

### 4. Observer Mode Test (Optional)

##### Window 3 (Observer):
1. Open a third browser window
2. Use the **Spectator Link** from Player 1's window
3. Click "Ready" is disabled (observer can't control)
4. **You should see**: The entire game rendering (paddles, ball, scores)
5. **You cannot**: Control any paddles

## Common Testing Scenarios

### Scenario 1: Quick 2-Player Game
1. Create room (Window 1)
2. Join room (Window 2)
3. Both click Ready
4. Play one point (let ball pass one paddle)
5. Verify score updates
6. Continue to 5 points
7. Verify game over screen

### Scenario 2: Test Disconnect
1. Start a game with 2 players
2. Close one browser window
3. Other player should see "Player disconnected" alert
4. Should return to main menu

### Scenario 3: Multiple Rooms
1. Create Room A (Windows 1 & 2)
2. Create Room B (Windows 3 & 4)
3. Both games should work independently
4. No interference between rooms

## Troubleshooting

### "Connection error" or WebSocket fails
```bash
# Check backend is running
docker compose ps

# Restart backend if needed
docker compose restart backend

# Check logs
docker compose logs backend --tail 50
```

### Game.js not loading (404 error)
```bash
# Check static files
curl -I http://localhost:8000/static/game.js

# Should return: HTTP/1.1 200 OK
```

### Paddles/ball still not visible
1. **Hard refresh** your browser: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
2. **Clear browser cache**
3. Check browser console (F12) for JavaScript errors
4. Verify game.js loaded:
   ```javascript
   // In browser console:
   console.log(currentScreen);  // Should show current screen
   ```

### Backend not responding
```bash
# Full restart
cd /Users/dea/Documents/intel471/demo_project
docker compose down
docker compose up -d

# Wait 5 seconds
sleep 5

# Test
curl http://localhost:8000/
```

## What Was Fixed

### Bug Details
**Problem**: Players and ball invisible when game started

**Root Cause**: Case mismatch in screen names
```javascript
// BROKEN (before fix)
function showGameScreen() {
    showScreen('gameScreen');  // ❌ camelCase
}

function render() {
    if (currentScreen !== 'game-screen') {  // ✓ kebab-case
        stopRenderLoop();  // ← This always happened!
        return;
    }
    // Rendering code never reached
}
```

**Fix**: Made all screen names use kebab-case consistently
```javascript
// FIXED (now)
function showGameScreen() {
    showScreen('game-screen');  // ✅ kebab-case
}

// Now currentScreen matches the check, rendering works!
```

### Files Changed
- `backend/static/game.js` - 5 case mismatches fixed
- Lines: 43-46, 209, 250, 254, 343, 351, 359, 558

## Expected Behavior

### Before Fix ❌
- Game starts (status changes to "playing")
- WebSocket updates received
- Scores update in background
- **BLACK SCREEN** - nothing visible
- Player controls sent but no visual feedback

### After Fix ✅
- Game starts (status changes to "playing")
- WebSocket updates received
- **PADDLES VISIBLE** with neon green glow
- **BALL VISIBLE** moving smoothly
- Scores update and visible
- Player controls work with visual feedback
- Complete game experience

## Testing Checklist

Use this checklist during manual testing:

### Setup
- [ ] Backend running (docker compose ps shows all services healthy)
- [ ] Browser 1 ready at http://localhost:8000
- [ ] Browser 2 ready (separate window/incognito)

### Room Creation & Joining
- [ ] Room created successfully
- [ ] Room code displayed (6 characters)
- [ ] Player link generated
- [ ] Observer link generated
- [ ] Second player can join via link
- [ ] Second player can join via room code

### Lobby
- [ ] Lobby screen shows room code
- [ ] Status shows "WAITING FOR OPPONENT" (before P2)
- [ ] Status shows "PRESS READY TO START" (after P2 joins)
- [ ] Ready button enabled for players
- [ ] Ready button disabled for observers
- [ ] Can copy room code
- [ ] Can copy links

### Game Start
- [ ] Both players click Ready
- [ ] Screen transitions to game view
- [ ] **CRITICAL: Both paddles visible** ✅
- [ ] **CRITICAL: Ball visible** ✅
- [ ] Scores visible (00 : 00)
- [ ] Center line visible (dashed)
- [ ] Background dark green/black

### Gameplay
- [ ] Player 1 paddle moves (W/S or arrows)
- [ ] Player 2 paddle moves (arrows)
- [ ] Ball moves automatically
- [ ] Ball bounces off paddles
- [ ] Ball bounces off top wall
- [ ] Ball bounces off bottom wall
- [ ] Ball speeds up after paddle hits
- [ ] Score increases when ball passes paddle
- [ ] Ball resets to center after score
- [ ] Ball serves toward last scorer

### Game End
- [ ] Game ends at 5 points (or configured limit)
- [ ] Game over screen appears
- [ ] Winner displayed correctly
- [ ] Final scores displayed
- [ ] Winner badge shown on correct player
- [ ] Can return to main menu
- [ ] Main menu loads correctly

### Observer Mode
- [ ] Observer can join via observer link
- [ ] Observer sees "Observer Mode" instead of Ready
- [ ] Observer cannot control paddles
- [ ] Observer sees full game rendering
- [ ] Observer sees score updates

### Error Handling
- [ ] Player disconnect shows alert
- [ ] Returns to main menu on disconnect
- [ ] Can create new room after disconnect
- [ ] Multiple rooms work independently

## Performance Notes

### Expected Performance
- **Smooth 60 FPS** rendering
- **No lag** in paddle movement
- **No jitter** in ball movement
- **Instant** score updates
- **Responsive** controls (<50ms)

### If Performance Issues
- Check browser console for errors
- Check Network tab for WebSocket disconnects
- Verify CPU usage isn't maxed (Activity Monitor/Task Manager)
- Try in Chrome/Firefox for comparison

## Success Criteria

✅ **Bug Fix Verified** if:
1. Both paddles are visible throughout the game
2. Ball is visible throughout the game
3. All game objects render with neon glow effect
4. Game plays from start to finish with full visual feedback

✅ **Ready for Production** if:
1. All checklist items pass
2. No console errors in browser
3. No crashes or freezes
4. Multiple games work independently
5. Observer mode works correctly

## Need Help?

### Check Logs
```bash
# Backend logs
make logs-backend

# All services
make logs

# Follow logs in real-time
docker compose logs -f backend
```

### Run Tests
```bash
# Frontend unit tests
make test-frontend

# Backend unit tests
make test-unit

# Integration tests
make test-integration-real
```

### Restart Everything
```bash
# Clean restart
make restart

# Or full reset
make clean
make install
```

---

**Ready to test!** Open http://localhost:8000 in two browser windows and verify paddles/ball are visible! 🎮
