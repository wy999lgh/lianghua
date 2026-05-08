import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true
      },
      '/stock-data': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
        rewrite: (path) => `/api${path}`
      },
      '/ema-data': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
        rewrite: (path) => `/api${path}`
      },
      '/data': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
        rewrite: (path) => `/api${path}`
      },
      '/strategies': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
        rewrite: (path) => `/api${path}`
      },
      '/backtest': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
        rewrite: (path) => `/api${path}`
      },
      '/factors': {
        target: 'http://127.0.0.1:8004',
        changeOrigin: true,
        rewrite: (path) => `/api${path}`
      }
    }
  },
  optimizeDeps: {
    exclude: ['lightweight-charts-master']
  }
})
