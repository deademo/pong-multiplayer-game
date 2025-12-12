/**
 * Tests for the player/ball visibility bug fix
 */

import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

const gameJsPath = path.join(process.cwd(), 'backend/static/game.js');

describe('Player/Ball Visibility Bug - FIXED', () => {
  it('CRITICAL BUG FIX: showGameScreen must use correct screen name', () => {
    const content = fs.readFileSync(gameJsPath, 'utf-8');
    
    // Find the showGameScreen function
    const functionMatch = content.match(/function showGameScreen\(\)\s*{[^}]*}/);
    expect(functionMatch).toBeTruthy();
    
    const functionBody = functionMatch[0];
    
    // MUST use 'game-screen' not 'gameScreen'
    expect(functionBody).toContain("'game-screen'");
    expect(functionBody).not.toContain("'gameScreen'");
  });

  it('VERIFY FIX: render function checks correct screen name', () => {
    const content = fs.readFileSync(gameJsPath, 'utf-8');
    
    // Find the render function
    const renderMatch = content.match(/function render\(\)\s*{[\s\S]*?^}/m);
    expect(renderMatch).toBeTruthy();
    
    const renderBody = renderMatch[0];
    
    // Should check for 'game-screen'
    expect(renderBody).toContain("'game-screen'");
  });

  it('VERIFY FIX: screen names are consistent throughout', () => {
    const content = fs.readFileSync(gameJsPath, 'utf-8');
    
    // Extract all screen name references
    const mainMenuRefs = (content.match(/['"]main-menu['"]/g) || []).length;
    const lobbyRefs = (content.match(/['"]lobby['"]/g) || []).length;
    const gameScreenRefs = (content.match(/['"]game-screen['"]/g) || []).length;
    const gameOverRefs = (content.match(/['"]game-over['"]/g) || []).length;
    
    // All should use kebab-case consistently
    expect(mainMenuRefs).toBeGreaterThan(0);
    expect(lobbyRefs).toBeGreaterThan(0);
    expect(gameScreenRefs).toBeGreaterThan(0);
    expect(gameOverRefs).toBeGreaterThan(0);
    
    // Should NOT have camelCase versions
    expect(content).not.toContain("'gameScreen'");
    expect(content).not.toContain("'mainMenu'");
    expect(content).not.toContain("'gameOver'");
  });

  it('ROOT CAUSE: explains the bug that was fixed', () => {
    /**
     * BUG DESCRIPTION:
     * Players and ball were not visible when everyone connected and started playing.
     * 
     * ROOT CAUSE:
     * Line 250 in game.js had:
     *   function showGameScreen() {
     *     showScreen('gameScreen');  // ← WRONG (camelCase)
     *   }
     * 
     * But render() checked:
     *   if (currentScreen !== 'game-screen') {  // ← Expected kebab-case
     *     stopRenderLoop();
     *     return;
     *   }
     * 
     * RESULT:
     * - showGameScreen() set currentScreen = 'gameScreen'
     * - render() checked currentScreen !== 'game-screen'
     * - This was always true, so render stopped immediately
     * - No rendering = no visible paddles or ball!
     * 
     * FIX:
     * Changed line 250 to:
     *   showScreen('game-screen');  // ✓ Correct kebab-case
     */
    
    const content = fs.readFileSync(gameJsPath, 'utf-8');
    
    // Verify the fix is in place
    const showGameScreenFunc = content.match(/function showGameScreen\(\)[^}]*}/)[0];
    expect(showGameScreenFunc).toContain('game-screen');
    expect(showGameScreenFunc).not.toContain('gameScreen');
  });

  it('REGRESSION TEST: all helper functions use correct names', () => {
    const content = fs.readFileSync(gameJsPath, 'utf-8');
    
    // Check all screen helper functions
    const helperFunctions = [
      { name: 'showLobby', expectedCall: 'lobby' },
      { name: 'showGameScreen', expectedCall: 'game-screen' },
      { name: 'showGameOver', expectedCall: 'game-over' }
    ];
    
    helperFunctions.forEach(({ name, expectedCall }) => {
      const funcMatch = content.match(new RegExp(`function ${name}\\(\\)[^}]*}`));
      if (funcMatch) {
        const funcBody = funcMatch[0];
        // Should call showScreen with correct name
        expect(funcBody).toContain(`'${expectedCall}'`);
      }
    });
  });

  it('INTEGRATION: complete message flow uses correct screen names', () => {
    const content = fs.readFileSync(gameJsPath, 'utf-8');
    
    // When status changes to 'playing', showGameScreen is called
    const statusChangeHandler = content.match(/case\s+['"]status_change['"][\s\S]*?break/);
    expect(statusChangeHandler).toBeTruthy();
    
    const handler = statusChangeHandler[0];
    if (handler.includes("'playing'") && handler.includes('showGameScreen')) {
      // If showGameScreen is called on playing status, it must set correct name
      const showGameScreenFunc = content.match(/function showGameScreen\(\)[^}]*}/)[0];
      expect(showGameScreenFunc).toContain('game-screen');
    }
  });
});

describe('Code Structure Validation', () => {
  it('should have DOMContentLoaded listener', () => {
    const content = fs.readFileSync(gameJsPath, 'utf-8');
    expect(content).toContain('DOMContentLoaded');
  });

  it('should initialize canvas on load', () => {
    const content = fs.readFileSync(gameJsPath, 'utf-8');
    expect(content).toContain('getElementById(\'game-canvas\')');
    expect(content).toContain('getContext(\'2d\')');
  });

  it('should have proper screen element IDs', () => {
    const content = fs.readFileSync(gameJsPath, 'utf-8');
    
    const screenIds = ['main-menu', 'lobby', 'game-screen', 'game-over'];
    screenIds.forEach(id => {
      expect(content).toContain(`'${id}'`);
    });
  });
});
