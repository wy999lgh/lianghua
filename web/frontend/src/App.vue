<template>
  <div class="app-container">
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header height="70px" class="header">
        <div class="header-left">
          <div class="logo-container">
            <div class="logo-icon">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <rect x="2" y="8" width="6" height="16" rx="2" fill="url(#grad1)"/>
                <rect x="10" y="4" width="6" height="24" rx="2" fill="url(#grad2)"/>
                <rect x="18" y="10" width="6" height="12" rx="2" fill="url(#grad3)"/>
                <rect x="26" y="6" width="4" height="20" rx="2" fill="url(#grad4)"/>
                <defs>
                  <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#4f46e5"/>
                    <stop offset="100%" style="stop-color:#7c3aed"/>
                  </linearGradient>
                  <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#7c3aed"/>
                    <stop offset="100%" style="stop-color:#ec4899"/>
                  </linearGradient>
                  <linearGradient id="grad3" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#4f46e5"/>
                    <stop offset="100%" style="stop-color:#06b6d4"/>
                  </linearGradient>
                  <linearGradient id="grad4" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#10b981"/>
                    <stop offset="100%" style="stop-color:#06b6d4"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div class="logo-text">
              <span class="logo-title">网格交易</span>
              <span class="logo-subtitle">量化策略系统</span>
            </div>
          </div>
        </div>
        
        <div class="nav-buttons">
          <el-button 
            :class="['nav-btn', { active: activeMenu === 'backtest' }]"
            @click="switchComponent('backtest', Backtest)"
          >
            <el-icon><DataAnalysis /></el-icon>
            <span>回测分析</span>
          </el-button>
          <el-button 
            :class="['nav-btn', { active: activeMenu === 'kline-chart' }]"
            @click="switchComponent('kline-chart', KLineChart)"
          >
            <el-icon><TrendCharts /></el-icon>
            <span>K线图</span>
          </el-button>
          <el-button 
            :class="['nav-btn', { active: activeMenu === 'data-management' }]"
            @click="switchComponent('data-management', DataManagement)"
          >
            <el-icon><Download /></el-icon>
            <span>数据管理</span>
          </el-button>
          <el-button 
            :class="['nav-btn', { active: activeMenu === 'performance' }]"
            @click="switchComponent('performance', Performance)"
          >
            <el-icon><TrendCharts /></el-icon>
            <span>性能分析</span>
          </el-button>
        </div>
        
        <div class="header-right">
          <div class="status-indicator">
            <span class="status-dot"></span>
            <span class="status-text">系统运行中</span>
          </div>
        </div>
      </el-header>

      <!-- 主要内容区域 -->
      <el-main class="main-content">
        <transition name="fade" mode="out-in">
          <component :is="currentComponent" :key="activeMenu" />
        </transition>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, provide } from 'vue'
import { DataAnalysis, Document, TrendCharts, Download } from '@element-plus/icons-vue'
import Backtest from './components/Backtest.vue'
import KLineChart from './components/KLineChart.vue'
import DataManagement from './components/DataManagement.vue'
import Performance from './components/Performance.vue'

export default {
  name: 'App',
  components: {
    DataAnalysis,
    Document,
    TrendCharts,
    Download,
    Backtest,
    KLineChart,
    DataManagement,
    Performance
  },
  setup() {
    const activeMenu = ref('backtest')
    const currentComponent = ref(Backtest)
    
    const gridConfig = ref({
      symbol: '',
      base_price: 10000,
      upper_step: 1,
      lower_step: 1,
      upper_count: 5,
      lower_count: 5,
      max_position: null,
      min_position: null
    })

    provide('gridConfig', gridConfig)
    provide('updateGridConfig', (newConfig) => {
      gridConfig.value = { ...newConfig }
    })

    const switchComponent = (menuKey, component) => {
      activeMenu.value = menuKey
      currentComponent.value = component
    }

    return {
      activeMenu,
      currentComponent,
      switchComponent,
      Backtest,
      KLineChart,
      DataManagement,
      Performance
    }
  }
}
</script>

<style>
.app-container {
  min-height: 100vh;
  background: transparent;
}

.header {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

.logo-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 2px;
  text-transform: uppercase;
}

.nav-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.nav-btn {
  color: rgba(255, 255, 255, 0.9) !important;
  background-color: rgba(255, 255, 255, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  border-radius: 10px !important;
  font-weight: 500;
  font-size: 14px;
  padding: 10px 18px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.25) !important;
  border-color: rgba(255, 255, 255, 0.4) !important;
  transform: translateY(-2px);
}

.nav-btn.active {
  background: rgba(255, 255, 255, 0.3) !important;
  border-color: rgba(255, 255, 255, 0.5) !important;
  color: #fff !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.nav-btn i {
  font-size: 16px;
}

.header-right {
  display: flex;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-text {
  font-size: 12px;
  color: #fff;
  font-weight: 500;
}

.main-content {
  padding: 28px;
  min-height: calc(100vh - 70px);
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(15px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-15px);
}

/* 卡片样式 */
.card {
  background: #fff !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
  }
  50% {
    opacity: 0.8;
    box-shadow: 0 0 0 6px rgba(16, 185, 129, 0);
  }
}
</style>
