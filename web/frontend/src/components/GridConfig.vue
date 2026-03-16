<template>
  <div class="grid-config">
    <el-card class="card">
      <template #header>
        <div class="card-header">
          <span>网格策略配置</span>
        </div>
      </template>

      <el-form :model="gridConfig" label-width="120px" class="grid-form">
        <el-form-item label="交易对">
          <el-select v-model="gridConfig.symbol" placeholder="请选择交易对">
            <el-option v-for="symbol in symbols" :key="symbol" :label="symbol" :value="symbol" />
          </el-select>
        </el-form-item>

        <el-form-item label="基准价格">
          <el-input-number v-model="gridConfig.base_price" :min="0" :step="0.01" placeholder="请输入基准价格" />
        </el-form-item>

        <el-form-item label="上步长">
          <el-input-number v-model="gridConfig.upper_step" :min="0.01" :step="0.01" placeholder="请输入上步长（百分比）" />
        </el-form-item>

        <el-form-item label="下步长">
          <el-input-number v-model="gridConfig.lower_step" :min="0.01" :step="0.01" placeholder="请输入下步长（百分比）" />
        </el-form-item>

        <el-form-item label="上涨数量">
          <el-input-number v-model="gridConfig.upper_count" :min="1" :max="50" :step="1" placeholder="请输入上涨数量" />
        </el-form-item>

        <el-form-item label="下跌数量">
          <el-input-number v-model="gridConfig.lower_count" :min="1" :max="50" :step="1" placeholder="请输入下跌数量" />
        </el-form-item>

        <el-form-item label="最大持仓">
          <el-input-number v-model="gridConfig.max_position" :min="0" :step="100" placeholder="请输入最大持仓" />
        </el-form-item>

        <el-form-item label="最小持仓">
          <el-input-number v-model="gridConfig.min_position" :min="0" :step="100" placeholder="请输入最小持仓" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="submitConfig">保存配置</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 配置结果 -->
    <el-card v-if="configResult" class="card result-card">
      <template #header>
        <div class="card-header">
          <span>配置结果</span>
        </div>
      </template>
      <el-alert
        :title="configResult.status === 'success' ? '配置成功' : '配置失败'"
        :type="configResult.status === 'success' ? 'success' : 'error'"
        show-icon
      />
      <pre v-if="configResult.config" class="config-json">{{ JSON.stringify(configResult.config, null, 2) }}</pre>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'GridConfig',
  inject: ['gridConfig', 'updateGridConfig'],
  data() {
    return {
      symbols: ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],
      configResult: null
    }
  },
  methods: {
    submitConfig() {
      this.$axios.post('/strategies/config', this.gridConfig)
        .then(response => {
          this.configResult = response.data
          // 更新全局配置状态
          this.updateGridConfig(this.gridConfig)
          this.$message.success('配置保存成功！')
        })
        .catch(error => {
          console.error('配置保存失败:', error)
          this.$message.error('配置保存失败，请重试')
        })
    },
    resetForm() {
      const defaultConfig = {
        symbol: '', // 清空交易对字段
        base_price: 10000,
        upper_step: 1,
        lower_step: 1,
        upper_count: 5,
        lower_count: 5,
        max_position: 10000,
        min_position: 1000
      }
      this.gridConfig = defaultConfig
      this.updateGridConfig(defaultConfig)
      this.configResult = null
    }
  }
}
</script>

<style scoped>
.grid-config {
  padding: 20px;
}

.card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.grid-form {
  margin-top: 20px;
}

.result-card {
  margin-top: 20px;
}

.config-json {
  margin-top: 10px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  white-space: pre-wrap;
}
</style>
