import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Shared proxy: frontend uses same-origin `/api` (see src/services/api.ts).
// Long-running AI calls need a high timeout; `vite preview` needs the same proxy as `vite dev`.
const apiProxy = {
  target: 'http://localhost:8000',
  changeOrigin: true,
  rewrite: (path: string) => path.replace(/^\/api/, ''),
  timeout: 300000,
  proxyTimeout: 300000,
} as const

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': apiProxy,
    },
  },
  preview: {
    proxy: {
      '/api': apiProxy,
    },
  },
})
