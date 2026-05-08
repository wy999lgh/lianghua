<template>
  <div class="kline-chart-container">
    <!-- 控制面板 -->
    <el-card class="control-panel">
      <template #header>
        <div class="panel-header">
          <div class="header-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <span class="title">K线图表</span>
        </div>
      </template>
      
      <div class="control-panel-wrapper">
        <div class="control-row">
          <div class="control-item">
            <el-input
              v-model="symbol"
              placeholder="股票代码"
              class="symbol-input"
              @keyup.enter="loadData"
            >
              <template #prepend>
                <el-icon><CirclePlus /></el-icon>
              </template>
              <template #append>
                <el-button @click="loadData" :loading="loading" type="primary">
                  <el-icon><Search /></el-icon>
                  加载
                </el-button>
              </template>
            </el-input>
          </div>
          
          <div class="control-item">
            <el-select v-model="timeframe" @change="loadData" placeholder="时间周期" class="form-select">
              <el-option label="日线" value="1d" />
              <el-option label="周线" value="1w" />
              <el-option label="月线" value="1m" />
            </el-select>
          </div>
          
          <div class="control-item">
            <el-select v-model="dataLimit" @change="loadData" placeholder="数据条数" class="form-select">
              <el-option label="100条" :value="100" />
              <el-option label="300条" :value="300" />
              <el-option label="500条" :value="500" />
              <el-option label="1000条" :value="1000" />
            </el-select>
          </div>
          
          <div class="control-item">
            <el-select v-model="emaPeriod" @change="loadEMAData" placeholder="EMA周期" class="form-select">
              <el-option label="EMA 5" :value="5" />
              <el-option label="EMA 10" :value="10" />
              <el-option label="EMA 20" :value="20" />
              <el-option label="EMA 30" :value="30" />
              <el-option label="EMA 60" :value="60" />
            </el-select>
          </div>
          
          <div class="control-item action-item">
            <div class="button-group">
              <el-button @click="resetZoom" class="action-btn" title="重置缩放">
                <el-icon><FullScreen /></el-icon>
              </el-button>
              <el-button @click="toggleMA" :class="['action-btn', { active: showMA }]" plain>
                MA线
              </el-button>
              <el-button @click="toggleEMA" :class="['action-btn', { active: showEMA }]" plain>
                EMA线
              </el-button>
              <el-button @click="toggleSignals" :class="['action-btn', { active: showSignals }]" plain>
                <el-icon><Position /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
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
      <div v-loading="loading" ref="chartContainer" style="width: 100%; height: 500px;"></div>
    </el-card>
    
  </div>
</template>

<script>
import { Search, FullScreen, Position, Document, Calendar, TrendCharts, DataLine, PriceTag, CirclePlus, Timer, DataAnalysis, Setting } from '@element-plus/icons-vue'

export default {
  name: 'KLineChart',
  components: {
    Search,
    FullScreen,
    Position,
    Document,
    Calendar,
    TrendCharts,
    DataLine,
    PriceTag,
    CirclePlus,
    Timer,
    DataAnalysis,
    Setting
  },
  data() {
    return {
      chart: null,
      candlestickSeries: null,
      volumeSeries: null,
      ma5Series: null,
      ma10Series: null,
      ma20Series: null,
      ma30Series: null,
      emaSegmentSeries: [],
      loading: false,
      timeframe: '1d',
      symbol: '999999',
      dataLimit: 300,
      showMA: false,
      showEMA: false,
      showSignals: false,
      emaPeriod: 20,
      historicalData: [],
      emaRawData: [],
      stats: {},
      latestClose: null,
      previousClose: null,
      resizeHandler: null,
      // 数据缓存
      dataCache: {},
      cacheTimeout: 5 * 60 * 1000 // 5分钟缓存
    }
  },
  props: {
    tradeHistory: {
      type: Array,
      default: null
    }
  },
  watch: {
    tradeHistory: {
      handler() {
        this.updateChart()
      },
      deep: true
    },
    // 股票代码变更时清除缓存
    symbol() {
      this.clearCache()
    }
  },
  mounted() {
    this.initChart()
    this.loadData()
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.remove()
    }
    if (this.resizeHandler) {
      window.removeEventListener('resize', this.resizeHandler)
    }
  },
  methods: {
    initChart() {
      // 检查 LightweightCharts 是否加载
      if (typeof LightweightCharts === 'undefined') {
        console.error('LightweightCharts 库未加载')
        this.$message.error('LightweightCharts 库未加载')
        return
      }
      
      // 检查图表容器是否存在
      if (!this.$refs.chartContainer) {
        console.error('图表容器不存在')
        this.$message.error('图表容器不存在')
        return
      }
      
      // 打印容器尺寸
      console.log('容器尺寸:', this.$refs.chartContainer.clientWidth, 'x', this.$refs.chartContainer.clientHeight)
      
      // 创建图表
      try {
        this.chart = LightweightCharts.createChart(this.$refs.chartContainer, {
          layout: {
            background: { color: '#ffffff' },
            textColor: '#1e293b',
          },
          grid: {
            vertLines: { color: '#e2e8f0' },
            horzLines: { color: 'rgba(0, 0, 0, 0)' },
          },
          crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: {
              color: 'rgba(0, 0, 0, 0)',
              style: 1,
              width: 1,
            },
            horzLine: {
              color: 'rgba(0, 0, 0, 0)',
              style: 1,
              width: 1,
            },
          },
          rightPriceScale: {
            borderColor: '#e2e8f0',
            gridLinesColor: 'rgba(0, 0, 0, 0)',
          },
          leftPriceScale: {
            borderColor: 'rgba(0, 0, 0, 0)',
            gridLinesColor: 'rgba(0, 0, 0, 0)',
          },
          timeScale: {
            borderColor: '#e2e8f0',
            timeVisible: true,
            gridLinesColor: 'rgba(0, 0, 0, 0)',
          },
          width: this.$refs.chartContainer.clientWidth,
          height: this.$refs.chartContainer.clientHeight,
        })
        console.log('图表创建成功')
      } catch (error) {
        console.error('图表创建失败:', error)
        this.$message.error('图表创建失败: ' + error.message)
        return
      }
      
      // 添加蜡烛图系列
      try {
        this.candlestickSeries = this.chart.addCandlestickSeries({
          upColor: '#ef4136',
          downColor: '#4caf50',
          borderUpColor: '#ef4136',
          borderDownColor: '#4caf50',
          wickUpColor: '#ef4136',
          wickDownColor: '#4caf50',
        })
        console.log('蜡烛图系列添加成功')
      } catch (error) {
        console.error('添加蜡烛图系列失败:', error)
        this.$message.error('添加蜡烛图系列失败: ' + error.message)
      }
      
      // 添加成交量系列（在独立的价格刻度上）
      try {
        this.volumeSeries = this.chart.addHistogramSeries({
          priceFormat: {
            type: 'volume',
          },
          priceScaleId: '',
          scaleMargins: {
            top: 0.8,
            bottom: 0,
          },
        })
        console.log('成交量系列添加成功')
        
        if (this.volumeSeries && this.volumeSeries.priceScale) {
          this.volumeSeries.priceScale().applyOptions({
            scaleMargins: {
              top: 0.8,
              bottom: 0,
            },
            gridLinesColor: 'rgba(0, 0, 0, 0)',
          })
        }
      } catch (error) {
        console.error('添加成交量系列失败:', error)
        this.$message.error('添加成交量系列失败: ' + error.message)
      }
      
      // 添加MA线系列
      try {
        this.ma5Series = this.chart.addLineSeries({
          color: '#0099ff',
          lineWidth: 1,
          title: 'MA5',
        })
        console.log('MA5系列添加成功')
      } catch (error) {
        console.error('添加MA5系列失败:', error)
      }
      
      try {
        this.ma10Series = this.chart.addLineSeries({
          color: '#4caf50',
          lineWidth: 1,
          title: 'MA10',
        })
        console.log('MA10系列添加成功')
      } catch (error) {
        console.error('添加MA10系列失败:', error)
      }
      
      try {
        this.ma20Series = this.chart.addLineSeries({
          color: '#000000',
          lineWidth: 1,
          title: 'MA20',
        })
        console.log('MA20系列添加成功')
      } catch (error) {
        console.error('添加MA20系列失败:', error)
      }
      
      try {
        this.ma30Series = this.chart.addLineSeries({
          color: '#ff9800',
          lineWidth: 1,
          title: 'MA30',
        })
        console.log('MA30系列添加成功')
      } catch (error) {
        console.error('添加MA30系列失败:', error)
      }
      
      // EMA系列在updateChart中按需动态创建

      // 窗口大小改变时调整图表大小
      this.resizeHandler = () => {
        if (this.chart && this.$refs.chartContainer) {
          this.chart.applyOptions({
            width: this.$refs.chartContainer.clientWidth,
            height: this.$refs.chartContainer.clientHeight,
          })
        }
      }
      window.addEventListener('resize', this.resizeHandler)
    },
    
    /**
     * 检查缓存是否有效
     */
    isCacheValid(cacheKey) {
      const cached = this.dataCache[cacheKey]
      if (!cached) return false
      return Date.now() - cached.timestamp < this.cacheTimeout
    },

    /**
     * 获取缓存数据
     */
    getFromCache(cacheKey) {
      const cached = this.dataCache[cacheKey]
      return cached ? cached.data : null
    },

    /**
     * 设置缓存数据
     */
    setCache(cacheKey, data) {
      this.dataCache[cacheKey] = {
        data: data,
        timestamp: Date.now()
      }
    },

    /**
     * 清除缓存
     */
    clearCache() {
      this.dataCache = {}
    },

    /**
     * 加载数据（优化版 - 并行请求 + 缓存）
     */
    async loadData() {
      this.loading = true
      try {
        console.log(`正在加载数据: symbol=${this.symbol}, limit=${this.dataLimit}`)
        
        // 检查K线数据缓存
        const klineCacheKey = `kline_${this.symbol}_${this.dataLimit}`
        let klineData = null
        
        if (this.isCacheValid(klineCacheKey)) {
          console.log('使用K线数据缓存')
          klineData = this.getFromCache(klineCacheKey)
        } else {
          console.log('请求K线数据')
          const response = await this.$axios.get('/stock-data', {
            params: {
              symbol: this.symbol,
              limit: this.dataLimit
            }
          })
          
          if (!response.data || !Array.isArray(response.data.data)) {
            throw new Error('API返回的数据格式不正确')
          }
          
          klineData = response.data
          // 缓存K线数据
          this.setCache(klineCacheKey, klineData)
        }
        
        // 处理K线数据
        this.historicalData = klineData.data.map(item => ({
          time: item.date ? item.date.split(' ')[0] : '',
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
        
        // 优化：并行请求统计数据和EMA数据
        const promises = []
        
        // 并行请求统计数据
        promises.push(
          this.loadStats().catch(error => {
            console.warn('加载统计数据失败 (可忽略):', error.message)
            this.stats = {}
          })
        )
        
        // 并行请求EMA数据（如果开启）
        if (this.showEMA) {
          promises.push(
            this.loadEMAData().catch(error => {
              console.warn('加载 EMA 数据失败:', error.message)
              this.emaRawData = []
            })
          )
        } else {
          this.emaRawData = []
        }
        
        // 等待所有并行请求完成
        await Promise.all(promises)
        
        // 更新图表
        this.updateChart()
        
      } catch (error) {
        console.error('加载数据失败详情:', error)
        let msg = error.message
        if (error.response && error.response.data) {
           msg = error.response.data.detail || JSON.stringify(error.response.data)
        }
        console.warn('加载数据失败:', msg)
        this.$message.error('加载数据失败: ' + msg)
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 加载EMA数据（优化版 - 添加缓存）
     */
    async loadEMAData() {
      if (!this.showEMA) return

      // 检查EMA缓存（固定使用斜率过滤）
      const emaCacheKey = `ema_${this.symbol}_${this.emaPeriod}_${this.dataLimit}_1`
      if (this.isCacheValid(emaCacheKey)) {
        console.log('使用EMA数据缓存')
        this.emaRawData = this.getFromCache(emaCacheKey)
        this.updateChart()
        return
      }

      try {
        console.log('请求EMA数据')
        const response = await this.$axios.get('/ema-data', {
          params: {
            symbol: this.symbol,
            period: this.emaPeriod,
            limit: this.dataLimit,
            slope_filter: 1
          }
        })
        this.emaRawData = response.data.data || []
        // 缓存EMA数据
        this.setCache(emaCacheKey, this.emaRawData)
        this.updateChart()
      } catch (error) {
        console.warn('加载 EMA 数据失败:', error.message)
        this.emaRawData = []
      }
    },

    _clearEMASegments() {
      if (!this.chart) return
      for (const series of this.emaSegmentSeries) {
        try { this.chart.removeSeries(series) } catch (e) { /* ignore */ }
      }
      this.emaSegmentSeries = []
    },

    _splitEMASegments(emaData) {
      if (!emaData.length) return []
      const segments = []
      let start = 0
      for (let i = 1; i < emaData.length; i++) {
        if (emaData[i].direction !== emaData[start].direction) {
          segments.push({
            direction: emaData[start].direction,
            points: emaData.slice(start, i + 1)
          })
          start = i
        }
      }
      if (start < emaData.length) {
        segments.push({
          direction: emaData[start].direction,
          points: emaData.slice(start)
        })
      }
      return segments
    },
    
    /**
     * 加载统计数据（优化版 - 添加缓存）
     */
    async loadStats() {
      // 检查统计数据缓存
      const statsCacheKey = `stats_${this.symbol}`
      if (this.isCacheValid(statsCacheKey)) {
        console.log('使用统计数据缓存')
        this.stats = this.getFromCache(statsCacheKey)
        return
      }
      
      try {
        console.log('请求统计数据')
        const response = await this.$axios.get(`/stock-data/stats/${this.symbol}`)
        this.stats = response.data.statistics
        // 缓存统计数据
        this.setCache(statsCacheKey, this.stats)
      } catch (error) {
        console.warn('加载统计数据失败 (可忽略):', error.message)
        this.stats = {}
      }
    },
    
    /**
     * 刷新数据（清除缓存后重新加载）
     */
    refreshData() {
      this.clearCache()
      this.loadData()
    },
    
    toggleMA() {
      this.showMA = !this.showMA
      this.updateChart()
    },
    
    toggleEMA() {
      this.showEMA = !this.showEMA
      if (this.showEMA && this.emaRawData.length === 0) {
        this.loadEMAData()
      } else {
        this.updateChart()
      }
    },
    
    toggleSignals() {
      this.showSignals = !this.showSignals
      this.updateChart()
    },
    
    updateChart() {
      if (!this.chart || !this.candlestickSeries || !this.volumeSeries || this.historicalData.length === 0) {
        console.error('图表或系列对象未初始化')
        return
      }
      
      // 将数据按时间正序排列（最早的数据在前）
      const sortedData = [...this.historicalData].reverse()
      
      // 准备蜡烛图数据，确保所有值都是有效的数字
      const candlestickData = sortedData.map(item => ({
        time: item.time || '',
        open: Number(item.open) || 0,
        high: Number(item.high) || 0,
        low: Number(item.low) || 0,
        close: Number(item.close) || 0,
      })).filter(item => {
        // 过滤掉无效数据
        return item.time && item.open > 0 && item.high > 0 && item.low > 0 && item.close > 0
      })
      
      // 准备成交量数据
      const volumeData = sortedData.map(item => ({
        time: item.time || '',
        value: Number(item.volume) || 0,
        color: item.close >= item.open ? '#ef4136' : '#4caf50',
      })).filter(item => {
        // 过滤掉无效数据
        return item.time && item.value >= 0
      })
      
      console.log('Candlestick data:', candlestickData)
      console.log('Volume data:', volumeData)
      
      // 确保数据不为空
      if (candlestickData.length === 0 || volumeData.length === 0) {
        console.error('No valid data to display')
        this.$message.error('没有有效的数据可以显示')
        return
      }
      
      // 设置蜡烛图数据
      try {
        this.candlestickSeries.setData(candlestickData)
      } catch (error) {
        console.error('Error setting candlestick data:', error)
      }
      
      // 设置成交量数据
      try {
        this.volumeSeries.setData(volumeData)
      } catch (error) {
        console.error('Error setting volume data:', error)
      }
      
      // 计算并设置MA线数据
      if (this.showMA) {
        const ma5Data = this.calculateMAData(5, sortedData)
        const ma10Data = this.calculateMAData(10, sortedData)
        const ma20Data = this.calculateMAData(20, sortedData)
        const ma30Data = this.calculateMAData(30, sortedData)
        
        if (this.ma5Series) this.ma5Series.setData(ma5Data)
        if (this.ma10Series) this.ma10Series.setData(ma10Data)
        if (this.ma20Series) this.ma20Series.setData(ma20Data)
        if (this.ma30Series) this.ma30Series.setData(ma30Data)
        
        if (this.ma5Series) this.ma5Series.applyOptions({ visible: true })
        if (this.ma10Series) this.ma10Series.applyOptions({ visible: true })
        if (this.ma20Series) this.ma20Series.applyOptions({ visible: true })
        if (this.ma30Series) this.ma30Series.applyOptions({ visible: true })
      } else {
        if (this.ma5Series) this.ma5Series.applyOptions({ visible: false })
        if (this.ma10Series) this.ma10Series.applyOptions({ visible: false })
        if (this.ma20Series) this.ma20Series.applyOptions({ visible: false })
        if (this.ma30Series) this.ma30Series.applyOptions({ visible: false })
      }
      
      // 绘制EMA均线：按方向分段显示，不同颜色区分趋势，与MA线位置一致
      this._clearEMASegments()
      if (this.showEMA && this.emaRawData.length > 0) {
        const segments = this._splitEMASegments(this.emaRawData)
        const colorMap = { up: '#ef4136', down: '#22c55e', flat: '#616161' }
        for (const seg of segments) {
          if (seg.points.length < 2) continue
          try {
            const series = this.chart.addLineSeries({
              lineWidth: 2,
              color: colorMap[seg.direction] || '#616161',
            })
            series.setData(seg.points.map(p => ({ time: p.time, value: p.value })))
            this.emaSegmentSeries.push(series)
          } catch (e) {
            console.warn('添加EMA分段系列失败:', e)
          }
        }
      }

      // 添加交易信号标记
      let markers = []
      
      // 交易信号标记
      if (this.showSignals) {
        const signalMarkers = this.getTradeSignalsMarkers(sortedData)
        markers = [...markers, ...signalMarkers]
      }
      
      // 设置标记
      if (this.candlestickSeries && this.candlestickSeries.setMarkers) {
        this.candlestickSeries.setMarkers(markers)
      }
      
      // 调整图表以适应数据
      this.chart.timeScale().fitContent()
    },
    
    calculateMAData(dayCount, data) {
      const result = []
      for (let i = 0; i < data.length; i++) {
        if (i < dayCount - 1) {
          continue
        }
        let sum = 0
        let validCount = 0
        for (let j = 0; j < dayCount; j++) {
          const closeValue = Number(data[i - j].close)
          if (!isNaN(closeValue) && closeValue > 0) {
            sum += closeValue
            validCount++
          }
        }
        if (validCount > 0) {
          result.push({
            time: data[i].time,
            value: parseFloat((sum / validCount).toFixed(2))
          })
        }
      }
      return result
    },
    

    
    getTradeSignalsMarkers(data) {
      let markers = []
      
      // 高低点识别算法（两阶段过滤）
      // 第一阶段：5根K线窗口识别局部高低点
      // 第二阶段：每3个局部高低点比较，找出最显著的高低点
      
      const window = 5     // 局部高低点识别窗口
      const groupSize = 3  // 每组比较的局部高低点数量
      
      // ========== 第一阶段：识别所有局部高低点 ==========
      let localHighs = []   // 存储局部高点 {index, price, time}
      let localLows = []    // 存储局部低点 {index, price, time}
      
      for (let i = window; i < data.length - window; i++) {
        try {
          const currentHigh = Number(data[i].high)
          const currentLow = Number(data[i].low)
          
          if (isNaN(currentHigh) || isNaN(currentLow)) {
            continue
          }
          
          // 检查是否是局部高点（前后window根K线的最高价）
          let isHigh = true
          for (let j = 1; j <= window; j++) {
            if (Number(data[i - j].high) >= currentHigh || Number(data[i + j].high) >= currentHigh) {
              isHigh = false
              break
            }
          }
          
          // 检查是否是局部低点（前后window根K线的最低价）
          let isLow = true
          for (let j = 1; j <= window; j++) {
            if (Number(data[i - j].low) <= currentLow || Number(data[i + j].low) <= currentLow) {
              isLow = false
              break
            }
          }
          
          if (isHigh) {
            localHighs.push({
              index: i,
              price: currentHigh,
              time: data[i].time
            })
          }
          
          if (isLow) {
            localLows.push({
              index: i,
              price: currentLow,
              time: data[i].time
            })
          }
        } catch (error) {
          console.error('Error identifying local high/low:', error)
        }
      }
      
      // ========== 第二阶段：每3个局部高低点比较，找出最显著的点 ==========
      
      // 处理高点：每3个一组，找出最高的那个
      for (let i = 0; i < localHighs.length; i += groupSize) {
        const group = localHighs.slice(i, i + groupSize)
        if (group.length === 0) continue
        
        // 找出组内最高的高点
        const highest = group.reduce((max, curr) => curr.price > max.price ? curr : max)
        
        markers.push({
          time: highest.time,
          position: 'aboveBar',
          color: '#ef4136',
          shape: 'arrowDown',
          text: '高',
          size: 2,
        })
      }
      
      // 处理低点：每3个一组，找出最低的那个
      for (let i = 0; i < localLows.length; i += groupSize) {
        const group = localLows.slice(i, i + groupSize)
        if (group.length === 0) continue
        
        // 找出组内最低的低点
        const lowest = group.reduce((min, curr) => curr.price < min.price ? curr : min)
        
        markers.push({
          time: lowest.time,
          position: 'belowBar',
          color: '#9c27b0',
          shape: 'arrowUp',
          text: '低',
          size: 2,
        })
      }
      
      return markers
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
    
    resetZoom() {
      if (this.chart) {
        this.chart.timeScale().fitContent()
      }
    },
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

.control-panel-wrapper {
  padding: 12px 0;
}

.control-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
}

.control-item {
  flex: 0 1 auto;
  min-width: 160px;
}

.control-item:first-child {
  flex: 1;
  min-width: 240px;
}

.control-item.action-item {
  flex: 0 0 auto;
  min-width: auto;
}

.symbol-input {
  width: 100%;
}

.form-select {
  min-width: 140px;
  width: 100%;
}

.button-group {
  display: flex;
  gap: 6px;
}

.action-btn {
  background: transparent !important;
  border: 1px solid #e2e8f0 !important;
  color: #64748b !important;
  transition: all 0.2s ease;
  padding: 6px 12px;
}

.action-btn:hover {
  background: #f1f5f9 !important;
  border-color: #cbd5e1 !important;
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

.price-up {
  color: #ef4136 !important;
  font-weight: 700;
}

.price-down {
  color: #4caf50 !important;
  font-weight: 700;
}

.price-neutral {
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
