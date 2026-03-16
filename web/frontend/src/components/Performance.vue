<template>
  <div class="performance">
    <el-card class="card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <div class="header-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <span class="title">性能分析</span>
          </div>
          <el-select v-model="symbol" placeholder="选择交易对" class="light-select">
            <el-option v-for="item in symbols" :key="item" :label="item" :value="item" />
          </el-select>
        </div>
      </template>

      <!-- 性能指标 -->
      <div class="performance-metrics">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="metric-card">
              <div class="metric-icon positive">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-label">总收益率</div>
                <div class="metric-value positive">+{{ performanceMetrics.totalReturn.toFixed(2) }}%</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="metric-card">
              <div class="metric-icon negative">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-label">最大回撤</div>
                <div class="metric-value negative">-{{ performanceMetrics.maxDrawdown.toFixed(2) }}%</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="metric-card">
              <div class="metric-icon neutral">
                <el-icon><PieChart /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-label">夏普比率</div>
                <div class="metric-value">{{ performanceMetrics.sharpeRatio.toFixed(2) }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="metric-card">
              <div class="metric-icon highlight">
                <el-icon><List /></el-icon>
              </div>
              <div class="metric-content">
                <div class="metric-label">交易次数</div>
                <div class="metric-value highlight">{{ performanceMetrics.tradeCount }}</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 净值曲线 -->
      <div class="equity-curve">
        <h3 class="section-title">
          <el-icon><TrendCharts /></el-icon>
          净值曲线
        </h3>
        <el-card class="chart-card">
          <div ref="equityChartRef" style="height: 400px;"></div>
        </el-card>
      </div>

      <!-- 月度收益 -->
      <div class="monthly-returns">
        <h3 class="section-title">
          <el-icon><Calendar /></el-icon>
          月度收益
        </h3>
        <el-card class="chart-card">
          <div ref="monthlyChartRef" style="height: 300px;"></div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'Performance',
  data() {
    return {
      symbol: '159633',
      symbols: ['159633', '510300', '510500'],
      performanceMetrics: {
        totalReturn: 25.4,
        maxDrawdown: 12.3,
        sharpeRatio: 1.8,
        tradeCount: 120
      },
      equityData: [
        { date: '2024-01', value: 100 },
        { date: '2024-02', value: 105 },
        { date: '2024-03', value: 108 },
        { date: '2024-04', value: 103 },
        { date: '2024-05', value: 110 },
        { date: '2024-06', value: 115 },
        { date: '2024-07', value: 120 },
        { date: '2024-08', value: 125.4 }
      ],
      monthlyData: [
        { month: '2024-01', return: 2.5 },
        { month: '2024-02', return: 5.0 },
        { month: '2024-03', return: 2.9 },
        { month: '2024-04', return: -4.6 },
        { month: '2024-05', return: 6.8 },
        { month: '2024-06', return: 4.5 },
        { month: '2024-07', return: 4.3 },
        { month: '2024-08', return: 4.5 }
      ],
      equityChart: null,
      monthlyChart: null,
      equityChartRef: null,
      monthlyChartRef: null
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.equityChartRef = this.$refs.equityChartRef
      this.monthlyChartRef = this.$refs.monthlyChartRef
      this.initCharts()
    })
  },
  beforeUnmount() {
    if (this.equityChart) {
      this.equityChart.dispose()
    }
    if (this.monthlyChart) {
      this.monthlyChart.dispose()
    }
  },
  methods: {
    initCharts() {
      if (this.equityChartRef) {
        this.equityChart = echarts.init(this.equityChartRef)
        this.equityChart.setOption({
          backgroundColor: '#fff',
          tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            borderColor: '#e2e8f0',
            textStyle: { color: '#1e293b' }
          },
          grid: { left: '8%', right: '5%', top: '15%', bottom: '10%' },
          xAxis: {
            type: 'category',
            data: this.equityData.map(item => item.date),
            axisLine: { lineStyle: { color: '#e2e8f0' } },
            axisLabel: { color: '#64748b' }
          },
          yAxis: {
            type: 'value',
            axisLine: { lineStyle: { color: '#e2e8f0' } },
            axisLabel: { color: '#64748b' },
            splitLine: { lineStyle: { color: '#f1f5f9' } }
          },
          series: [{
            data: this.equityData.map(item => item.value),
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 10,
            lineStyle: { color: '#4f46e5', width: 3 },
            itemStyle: { color: '#4f46e5' },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(79, 70, 229, 0.3)' },
                  { offset: 1, color: 'rgba(79, 70, 229, 0.02)' }
                ]
              }
            }
          }]
        })
        window.addEventListener('resize', () => this.equityChart?.resize())
      }

      if (this.monthlyChartRef) {
        this.monthlyChart = echarts.init(this.monthlyChartRef)
        this.monthlyChart.setOption({
          backgroundColor: '#fff',
          tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            borderColor: '#e2e8f0',
            textStyle: { color: '#1e293b' },
            formatter: params => `${params[0].name}<br/>收益: <span style="color: ${params[0].value >= 0 ? '#4caf50' : '#ef4136'}; font-weight: 600;">${params[0].value}%</span>`
          },
          grid: { left: '8%', right: '5%', top: '15%', bottom: '10%' },
          xAxis: {
            type: 'category',
            data: this.monthlyData.map(item => item.month),
            axisLine: { lineStyle: { color: '#e2e8f0' } },
            axisLabel: { color: '#64748b' }
          },
          yAxis: {
            type: 'value',
            axisLine: { lineStyle: { color: '#e2e8f0' } },
            axisLabel: { color: '#64748b', formatter: '{value}%' },
            splitLine: { lineStyle: { color: '#f1f5f9' } }
          },
          series: [{
            data: this.monthlyData.map(item => ({
              value: item.return,
              itemStyle: { color: item.return >= 0 ? '#4caf50' : '#ef4136' }
            })),
            type: 'bar',
            barWidth: '50%',
            itemStyle: { borderRadius: [6, 6, 0, 0] }
          }]
        })
        window.addEventListener('resize', () => this.monthlyChart?.resize())
      }
    }
  }
}
</script>

<style scoped>
.performance {
  padding: 0;
}

.card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border-radius: 10px;
  color: #fff;
  font-size: 18px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.performance-metrics {
  margin-bottom: 30px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.metric-card:hover {
  border-color: #4f46e5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
}

.metric-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 24px;
}

.metric-icon.positive {
  background: #e8f5e9;
  color: #4caf50;
}

.metric-icon.negative {
  background: #ffebee;
  color: #ef4136;
}

.metric-icon.neutral {
  background: #e0e7ff;
  color: #4f46e5;
}

.metric-icon.highlight {
  background: #f3e8ff;
  color: #8b5cf6;
}

.metric-content {
  flex: 1;
}

.metric-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 26px;
  font-weight: 700;
  color: #1e293b;
}

.metric-value.positive {
  color: #4caf50;
}

.metric-value.negative {
  color: #ef4136;
}

.metric-value.highlight {
  color: #8b5cf6;
}

.equity-curve,
.monthly-returns {
  margin-bottom: 30px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  color: #1e293b;
  font-size: 16px;
  font-weight: 600;
}

.chart-card {
  background: #fafbfc !important;
}

.light-select {
  width: 150px;
}
</style>
