import { createApp } from 'vue'
import DebugApp from './DebugApp.vue'

console.log('🚀 正在启动调试应用...')

const app = createApp(DebugApp)
app.mount('#app')

console.log('✅ 调试应用已挂载到 #app')
