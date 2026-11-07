import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, timeout: 90_000,
  expect: { timeout: 12_000 }, reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5178', browserName: 'chromium',
    channel: process.env.PLAYWRIGHT_CHANNEL || (process.platform === 'win32' ? 'msedge' : undefined),
    headless: true, actionTimeout: 10_000, viewport: { width: 1440, height: 1000 }, locale: 'en-US', timezoneId: 'Asia/Kolkata',
    screenshot: 'only-on-failure', trace: 'retain-on-failure' },
});
