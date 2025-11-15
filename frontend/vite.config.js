import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    allowedHosts: ['capital.limeox.com', '101.53.247.91'],
    proxy: {
      '/api': {
        target: 'http://101.53.247.91:9000',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    },
  },
})

