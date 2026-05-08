import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import api from './services/api'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const app = createApp(App)
const pinia = createPinia()

// 配置axios
app.config.globalProperties.$axios = api

app.use(pinia)
app.use(ElementPlus, {
  locale: zhCn
})
app.mount('#app')
