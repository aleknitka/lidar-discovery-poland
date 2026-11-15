import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// `ldp dev --api-port N` sets LDP_API_URL; the default matches `ldp serve`.
const apiUrl = process.env.LDP_API_URL ?? 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': { target: apiUrl, changeOrigin: true } },
  },
  test: { environment: 'node', include: ['src/**/*.test.ts'] },
});
