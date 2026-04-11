import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
    copyPublicDir: true,
  },
  publicDir: 'public',
  server: {
    port: 3000,
  },
  assetsInclude: ['**/*.png', '**/*.jpg', '**/*.svg', '**/*.webp', '**/*.ico', '**/*.json'],
})
