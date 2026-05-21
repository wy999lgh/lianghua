console.log('🚀 开始加载 main.js...')

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import api from './services/api'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

console.log('✅ 所有模块导入成功')

const app = createApp(App)
const pinia = createPinia()

console.log('✅ Vue 应用创建成功')

// 配置axios
app.config.globalProperties.$axios = api
console.log('✅ axios 配置成功')

app.use(pinia)
console.log('✅ Pinia 安装成功')

app.use(ElementPlus, {
  locale: zhCn
})
console.log('✅ ElementPlus 安装成功')

app.mount('#app')
console.log('✅ 应用已挂载到 #app')
console.log('🎉 前端应用启动成功！')
