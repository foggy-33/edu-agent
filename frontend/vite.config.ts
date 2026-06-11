import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: (import.meta as any).env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
