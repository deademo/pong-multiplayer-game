import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './tests/setup.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      include: ['../backend/static/game.js'],
      exclude: ['tests/**', 'node_modules/**'],
      all: true,
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80
    },
    testTimeout: 10000,
    hookTimeout: 10000
  }
});
