<template>
  <div class="backtest-history">
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">回测历史</h1>
          <p class="page-subtitle">查看所有策略回测结果历史记录</p>
        </div>
      </div>
    </div>

    <div class="main-content">
      <el-card class="card history-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">回测记录列表</span>
            <div class="search-bar">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索策略名称或标的"
                prefix-icon="Search"
                class="search-input"
              />
            </div>
          </div>
        </template>

        <div v-if="historyList.length === 0" class="empty-state">
          <div class="empty-icon">
            <el-icon><Document /></el-icon>
          </div>
          <p>暂无回测历史记录</p>
        </div>

        <el-table v-else :data="filteredHistory" stripe class="history-table">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="strategy_name" label="策略名称" min-width="180">
            <template #default="scope">
              <span class="strategy-name">{{ scope.row.strategy_name || '未命名策略' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="strategy_type" label="策略类型" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.strategy_type === 'grid' ? 'primary' : 'success'">
                {{ scope.row.strategy_type === 'grid' ? '网格交易' : '均线牛熊' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="symbol" label="标的" width="120" />
          <el-table-column prop="total_return" label="总收益(%)" width="120">
            <template #default="scope">
              <span :class="{'positive': scope.row.total_return >= 0, 'negative': scope.row.total_return < 0}">
                {{ (scope.row.total_return || 0).toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="annual_return" label="年化(%)" width="120">
            <template #default="scope">
              <span :class="{'positive': scope.row.annual_return >= 0, 'negative': scope.row.annual_return < 0}">
                {{ (scope.row.annual_return || 0).toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="max_drawdown" label="最大回撤(%)" width="140">
            <template #default="scope">
              <span class="negative">
                {{ (Math.abs(scope.row.max_drawdown) || 0).toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="sharpe_ratio" label="夏普比率" width="120">
            <template #default="scope">
              {{ (scope.row.sharpe_ratio || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="trade_count" label="交易次数" width="100" />
          <el-table-column prop="created_at" label="回测时间" width="180">
            <template #default="scope">{{ formatDateTime(scope.row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="scope">
              <el-button
                size="small"
                type="primary"
                @click="viewDetail(scope.row)"
                class="action-btn"
              >
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteConfirm(scope.row)"
                class="action-btn"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-drawer
        v-model="showDetail"
        :title="'回测详情 - ' + (selectedHistory?.strategy_name || '未命名策略')"
        size="70%"
      >
        <div v-if="selectedHistory" class="detail-content">
          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="策略ID">
              <span class="highlight">{{ selectedHistory.id }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="策略名称">
              {{ selectedHistory.strategy_name || '未命名策略' }}
            </el-descriptions-item>
            <el-descriptions-item label="策略类型">
              <el-tag :type="selectedHistory.strategy_type === 'grid' ? 'primary' : 'success'">
                {{ selectedHistory.strategy_type === 'grid' ? '网格交易' : '均线牛熊' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="标的">
              {{ selectedHistory.symbol }}
            </el-descriptions-item>
            <el-descriptions-item label="回测时间">
              {{ formatDateTime(selectedHistory.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="回测区间">
              {{ selectedHistory.start_date || '-' }} 至 {{ selectedHistory.end_date || '-' }}
            </el-descriptions-item>
          </el-descriptions>

          <h3 class="section-title">收益指标</h3>
          <el-row :gutter="20" class="metrics-row">
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-label">总收益率</div>
                <div class="metric-value" :class="{'positive': selectedHistory.total_return >= 0, 'negative': selectedHistory.total_return < 0}">
                  {{ (selectedHistory.total_return || 0).toFixed(2) }}%
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-label">年化收益率</div>
                <div class="metric-value" :class="{'positive': selectedHistory.annual_return >= 0, 'negative': selectedHistory.annual_return < 0}">
                  {{ (selectedHistory.annual_return || 0).toFixed(2) }}%
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-label">夏普比率</div>
                <div class="metric-value">
                  {{ (selectedHistory.sharpe_ratio || 0).toFixed(2) }}
                </div>
              </el-card>
            </el-col>
          </el-row>

          <h3 class="section-title">风险指标</h3>
          <el-row :gutter="20" class="metrics-row">
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-label">最大回撤</div>
                <div class="metric-value negative">
                  {{ (Math.abs(selectedHistory.max_drawdown) || 0).toFixed(2) }}%
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-label">波动率</div>
                <div class="metric-value">
                  {{ (selectedHistory.volatility || 0).toFixed(2) }}%
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-label">索提诺比率</div>
                <div class="metric-value">
                  {{ (selectedHistory.sortino_ratio || 0).toFixed(2) }}
                </div>
              </el-card>
            </el-col>
          </el-row>

          <h3 class="section-title">交易统计</h3>
          <el-row :gutter="20" class="metrics-row">
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-label">交易次数</div>
                <div class="metric-value">
                  {{ selectedHistory.trade_count || 0 }}
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-label">胜率</div>
                <div class="metric-value" :class="{'positive': (selectedHistory.win_rate || 0) >= 50}">
                  {{ (selectedHistory.win_rate || 0).toFixed(2) }}%
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-label">卡尔马比率</div>
                <div class="metric-value">
                  {{ (selectedHistory.calmar_ratio || 0).toFixed(2) }}
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-drawer>
    </div>

    <el-dialog
      v-model="showDeleteConfirm"
      title="确认删除"
      width="400px"
    >
      <p>确定要删除这条回测记录吗？</p>
      <p class="warning-text">此操作无法撤销。</p>
      <template #footer>
        <el-button @click="showDeleteConfirm = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete" :loading="deleting">
          确认删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { DataAnalysis, Document, View, Delete } from '@element-plus/icons-vue'

export default {
  name: 'BacktestHistory',
  components: {
    DataAnalysis,
    Document,
    View,
    Delete
  },
  data() {
    return {
      historyList: [],
      searchKeyword: '',
      showDetail: false,
      selectedHistory: null,
      showDeleteConfirm: false,
      deletingHistory: null,
      deleting: false
    }
  },
  computed: {
    filteredHistory() {
      if (!this.searchKeyword) {
        return this.historyList
      }
      const keyword = this.searchKeyword.toLowerCase()
      return this.historyList.filter(h =>
        (h.strategy_name && h.strategy_name.toLowerCase().includes(keyword)) ||
        (h.symbol && h.symbol.toLowerCase().includes(keyword))
      )
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    async loadHistory() {
      try {
        const response = await this.$axios.get('/backtest/history')
        if (response.data.status === 'success') {
          this.historyList = response.data.data || []
        }
      } catch (error) {
        console.error('加载回测历史失败:', error)
        this.$message.error('加载回测历史失败')
      }
    },
    viewDetail(history) {
      this.selectedHistory = history
      this.showDetail = true
    },
    deleteConfirm(history) {
      this.deletingHistory = history
      this.showDeleteConfirm = true
    },
    async confirmDelete() {
      if (!this.deletingHistory) return
      
      this.deleting = true
      try {
        const response = await this.$axios.delete(`/backtest/history/${this.deletingHistory.id}`)
        if (response.data.status === 'success') {
          this.$message.success('删除成功')
          await this.loadHistory()
        }
        this.showDeleteConfirm = false
      } catch (error) {
        console.error('删除失败:', error)
        this.$message.error(error.response?.data?.detail || '删除失败')
      } finally {
        this.deleting = false
        this.deletingHistory = null
      }
    },
    formatDateTime(dt) {
      if (!dt) return '-'
      const date = new Date(dt)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.backtest-history {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: linear-gradient(135deg, #fff 0%, #f8fafc 100%);
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #10b981 0%, #0ea5e9 100%);
  border-radius: 12px;
  color: #fff;
  font-size: 24px;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 4px 0 0 0;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  width: 240px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.empty-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  border-radius: 50%;
  margin-bottom: 16px;
  font-size: 32px;
}

.empty-state p {
  margin-bottom: 16px;
}

.history-table {
  margin-top: 16px;
}

.strategy-name {
  font-weight: 600;
  color: #1e293b;
}

.action-btn {
  margin-right: 8px;
}

.positive {
  color: #10b981;
  font-weight: 600;
}

.negative {
  color: #ef4444;
  font-weight: 600;
}

.detail-content {
  padding: 16px;
}

.detail-descriptions {
  margin-bottom: 32px;
}

.highlight {
  color: #4f46e5;
  font-weight: 600;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 24px 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.metrics-row {
  margin-bottom: 16px;
}

.metric-card {
  text-align: center;
  border: 1px solid #e2e8f0;
}

.metric-label {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
}

.warning-text {
  color: #f59e0b;
  font-size: 14px;
  margin-top: 8px;
}
</style>
