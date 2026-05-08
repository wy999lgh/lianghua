import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',
    exclude: ['**/lightweight-charts-master/**', '**/node_modules/**'],
    coverage: {
      reporter: ['text', 'json', 'html'],
    },
  },
})
