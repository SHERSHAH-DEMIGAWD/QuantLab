import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

const target = process.env.QUANTLAB_API_TARGET || 'http://127.0.0.1:8000';
const proxy = { '/api': { target, changeOrigin: true } };

export default defineConfig({
  plugins: [react()],
  server: { host: '127.0.0.1', port: 5173, strictPort: true, proxy },
  preview: { host: '127.0.0.1', port: 4173, strictPort: true, proxy },
  test: { environment: 'jsdom', setupFiles: ['./src/test/setup.ts'], include: ['src/**/*.test.{ts,tsx}'] },
});
