<template>
  <div class="app-container">
    <el-container class="layout">
      <el-aside :width="isCollapsed ? '64px' : '220px'" class="aside">
        <div class="aside-header">
          <el-button class="collapse-btn" @click="isCollapsed = !isCollapsed" plain>
            {{ isCollapsed ? '展开' : '收起' }}
          </el-button>
        </div>
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapsed"
          class="menu"
          @select="handleSelect"
        >
          <el-menu-item index="grid-backtest">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>网格回测</template>
          </el-menu-item>
          <el-menu-item index="strategy-management">
            <el-icon><Setting /></el-icon>
            <template #title>策略管理</template>
          </el-menu-item>
          <el-menu-item index="universal-backtest">
            <el-icon><TrendCharts /></el-icon>
            <template #title>通用回测</template>
          </el-menu-item>
          <el-menu-item index="kline-chart">
            <el-icon><TrendCharts /></el-icon>
            <template #title>K线图</template>
          </el-menu-item>
          <el-menu-item index="data-management">
            <el-icon><Download /></el-icon>
            <template #title>数据管理</template>
          </el-menu-item>
          
          <el-menu-item index="factor-management">
            <el-icon><Grid /></el-icon>
            <template #title>因子管理</template>
          </el-menu-item>
          <el-menu-item index="backtest-history">
            <el-icon><Document /></el-icon>
            <template #title>回测历史</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
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
          <div class="header-right">
            <div class="status-indicator">
              <span class="status-dot"></span>
              <span class="status-text">系统运行中</span>
            </div>
          </div>
        </el-header>

        <el-main class="main-content">
          <transition name="fade" mode="out-in">
            <component :is="currentComponent" :key="activeMenu" />
          </transition>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { ref, provide } from 'vue'
import { DataAnalysis, TrendCharts, Download, Grid, Setting, Document } from '@element-plus/icons-vue'
import Backtest from './components/Backtest.vue'
import StrategyManagement from './components/StrategyManagement.vue'
import BacktestUniversal from './components/BacktestUniversal.vue'
import KLineChart from './components/KLineChart.vue'
import DataManagement from './components/DataManagement.vue'

import FactorManagement from './components/FactorManagement.vue'
import BacktestHistory from './components/BacktestHistory.vue'

export default {
  name: 'App',
  components: {
    DataAnalysis,
    TrendCharts,
    Download,
    Grid,
    Setting,
    Document,
    Backtest,
    StrategyManagement,
    BacktestUniversal,
    KLineChart,
    DataManagement,
    
    FactorManagement,
    BacktestHistory
  },
  setup() {
    const activeMenu = ref('grid-backtest')
    const currentComponent = ref(Backtest)
    const isCollapsed = ref(false)
    
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

    const handleSelect = (menuKey) => {
      const map = {
        'grid-backtest': Backtest,
        'strategy-management': StrategyManagement,
        'universal-backtest': BacktestUniversal,
        'kline-chart': KLineChart,
        'data-management': DataManagement,
        
        'factor-management': FactorManagement,
        'backtest-history': BacktestHistory
      }
      activeMenu.value = menuKey
      currentComponent.value = map[menuKey] || Backtest
    }

    return {
      activeMenu,
      currentComponent,
      isCollapsed,
      handleSelect,
      Backtest,
      StrategyManagement,
      BacktestUniversal,
      KLineChart,
      DataManagement,
      
      FactorManagement,
      BacktestHistory
    }
  }
}
</script>

<style>
.app-container {
  min-height: 100vh;
  background: transparent;
}

.layout {
  min-height: 100vh;
}

.aside {
  background: linear-gradient(180deg, #4f46e5 0%, #6d28d9 100%);
  color: #fff;
  box-shadow: 4px 0 24px rgba(79, 70, 229, 0.2);
  transition: width 0.3s ease;
}

.aside-header {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.collapse-btn {
  width: 100%;
  border-color: rgba(255, 255, 255, 0.4) !important;
  background: rgba(255, 255, 255, 0.15) !important;
  color: #fff !important;
  font-size: 12px;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.25) !important;
  border-color: rgba(255, 255, 255, 0.6) !important;
}

.menu {
  border-right: none !important;
  background: transparent !important;
}

/* 左侧菜单项样式 */
.menu .el-menu-item {
  color: rgba(255, 255, 255, 0.85) !important;
  border-radius: 8px !important;
  margin: 4px 8px !important;
  transition: all 0.3s ease !important;
}

.menu .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.15) !important;
  color: #fff !important;
}

.menu .el-menu-item.is-active {
  background: rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
  font-weight: 600 !important;
}

/* 菜单图标颜色 */
.menu .el-menu-item .el-icon {
  color: rgba(255, 255, 255, 0.85) !important;
}

.menu .el-menu-item.is-active .el-icon {
  color: #fff !important;
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
