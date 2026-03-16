<template>
  <div class="kline-chart-container">
    <!-- 控制面板 -->
    <el-card class="control-panel">
      <template #header>
        <div class="panel-header">
          <div class="header-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <span class="title">ETF K线图表</span>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="6">
          <el-form-item label="股票代码">
            <template #label>
              <el-icon><CirclePlus /></el-icon>
              股票代码
            </template>
            <el-input 
              v-model="symbol" 
              placeholder="请输入股票代码" 
              @change="loadData"
            >
              <template #append>
                <el-button @click="loadData" :loading="loading">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
          </el-form-item>
        </el-col>
        
        <el-col :span="6">
          <el-form-item label="时间周期">
            <template #label>
              <el-icon><Timer /></el-icon>
              时间周期
            </template>
            <el-select v-model="timeframe" @change="loadData" class="light-select">
              <el-option label="日线" value="1d" />
              <el-option label="周线" value="1w" />
              <el-option label="月线" value="1m" />
            </el-select>
          </el-form-item>
        </el-col>
        
        <el-col :span="6">
          <el-form-item label="数据条数">
            <template #label>
              <el-icon><DataAnalysis /></el-icon>
              数据条数
            </template>
            <el-select v-model="dataLimit" @change="loadData" class="light-select">
              <el-option label="100条" :value="100" />
              <el-option label="300条" :value="300" />
              <el-option label="500条" :value="500" />
              <el-option label="1000条" :value="1000" />
            </el-select>
          </el-form-item>
        </el-col>
        
        <el-col :span="6">
          <el-form-item label="图表操作">
            <div class="button-group-custom">
              <el-button @click="zoomIn" class="action-btn" title="放大">
                <el-icon><ZoomIn /></el-icon>
              </el-button>
              <el-button @click="zoomOut" class="action-btn" title="缩小">
                <el-icon><ZoomOut /></el-icon>
              </el-button>
              <el-button @click="resetZoom" class="action-btn" title="重置缩放">
                <el-icon><FullScreen /></el-icon>
              </el-button>
              <el-button @click="toggleMA" :class="['action-btn', { active: showMA }]" plain>
                MA线
              </el-button>
              <el-button @click="toggleSignals" :class="['action-btn', { active: showSignals }]" plain>
                <el-icon><Position /></el-icon>信号
              </el-button>
            </div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <!-- 数据统计信息 -->
      <el-row :gutter="20" v-if="stats.total_records" class="stats-row">
        <el-col :span="4">
          <div class="stat-card">
            <div class="stat-icon blue">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">总记录数</div>
              <div class="stat-value">{{ stats.total_records }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="stat-card">
            <div class="stat-icon purple">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">日期范围</div>
              <div class="stat-value date-range">{{ stats.date_range?.start }} 至 {{ stats.date_range?.end }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="stat-card">
            <div class="stat-icon orange">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">价格区间</div>
              <div class="stat-value">{{ stats.price_range?.close?.min?.toFixed(2) }} - {{ stats.price_range?.close?.max?.toFixed(2) }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="stat-card">
            <div class="stat-icon green">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">平均成交量</div>
              <div class="stat-value">{{ formatVolume(stats.volume_stats?.average) }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="5">
          <div class="stat-card">
            <div class="stat-icon" :class="latestClose >= previousClose ? 'red' : 'green'">
              <el-icon><PriceTag /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-label">最新收盘价</div>
              <div class="stat-value" :class="getPriceClass(latestClose, previousClose)">
                {{ latestClose?.toFixed(2) }}
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 图表区域 -->
    <el-card class="chart-container">
      <div v-loading="loading" ref="chartRef" style="width: 100%; height: 500px;"></div>
    </el-card>
    

  </div>
</template>

<script>
import * as echarts from 'echarts'
import { Search, ZoomIn, ZoomOut, FullScreen, Position, Document, Calendar, TrendCharts, DataLine, PriceTag, CirclePlus, Timer, DataAnalysis } from '@element-plus/icons-vue'

export default {
  name: 'KLineChart',
  components: {
    Search,
    ZoomIn,
    ZoomOut,
    FullScreen,
    Position,
    Document,
    Calendar,
    TrendCharts,
    DataLine,
    PriceTag,
    CirclePlus,
    Timer,
    DataAnalysis
  },
  data() {
    return {
      chart: null,
      loading: false,
      timeframe: '1d',
      symbol: '159633',
      dataLimit: 300,
      showMA: true,
      showSignals: true,
      zoomLevel: 50,
      zoomStart: 50,
      zoomEnd: 100,
      historicalData: [],
      stats: {},
      latestClose: null,
      previousClose: null,
      tradeHistory: null // 交易历史数据
    }
  },
  props: {
    // 允许从父组件传入交易历史数据
    tradeHistory: {
      type: Array,
      default: null
    }
  },
  watch: {
    // 监听交易历史数据变化，更新图表
    tradeHistory: {
      handler() {
        this.updateChart()
      },
      deep: true
    }
  },
  mounted() {
    this.initChart()
    this.loadData()
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.dispose()
    }
  },
  methods: {
    initChart() {
      this.chart = echarts.init(this.$refs.chartRef)
      window.addEventListener('resize', () => {
        this.chart.resize()
      })
      
      // 监听dataZoom事件
      this.chart.on('dataZoom', this.onDataZoom)
    },
    
    async loadData() {
      this.loading = true
      try {
        console.log(`正在加载数据: symbol=${this.symbol}, limit=${this.dataLimit}`)
        const response = await this.$axios.get('/stock-data', {
          params: {
            symbol: this.symbol,
            limit: this.dataLimit
          }
        })
        
        console.log('数据加载成功:', response.data)
        
        if (!response.data || !Array.isArray(response.data.data)) {
          throw new Error('API返回的数据格式不正确')
        }

        this.historicalData = response.data.data.map(item => ({
          date: item.date ? item.date.split(' ')[0] : '',
          open: parseFloat(item.open),
          high: parseFloat(item.high),
          low: parseFloat(item.low),
          close: parseFloat(item.close),
          volume: parseInt(item.volume),
          change_percent: item.change_percent
        }))
        
        if (this.historicalData.length > 0) {
          this.latestClose = this.historicalData[0].close
          this.previousClose = this.historicalData.length > 1 ? this.historicalData[1].close : this.latestClose
        }
        
        await this.loadStats()
        
        this.updateChart()
        
      } catch (error) {
        console.error('加载数据失败详情:', error)
        let msg = error.message
        if (error.response && error.response.data) {
           // 尝试获取更详细的后端错误信息
           msg = error.response.data.detail || JSON.stringify(error.response.data)
        }
        console.warn('加载数据失败:', msg)
        this.$message.error('加载数据失败: ' + msg)
      } finally {
        this.loading = false
      }
    },
    
    async loadStats() {
      try {
        const response = await this.$axios.get(`/stock-data/stats/${this.symbol}`)
        this.stats = response.data.statistics
      } catch (error) {
        console.warn('加载统计数据失败 (可忽略):', error.message)
        this.stats = {}
      }
    },
    
    refreshData() {
      this.loadData()
    },
    
    toggleMA() {
      this.showMA = !this.showMA
      this.updateChart()
    },
    
    toggleSignals() {
      this.showSignals = !this.showSignals
      this.updateChart()
    },
    

    
    updateChart() {
      if (!this.chart || this.historicalData.length === 0) {
        return
      }
      
      // 将数据按时间正序排列（最早的数据在前）
      const sortedData = [...this.historicalData].reverse()
      
      // ECharts K线图数据格式：[open, close, low, high]
      const klineData = sortedData.map((item, index) => {
        return [
          item.open,
          item.close,
          item.low,
          item.high
        ];
      })
      
      const volumeData = sortedData.map(item => [
        item.date,
        item.volume
      ])
      
      const ma5 = this.calculateMA(5, sortedData)
      const ma10 = this.calculateMA(10, sortedData)
      const ma20 = this.calculateMA(20, sortedData)
      const ma30 = this.calculateMA(30, sortedData)
      
      const series = [
        {
          name: 'K线',
          type: 'candlestick',
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: klineData,
          itemStyle: {
            color: '#ef4136',
            color0: '#4caf50',
            borderColor: '#ef4136',
            borderColor0: '#4caf50',
            borderWidth: 1
          }
        }
      ]
      
      if (this.showMA) {
        series.push(
          { name: 'MA5', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma5, smooth: true, symbol: 'none', lineStyle: { color: '#0099ff', opacity: 0.8, width: 1 } },
          { name: 'MA10', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma10, smooth: true, symbol: 'none', lineStyle: { color: '#4caf50', opacity: 0.8, width: 1 } },
          { name: 'MA20', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma20, smooth: true, symbol: 'none', lineStyle: { color: '#000000', opacity: 0.8, width: 1 } },
          { name: 'MA30', type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: ma30, smooth: true, symbol: 'none', lineStyle: { color: '#ff9800', opacity: 0.8, width: 1 } }
        )
      }
      
      series.push({
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumeData,
        itemStyle: {
          color: function(params) {
            const index = params.dataIndex
            if (index < sortedData.length) {
              const item = sortedData[index]
              return item.close >= item.open ? '#ef4136' : '#4caf50'
            }
            return '#8392A5'
          }.bind(this)
        }
      })
      
      if (this.showSignals) {
        let buySignals = []
        let sellSignals = []
        
        // 优先使用交易历史数据
        if (this.tradeHistory && this.tradeHistory.length > 0) {
          // 处理交易历史数据
          const trades = this.tradeHistory
          
          // 转换交易历史数据为信号格式
          const tradeSignals = trades.map(trade => {
            // 处理日期格式，确保与K线图数据匹配
            const tradeDate = new Date(trade.datetime)
            const formattedDate = `${tradeDate.getFullYear()}-${String(tradeDate.getMonth() + 1).padStart(2, '0')}-${String(tradeDate.getDate()).padStart(2, '0')}`
            
            return {
              date: formattedDate,
              price: trade.price,
              type: trade.signal.toLowerCase()
            }
          })
          
          buySignals = tradeSignals.filter(signal => signal.type === 'buy')
          sellSignals = tradeSignals.filter(signal => signal.type === 'sell')
        } else {
          // 如果没有交易历史数据，使用传统的信号生成逻辑
          const signals = this.generateTradingSignals(sortedData)
          buySignals = signals.filter(signal => signal.type === 'buy')
          sellSignals = signals.filter(signal => signal.type === 'sell')
        }
        
        if (buySignals.length > 0) {
          series.push({
            name: '买入信号',
            type: 'scatter',
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: buySignals.map((signal) => {
              const index = sortedData.findIndex(item => item.date === signal.date)
              return index !== -1 ? [index, signal.price] : null
            }).filter(item => item !== null),
            symbol: 'triangle',
            symbolSize: 16,
            itemStyle: {
              color: '#ef4136', // 买入信号使用红色
              borderColor: '#fff',
              borderWidth: 2
            }
          })
        }
        
        if (sellSignals.length > 0) {
          series.push({
            name: '卖出信号',
            type: 'scatter',
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: sellSignals.map((signal) => {
              const index = sortedData.findIndex(item => item.date === signal.date)
              return index !== -1 ? [index, signal.price] : null
            }).filter(item => item !== null),
            symbol: 'triangle',
            symbolSize: 16,
            symbolRotate: 180,
            itemStyle: {
              color: '#4caf50', // 卖出信号使用绿色
              borderColor: '#fff',
              borderWidth: 2
            }
          })
        }
      }
      
      const option = {
        backgroundColor: '#fff',
        title: {
          text: `${this.symbol} K线图`,
          left: 'center',
          textStyle: { fontSize: 18, fontWeight: 'bold', color: '#1e293b' }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          backgroundColor: 'rgba(255, 255, 255, 0.98)',
          borderColor: '#e2e8f0',
          borderWidth: 1,
          padding: 12,
          textStyle: { color: '#1e293b' },
          formatter: function(params) {
            const dataIndex = params[0].dataIndex
            // 由于数据已经按时间正序排序，直接从sortedData中获取
            const sortedData = [...this.historicalData].reverse()
            const item = sortedData[dataIndex]
            if (!item) return ''
            
            let html = `<div style="font-size: 13px; font-weight: 600; margin-bottom: 8px;">${item.date}</div>`
            html += `<div style="display: grid; grid-template-columns: auto auto; gap: 4px 16px;">`
            html += `<div style="color: #64748b;">开盘:</div><div style="font-weight: 600;">${item.open.toFixed(3)}</div>`
            html += `<div style="color: #64748b;">最高:</div><div style="font-weight: 600; color: #ef4136;">${item.high.toFixed(3)}</div>`
            html += `<div style="color: #64748b;">最低:</div><div style="font-weight: 600; color: #4caf50;">${item.low.toFixed(3)}</div>`
            html += `<div style="color: #64748b;">收盘:</div><div style="font-weight: 600;">${item.close.toFixed(3)}</div>`
            html += `<div style="color: #64748b;">成交量:</div><div style="font-weight: 600;">${item.volume.toLocaleString()}</div>`
            html += `</div>`
            
            params.forEach(param => {
              if (param.seriesName && param.seriesName.startsWith('MA')) {
                html += `<div style="margin-top: 4px;"><span style="color: ${param.color}; font-weight: 600;">${param.seriesName}:</span> ${param.value ? param.value.toFixed(2) : 'N/A'}</div>`
              }
            })
            
            return html
          }.bind(this)
        },
        legend: {
          data: ['K线', ...(this.showMA ? ['MA5', 'MA10', 'MA20', 'MA30'] : []), '成交量', ...(this.showSignals ? ['买入信号', '卖出信号'] : [])],
          top: 40,
          textStyle: { fontSize: 12, color: '#64748b' }
        },
        grid: [
          { left: '8%', right: '8%', top: '18%', height: '50%' },
          { left: '8%', right: '8%', top: '75%', height: '15%' }
        ],
        xAxis: [
          {
            type: 'category',
            data: sortedData.map(item => item.date),
            boundaryGap: true,
            axisLine: { lineStyle: { color: '#e2e8f0' } },
            axisTick: { show: false },
            axisLabel: { color: '#64748b', fontSize: 11, rotate: 45 }
          },
          {
            type: 'category',
            gridIndex: 1,
            data: sortedData.map(item => item.date),
            boundaryGap: true,
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false }
          }
        ],
        yAxis: [
          {
            scale: true,
            splitArea: { show: false },
            axisLine: { lineStyle: { color: '#e2e8f0' } },
            axisTick: { show: false },
            axisLabel: { color: '#64748b', fontSize: 11 },
            splitLine: { lineStyle: { color: '#f1f5f9' } }
          },
          {
            scale: true,
            gridIndex: 1,
            splitNumber: 2,
            axisLabel: { show: false },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false }
          }
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1],
            start: 0,
            end: 100,
            zoomOnMouseWheel: true,
            moveOnMouseDrag: true,
            preventDefaultMouseMove: true
          },
          {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            bottom: '2%',
            start: 0,
            end: 100,
            height: 20,
            borderColor: '#e2e8f0',
            textStyle: { color: '#64748b' },
            handleStyle: { color: '#4f46e5', borderColor: '#4f46e5' },
            dataBackground: { lineStyle: { color: '#e2e8f0' }, areaStyle: { color: '#f1f5f9' } }
          }
        ],
        series: series
      }
      
      // 使用notMerge: false来合并配置，避免重复加载数据
      this.chart.setOption(option, false)
    },
    
    calculateMA(dayCount, data) {
      const result = []
      for (let i = 0; i < data.length; i++) {
        if (i < dayCount - 1) {
          result.push(null)
          continue
        }
        let sum = 0
        for (let j = 0; j < dayCount; j++) {
          sum += data[i - j].close
        }
        result.push(parseFloat((sum / dayCount).toFixed(2)))
      }
      return result
    },
    
    generateTradingSignals(data) {
      const signals = []
      if (!data || data.length < 2) return signals
      
      for (let i = 1; i < data.length; i++) {
        const current = data[i]
        const previous = data[i-1]
        const priceChange = ((current.close - previous.close) / previous.close) * 100
        
        if (priceChange < -1.5) {
          signals.push({ date: current.date, price: current.close, type: 'buy' })
        }
        else if (priceChange > 2.0) {
          signals.push({ date: current.date, price: current.close, type: 'sell' })
        }
      }
      
      return signals
    },
    
    formatVolume(volume) {
      if (!volume) return '-'
      if (volume >= 1000000) return (volume / 1000000).toFixed(2) + 'M'
      if (volume >= 1000) return (volume / 1000).toFixed(2) + 'K'
      return volume.toString()
    },
    
    getPriceClass(current, previous) {
      if (current > previous) return 'price-up'
      if (current < previous) return 'price-down'
      return 'price-neutral'
    },
    
    getChangeClass(change) {
      if (change > 0) return 'change-up'
      if (change < 0) return 'change-down'
      return 'change-neutral'
    },
    
    zoomIn() {
      const zoomStep = 10
      const newStart = Math.max(0, this.zoomStart - zoomStep)
      const newEnd = Math.min(100, this.zoomEnd - zoomStep)
      if (newEnd - newStart > 10) {
        this.zoomStart = newStart
        this.zoomEnd = newEnd
        this.updateChartZoom()
      }
    },
    
    zoomOut() {
      const zoomStep = 10
      const newStart = Math.max(0, this.zoomStart + zoomStep)
      const newEnd = Math.min(100, this.zoomEnd + zoomStep)
      this.zoomStart = newStart
      this.zoomEnd = newEnd
      this.updateChartZoom()
    },
    
    resetZoom() {
      this.zoomStart = 0
      this.zoomEnd = 100
      this.updateChartZoom()
    },
    
    updateChartZoom() {
      if (this.chart) {
        this.chart.dispatchAction({ type: 'dataZoom', xAxisIndex: [0, 1], start: this.zoomStart, end: this.zoomEnd })
      }
    },
    
    // 监听dataZoom事件，更新zoom状态
    onDataZoom(params) {
      if (params && params[0]) {
        this.zoomStart = params[0].start
        this.zoomEnd = params[0].end
      }
    }
  }
}
</script>

<style scoped>
.kline-chart-container {
  padding: 0;
}

.control-panel {
  margin-bottom: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border-radius: 10px;
  color: #fff;
  font-size: 20px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.button-group-custom {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  color: #64748b !important;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: #4f46e5 !important;
  border-color: #4f46e5 !important;
  color: #fff !important;
}

.action-btn.active {
  background: #4f46e5 !important;
  border-color: #4f46e5 !important;
  color: #fff !important;
}

.stats-row {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.stat-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 20px;
}

.stat-icon.blue { background: #dbeafe; color: #3b82f6; }
.stat-icon.purple { background: #f3e8ff; color: #8b5cf6; }
.stat-icon.orange { background: #ffedd5; color: #f97316; }
.stat-icon.green { background: #e8f5e9; color: #4caf50; }
.stat-icon.red { background: #ffebee; color: #ef4136; }

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.stat-value.date-range {
  font-size: 12px;
}

.chart-container {
  margin-bottom: 20px;
}



.price-text {
  font-weight: 600;
  color: #1e293b;
}

.volume-text {
  color: #64748b;
}

.price-up, .change-up {
  color: #ef4136 !important;
  font-weight: 700;
}

.price-down, .change-down {
  color: #4caf50 !important;
  font-weight: 700;
}

.price-neutral, .change-neutral {
  color: #64748b;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #64748b !important;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #e2e8f0;
  padding: 14px 20px;
}

:deep(.el-input-group__append) {
  background: #4f46e5 !important;
  border-color: #4f46e5 !important;
}

:deep(.el-input-group__append .el-button) {
  color: #fff !important;
}

.light-select {
  width: 100%;
}
</style>
