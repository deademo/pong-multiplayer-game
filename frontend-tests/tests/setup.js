/**
 * Vitest setup file for frontend tests
 * Sets up JSDOM environment and mocks browser APIs
 */

import { vi } from 'vitest';

// Mock WebSocket
global.WebSocket = vi.fn().mockImplementation((url) => {
  const ws = {
    url,
    readyState: WebSocket.CONNECTING,
    CONNECTING: 0,
    OPEN: 1,
    CLOSING: 2,
    CLOSED: 3,
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    onopen: null,
    onclose: null,
    onerror: null,
    onmessage: null
  };
  return ws;
});

// Mock AudioContext
global.AudioContext = vi.fn().mockImplementation(() => ({
  createOscillator: vi.fn(() => ({
    frequency: { value: 0 },
    type: 'square',
    connect: vi.fn(),
    start: vi.fn(),
    stop: vi.fn()
  })),
  createGain: vi.fn(() => ({
    gain: {
      value: 0,
      setValueAtTime: vi.fn(),
      exponentialRampToValueAtTime: vi.fn()
    },
    connect: vi.fn()
  })),
  destination: {},
  currentTime: 0
}));

global.webkitAudioContext = global.AudioContext;

// Mock requestAnimationFrame and cancelAnimationFrame
let animationFrameId = 0;
global.requestAnimationFrame = vi.fn((callback) => {
  animationFrameId++;
  setTimeout(() => callback(Date.now()), 16);
  return animationFrameId;
});

global.cancelAnimationFrame = vi.fn((id) => {
  // Mock implementation
});

// Mock clipboard API
global.navigator.clipboard = {
  writeText: vi.fn().mockResolvedValue()
};

// Mock alert
global.alert = vi.fn();

// Mock console methods for cleaner test output
global.console = {
  ...console,
  log: vi.fn(),
  error: vi.fn(),
  warn: vi.fn()
};

// Setup DOM with basic HTML structure
document.body.innerHTML = `
  <div id="main-menu" class=""></div>
  <div id="lobby" class="hidden"></div>
  <div id="game-screen" class="hidden"></div>
  <div id="game-over" class="hidden"></div>
  
  <button id="create-room-btn"></button>
  <button id="join-room-btn"></button>
  <button id="ready-btn"></button>
  <button id="cancel-lobby-btn"></button>
  <button id="exit-game-btn"></button>
  <button id="main-menu-btn"></button>
  <button id="copy-code-btn"></button>
  <button id="copy-player-link-btn"></button>
  <button id="copy-observer-link-btn"></button>
  
  <select id="points-select"><option value="5">5</option></select>
  <input id="room-code-input" type="text"/>
  
  <canvas id="game-canvas" width="800" height="600"></canvas>
  
  <div id="lobby-room-code">------</div>
  <div id="lobby-status">WAITING</div>
  <input id="player-link" readonly/>
  <input id="observer-link" readonly/>
  
  <div id="score-p1">00</div>
  <div id="score-p2">00</div>
  
  <div id="winner-text">Winner</div>
  <div id="final-score-p1">0</div>
  <div id="final-score-p2">0</div>
  <div id="winner-badge-p1" class="hidden"></div>
  <div id="winner-badge-p2" class="hidden"></div>
`;
