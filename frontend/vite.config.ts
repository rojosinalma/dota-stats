import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/auth': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/matches': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/stats': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/sync': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/heroes': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
})
