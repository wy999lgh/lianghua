<template>
  <div class="data-management">
    <el-card class="card">
      <template #header>
        <div class="card-header">
          <div class="header-icon">
            <el-icon><Download /></el-icon>
          </div>
          <span class="title">数据获取与管理</span>
        </div>
      </template>

      <el-form :model="fetchForm" :rules="rules" ref="fetchForm" label-width="120px" class="fetch-form">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="股票/ETF代码" prop="symbol">
              <el-input v-model="fetchForm.symbol" placeholder="例如: 159633" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker v-model="fetchForm.start_date" type="date" placeholder="选择开始日期" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="结束日期" prop="end_date">
              <el-date-picker v-model="fetchForm.end_date" type="date" placeholder="选择结束日期" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" @click="fetchData" :loading="loading" class="primary-btn">
            <el-icon><Refresh /></el-icon>
            获取并更新数据
          </el-button>
          <el-button @click="resetForm" class="default-btn">
            <el-icon><RefreshRight /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
      
      <el-alert
        v-if="fetchResult"
        :title="fetchResult.message"
        :type="fetchResult.status === 'success' ? 'success' : 'warning'"
        show-icon
        :closable="true"
        class="result-alert"
      />
    </el-card>

    <el-card class="card data-summary-card">
       <template #header>
        <div class="card-header">
          <div class="header-icon blue">
            <el-icon><DataLine /></el-icon>
          </div>
          <span class="title">当前数据概览</span>
        </div>
      </template>
      
      <div v-if="stats.total_records" class="stats-container">
         <el-descriptions :column="2" border>
            <el-descriptions-item label="标的代码">{{ stats.symbol }}</el-descriptions-item>
            <el-descriptions-item label="总记录数">{{ stats.total_records }}</el-descriptions-item>
            <el-descriptions-item label="数据时间范围">
              {{ stats.date_range?.start }} 至 {{ stats.date_range?.end }}
            </el-descriptions-item>
            <el-descriptions-item label="最新收盘价">
               {{ stats.price_range?.close?.max }} (最高) / {{ stats.price_range?.close?.min }} (最低)
            </el-descriptions-item>
         </el-descriptions>
      </div>
      <div v-else class="empty-stats">
        请先获取数据或输入代码查看概览
      </div>
    </el-card>
  </div>
</template>

<script>
import { Download, Refresh, RefreshRight, DataLine } from '@element-plus/icons-vue'

export default {
  name: 'DataManagement',
  components: {
    Download,
    Refresh,
    RefreshRight,
    DataLine
  },
  data() {
    return {
      fetchForm: {
        symbol: '159633',
        start_date: '',
        end_date: ''
      },
      rules: {
        symbol: [{ required: true, message: '请输入代码', trigger: 'blur' }],
        start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
        end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }]
      },
      loading: false,
      fetchResult: null,
      stats: {}
    }
  },
  mounted() {
    // 初始加载统计数据，然后根据统计数据设置日期
    if (this.fetchForm.symbol) {
      this.loadStats()
    }
  },
  methods: {
    fetchData() {
      this.$refs.fetchForm.validate((valid) => {
        if (!valid) return
        
        this.loading = true
        this.fetchResult = null
        
        const formatDate = (date) => {
          if (!date) return ''
          const d = new Date(date)
          return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
        }
        
        const payload = {
          symbol: this.fetchForm.symbol,
          start_date: formatDate(this.fetchForm.start_date),
          end_date: formatDate(this.fetchForm.end_date)
        }
        
        this.$axios.post('/data/fetch', payload)
          .then(response => {
            this.fetchResult = response.data
            if (response.data.status === 'success') {
              this.$message.success(response.data.message)
              // 更新统计数据
              this.loadStats()
            } else {
              this.$message.warning(response.data.message)
            }
          })
          .catch(error => {
            console.error('获取数据失败:', error)
            const msg = error.response?.data?.detail || '请求失败，请检查网络或后端服务'
            this.$message.error(msg)
            this.fetchResult = {
              status: 'error',
              message: msg
            }
          })
          .finally(() => {
            this.loading = false
          })
      })
    },
    
    resetForm() {
      this.$refs.fetchForm.resetFields()
      this.fetchResult = null
      // 重置时也重新加载统计并自动计算日期
      this.loadStats()
    },
    
    loadStats() {
      if (!this.fetchForm.symbol) return
      
      this.$axios.get(`/stock-data/stats/${this.fetchForm.symbol}`)
        .then(response => {
          this.stats = {
            symbol: response.data.symbol,
            ...response.data.statistics
          }
          
          // 自动设置日期范围
          const today = new Date()
          this.fetchForm.end_date = today
          
          if (this.stats.date_range && this.stats.date_range.end) {
            // 如果有现有数据，开始日期设为现有数据最新日期的下一天
            const lastDate = new Date(this.stats.date_range.end)
            const nextDay = new Date(lastDate)
            nextDay.setDate(nextDay.getDate() + 1)
            
            // 如果最新日期就是今天（或未来），则不需要更新，或者可以设为今天以尝试获取盘后数据
            if (nextDay > today) {
               this.fetchForm.start_date = today
            } else {
               this.fetchForm.start_date = nextDay
            }
          } else {
            // 如果没有数据，默认获取最近一年的数据
            const start = new Date()
            start.setFullYear(start.getFullYear() - 1)
            this.fetchForm.start_date = start
          }
        })
        .catch(error => {
          console.warn('获取统计数据失败:', error)
          this.stats = {}
          // 获取失败时也设置默认日期
          const end = new Date()
          const start = new Date()
          start.setFullYear(start.getFullYear() - 1)
          this.fetchForm.start_date = start
          this.fetchForm.end_date = end
        })
    }
  },
  watch: {
    'fetchForm.symbol': function(newVal) {
      if (newVal && newVal.length >= 6) {
        this.loadStats()
      }
    }
  }
}
</script>

<style scoped>
.data-management {
  padding: 0;
}

.card {
  margin-bottom: 20px;
}

.card-header {
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

.header-icon.blue {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.fetch-form {
  margin-top: 20px;
}

.primary-btn {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
  border: none !important;
  color: #fff !important;
  font-weight: 500;
}

.primary-btn:hover {
  background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%) !important;
}

.default-btn {
  background: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  color: #64748b !important;
}

.default-btn:hover {
  background: #f1f5f9 !important;
  border-color: #4f46e5 !important;
  color: #4f46e5 !important;
}

.result-alert {
  margin-top: 20px;
}

.stats-container {
  padding: 10px;
}

.empty-stats {
  padding: 40px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
}
</style>
