/**
 * Pong Online - Frontend Game Logic
 * Handles WebSocket communication, Canvas rendering, input, and audio
 */

// Game state
let ws = null;
let currentScreen = 'main-menu';
let roomCode = null;
let playerRole = null; // 'player' or 'observer'
let playerNum = null; // 1 or 2
let gameState = {
    status: 'waiting_for_opponent',
    p1_y: 50,
    p2_y: 50,
    ball_x: 50,
    ball_y: 50,
    score_p1: 0,
    score_p2: 0,
    winner: null
};

// Canvas and rendering
let canvas = null;
let ctx = null;
let animationFrame = null;

// Audio context
let audioContext = null;

// Input state
let keysPressed = {};

// Constants
const FIELD_WIDTH = 100;
const FIELD_HEIGHT = 100;
const PADDLE_WIDTH = 2;
const PADDLE_HEIGHT = 20;
const BALL_SIZE = 2;

// DOM Elements
const screens = {
    'main-menu': document.getElementById('main-menu'),
    'lobby': document.getElementById('lobby'),
    'game-screen': document.getElementById('game-screen'),
    'game-over': document.getElementById('game-over')
};

const buttons = {
    createRoom: document.getElementById('create-room-btn'),
    joinRoom: document.getElementById('join-room-btn'),
    ready: document.getElementById('ready-btn'),
    cancelLobby: document.getElementById('cancel-lobby-btn'),
    exitGame: document.getElementById('exit-game-btn'),
    mainMenu: document.getElementById('main-menu-btn'),
    copyCode: document.getElementById('copy-code-btn'),
    copyPlayerLink: document.getElementById('copy-player-link-btn'),
    copyObserverLink: document.getElementById('copy-observer-link-btn')
};

const inputs = {
    pointsSelect: document.getElementById('points-select'),
    roomCodeInput: document.getElementById('room-code-input')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    canvas = document.getElementById('game-canvas');
    ctx = canvas.getContext('2d');
    setupCanvas();
    
    // Initialize audio context on first user interaction
    document.addEventListener('click', initAudio, { once: true });
});

function setupEventListeners() {
    // Button clicks
    buttons.createRoom.addEventListener('click', handleCreateRoom);
    buttons.joinRoom.addEventListener('click', handleJoinRoom);
    buttons.ready.addEventListener('click', handleReady);
    buttons.cancelLobby.addEventListener('click', handleCancelLobby);
    buttons.exitGame.addEventListener('click', handleExitGame);
    buttons.mainMenu.addEventListener('click', handleMainMenu);
    
    // Copy buttons
    buttons.copyCode.addEventListener('click', () => copyToClipboard(roomCode));
    buttons.copyPlayerLink.addEventListener('click', () => {
        const link = document.getElementById('player-link').value;
        copyToClipboard(link);
    });
    buttons.copyObserverLink.addEventListener('click', () => {
        const link = document.getElementById('observer-link').value;
        copyToClipboard(link);
    });
    
    // Keyboard controls
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);
    
    // Handle enter key in room code input
    inputs.roomCodeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleJoinRoom();
        }
    });
}

function setupCanvas() {
    // Set canvas size to maintain 4:3 aspect ratio
    const resizeCanvas = () => {
        const container = canvas.parentElement;
        const containerWidth = container.clientWidth;
        const containerHeight = container.clientHeight;
        
        // Calculate size maintaining 4:3 ratio
        let width = containerWidth;
        let height = width * 0.75; // 4:3 ratio
        
        if (height > containerHeight) {
            height = containerHeight;
            width = height * (4/3);
        }
        
        canvas.width = width;
        canvas.height = height;
    };
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
}

// WebSocket Functions
function connectWebSocket(room, role = 'player') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/game/${room}/`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        // Join the game
        ws.send(JSON.stringify({
            type: 'join_game',
            role: role
        }));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        alert('Connection error. Please try again.');
    };
    
    ws.onclose = () => {
        console.log('WebSocket closed');
        if (currentScreen === 'game-screen') {
            alert('Connection lost. Returning to main menu.');
            handleMainMenu();
        }
    };
}

function handleWebSocketMessage(data) {
    console.log('Received:', data);
    
    switch(data.type) {
        case 'room_created':
            console.log('Room created:', data.room_code);
            break;
            
        case 'joined_as_player':
            playerRole = 'player';
            playerNum = data.player_num;
            roomCode = data.room_code;
            showLobby();
            break;
            
        case 'joined_as_observer':
            playerRole = 'observer';
            roomCode = data.room_code;
            showLobby();
            break;
            
        case 'status_change':
            gameState.status = data.status;
            updateLobbyStatus(data.status);
            if (data.status === 'playing') {
                showGameScreen();
                startRenderLoop();
            }
            break;
            
        case 'game_update':
            gameState = { ...gameState, ...data };
            updateScoreboard();
            break;
            
        case 'game_over':
            gameState.winner = data.winner;
            gameState.score_p1 = data.final_score[0];
            gameState.score_p2 = data.final_score[1];
            stopRenderLoop();
            setTimeout(() => showGameOver(), 1000);
            playSound('game_over');
            break;
            
        case 'player_disconnected':
            alert(`Player ${data.player_num} disconnected`);
            handleMainMenu();
            break;
            
        case 'error':
            alert(`Error: ${data.message}`);
            break;
    }
}

// Screen Navigation
function showScreen(screenName) {
    Object.values(screens).forEach(screen => screen.classList.add('hidden'));
    screens[screenName].classList.remove('hidden');
    currentScreen = screenName;
}

function showLobby() {
    showScreen('lobby');
    
    // Update lobby UI
    document.getElementById('lobby-room-code').textContent = roomCode;
    
    const baseUrl = window.location.origin;
    document.getElementById('player-link').value = `${baseUrl}/?room=${roomCode}`;
    document.getElementById('observer-link').value = `${baseUrl}/?room=${roomCode}&role=observer`;
    
    // Enable/disable ready button
    if (playerRole === 'observer') {
        buttons.ready.disabled = true;
        buttons.ready.innerHTML = '<span>Observer Mode</span>';
    } else {
        buttons.ready.disabled = false;
    }
}

function showGameScreen() {
    showScreen('game-screen');
}

function showGameOver() {
    showScreen('game-over');
    
    // Update game over screen
    document.getElementById('winner-text').textContent = `${gameState.winner} Wins!`;
    document.getElementById('final-score-p1').textContent = gameState.score_p1.toString().padStart(2, '0');
    document.getElementById('final-score-p2').textContent = gameState.score_p2.toString().padStart(2, '0');
    
    // Show winner badge
    if (gameState.winner === 'Player 1') {
        document.getElementById('winner-badge-p1').classList.remove('hidden');
        document.getElementById('winner-badge-p2').classList.add('hidden');
    } else {
        document.getElementById('winner-badge-p2').classList.remove('hidden');
        document.getElementById('winner-badge-p1').classList.add('hidden');
    }
}

function updateLobbyStatus(status) {
    const statusText = document.getElementById('lobby-status');
    switch(status) {
        case 'waiting_for_opponent':
            statusText.textContent = 'WAITING FOR OPPONENT...';
            buttons.ready.disabled = true;
            break;
        case 'waiting_for_ready':
            statusText.textContent = 'PRESS READY TO START';
            if (playerRole === 'player') {
                buttons.ready.disabled = false;
            }
            break;
        case 'playing':
            statusText.textContent = 'GAME STARTING...';
            break;
    }
}

function updateScoreboard() {
    document.getElementById('score-p1').textContent = gameState.score_p1.toString().padStart(2, '0');
    document.getElementById('score-p2').textContent = gameState.score_p2.toString().padStart(2, '0');
}

// Button Handlers
function handleCreateRoom() {
    const pointsLimit = parseInt(inputs.pointsSelect.value);
    roomCode = generateRoomCode();
    
    connectWebSocket(roomCode, 'player');
    
    // Send room creation message after connection
    setTimeout(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'create_room',
                points_limit: pointsLimit
            }));
        }
    }, 100);
}

function handleJoinRoom() {
    const code = inputs.roomCodeInput.value.trim().toUpperCase();
    if (!code) {
        alert('Please enter a room code');
        return;
    }
    
    roomCode = code;
    
    // Check if joining as observer (from URL parameter)
    const urlParams = new URLSearchParams(window.location.search);
    const role = urlParams.get('role') === 'observer' ? 'observer' : 'player';
    
    connectWebSocket(roomCode, role);
}

function handleReady() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'player_ready'
        }));
        buttons.ready.disabled = true;
        buttons.ready.innerHTML = '<span>Waiting...</span>';
    }
}

function handleCancelLobby() {
    if (ws) {
        ws.close();
    }
    showScreen('main-menu');
}

function handleExitGame() {
    if (ws) {
        ws.close();
    }
    stopRenderLoop();
    showScreen('main-menu');
}

function handleMainMenu() {
    if (ws) {
        ws.close();
    }
    stopRenderLoop();
    showScreen('main-menu');
    
    // Reset state
    roomCode = null;
    playerRole = null;
    playerNum = null;
    gameState = {
        status: 'waiting_for_opponent',
        p1_y: 50,
        p2_y: 50,
        ball_x: 50,
        ball_y: 50,
        score_p1: 0,
        score_p2: 0,
        winner: null
    };
}

// Input Handling
function handleKeyDown(e) {
    if (currentScreen !== 'game-screen' || playerRole !== 'player') return;
    
    keysPressed[e.key] = true;
    
    let direction = null;
    
    // Player 1 controls (W/S or Arrow keys for player 1)
    // Player 2 controls (Arrow keys for player 2)
    if (playerNum === 1) {
        if (e.key === 'w' || e.key === 'W' || e.key === 'ArrowUp') {
            direction = 'up';
        } else if (e.key === 's' || e.key === 'S' || e.key === 'ArrowDown') {
            direction = 'down';
        }
    } else if (playerNum === 2) {
        if (e.key === 'ArrowUp') {
            direction = 'up';
        } else if (e.key === 'ArrowDown') {
            direction = 'down';
        }
    }
    
    if (direction && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'move_paddle',
            direction: direction
        }));
    }
}

function handleKeyUp(e) {
    if (currentScreen !== 'game-screen' || playerRole !== 'player') return;
    
    delete keysPressed[e.key];
    
    // Check if all movement keys are released
    const movementKeys = ['w', 'W', 's', 'S', 'ArrowUp', 'ArrowDown'];
    const anyPressed = movementKeys.some(key => keysPressed[key]);
    
    if (!anyPressed && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'move_paddle',
            direction: 'stop'
        }));
    }
}

// Rendering
function startRenderLoop() {
    if (!animationFrame) {
        render();
    }
}

function stopRenderLoop() {
    if (animationFrame) {
        cancelAnimationFrame(animationFrame);
        animationFrame = null;
    }
}

function render() {
    if (currentScreen !== 'game-screen') {
        stopRenderLoop();
        return;
    }
    
    // Clear canvas
    ctx.fillStyle = '#050b07';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Calculate scaling factors
    const scaleX = canvas.width / FIELD_WIDTH;
    const scaleY = canvas.height / FIELD_HEIGHT;
    
    // Draw center line
    ctx.strokeStyle = '#2bee79';
    ctx.lineWidth = 2;
    ctx.setLineDash([10, 10]);
    ctx.globalAlpha = 0.5;
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2, 0);
    ctx.lineTo(canvas.width / 2, canvas.height);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
    
    // Draw paddles
    ctx.fillStyle = '#2bee79';
    ctx.shadowColor = '#2bee79';
    ctx.shadowBlur = 10;
    
    // Player 1 paddle (left)
    const p1X = PADDLE_WIDTH * scaleX;
    const p1Y = gameState.p1_y * scaleY;
    const paddleWidth = PADDLE_WIDTH * scaleX;
    const paddleHeight = PADDLE_HEIGHT * scaleY;
    
    ctx.fillRect(
        p1X - paddleWidth / 2,
        p1Y - paddleHeight / 2,
        paddleWidth,
        paddleHeight
    );
    
    // Player 2 paddle (right)
    const p2X = (FIELD_WIDTH - PADDLE_WIDTH) * scaleX;
    const p2Y = gameState.p2_y * scaleY;
    
    ctx.fillRect(
        p2X - paddleWidth / 2,
        p2Y - paddleHeight / 2,
        paddleWidth,
        paddleHeight
    );
    
    // Draw ball
    const ballX = gameState.ball_x * scaleX;
    const ballY = gameState.ball_y * scaleY;
    const ballSize = BALL_SIZE * scaleX;
    
    ctx.fillRect(
        ballX - ballSize / 2,
        ballY - ballSize / 2,
        ballSize,
        ballSize
    );
    
    ctx.shadowBlur = 0;
    
    animationFrame = requestAnimationFrame(render);
}

// Audio
function initAudio() {
    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {
        console.warn('Web Audio API not supported');
    }
}

function playSound(type) {
    if (!audioContext) return;
    
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    switch(type) {
        case 'paddleHit':
            oscillator.frequency.value = 200;
            oscillator.type = 'square';
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
            break;
            
        case 'wallHit':
            oscillator.frequency.value = 150;
            oscillator.type = 'square';
            gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
            break;
            
        case 'score':
            oscillator.frequency.value = 100;
            oscillator.type = 'square';
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
            break;
            
        case 'game_over':
            oscillator.frequency.value = 80;
            oscillator.type = 'square';
            gainNode.gain.setValueAtTime(0.4, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
            break;
    }
}

// Utilities
function generateRoomCode() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code = '';
    for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            // Show brief success indication
            alert('Copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        alert('Copied to clipboard!');
    }
}

// Handle URL parameters for direct join
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const room = urlParams.get('room');
    
    if (room) {
        inputs.roomCodeInput.value = room;
        // Auto-join after a brief delay
        setTimeout(() => {
            handleJoinRoom();
        }, 500);
    }
});
