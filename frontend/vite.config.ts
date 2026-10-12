import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
export default defineConfig({
  plugins: [react()],
  base: '/',
  build: {
    outDir: path.resolve(__dirname, 'dist'),
    emptyOutDir: true,
    assetsDir: 'assets',
    rollupOptions: { input: path.resolve(__dirname, 'vite-src/index.html') }
  },
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  server: { open: '/vite-src/index.html', proxy: { '/api': 'http://127.0.0.1:8000' } }
});
