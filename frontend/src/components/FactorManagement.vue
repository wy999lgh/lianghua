<template>
  <div class="factor-management-container">
    <header class="factor-header">
      <div class="factor-header-left">
        <span class="factor-title">因子管理</span>
      </div>
      <div class="factor-header-right">
        <el-button type="primary" @click="handleCompute" :loading="computing">
          <el-icon><Cpu /></el-icon>
          <span>计算因子</span>
        </el-button>
        <el-button @click="showAddModal = true">
          <el-icon><Plus /></el-icon>
          <span>新增因子</span>
        </el-button>
      </div>
    </header>

    <div class="factor-status-bar">
      <div class="factor-status-row">
        <div class="factor-status-item">
          <span class="factor-status-label">标的:</span>
          <SymbolSelector v-model="form.symbol" :type-filter="['stock', 'etf', 'index']" :remote="true" placeholder="选择标的" class="factor-status-selector"></SymbolSelector>
        </div>
        <div class="factor-status-divider"></div>
        <div class="factor-status-item">
          <span class="factor-status-label">开始:</span>
          <el-date-picker v-model="form.start_date" type="date" placeholder="开始日期" class="factor-status-date" value-format="YYYY-MM-DD"></el-date-picker>
        </div>
        <div class="factor-status-divider"></div>
        <div class="factor-status-item">
          <span class="factor-status-label">结束:</span>
          <el-date-picker v-model="form.end_date" type="date" placeholder="结束日期" class="factor-status-date" value-format="YYYY-MM-DD"></el-date-picker>
        </div>
      </div>
      <div class="factor-status-row">
        <div class="factor-status-item">
          <span class="factor-status-label">缺失值:</span>
          <el-select v-model="form.missing_method" class="factor-status-select" style="width: 120px;">
            <el-option value="ffill" label="前向填充"></el-option>
            <el-option value="mean" label="均值填充"></el-option>
            <el-option value="median" label="中位数填充"></el-option>
          </el-select>
        </div>
        <div class="factor-status-divider"></div>
        <div class="factor-status-item">
          <span class="factor-status-label">去极值:</span>
          <el-select v-model="form.outlier_method" class="factor-status-select" style="width: 120px;">
            <el-option value="mad" label="MAD法"></el-option>
            <el-option value="iqr" label="IQR法"></el-option>
            <el-option value="percentile" label="百分位法"></el-option>
          </el-select>
        </div>
        <div class="factor-status-divider"></div>
        <div class="factor-status-item">
          <span class="factor-status-label">标准化:</span>
          <el-select v-model="form.normalize_method" class="factor-status-select" style="width: 120px;">
            <el-option value="zscore" label="Z-score"></el-option>
            <el-option value="minmax" label="Min-Max"></el-option>
            <el-option value="rank" label="排名"></el-option>
          </el-select>
        </div>
      </div>
    </div>

    <div class="factor-main-content">
      <aside class="factor-sidebar">
        <div class="factor-sidebar-header">
          <span>因子库</span>
          <el-button size="small" @click="syncFactorConfigs">
            <el-icon><RefreshRight /></el-icon>
          </el-button>
        </div>
        <nav class="factor-nav">
          <div v-for="cat in factorCategories" :key="cat.name" class="factor-nav-category">
            <div class="factor-nav-category-title" @click="cat.expanded = !cat.expanded">
              <el-icon><component :is="cat.expanded ? 'ArrowDown' : 'ArrowRight'"></component></el-icon>
              <span>{{ cat.name }}</span>
              <span class="factor-nav-count">{{ cat.factors.length }}</span>
            </div>
            <div v-show="cat.expanded" class="factor-nav-items">
              <div v-for="factor in cat.factors" :key="factor.name" :class="['factor-nav-item', { 'factor-nav-active': selectedFactors.includes(factor.name) }]" @click="toggleFactor(factor.name)">
                <el-checkbox v-model="factor.selected" @change="handleFactorToggle(factor.name)"></el-checkbox>
                <span class="factor-nav-item-name">{{ factor.display_name }}</span>
                <el-button size="mini" icon="Edit" @click.stop="editFactor(factor)"></el-button>
                <el-button size="mini" icon="Delete" @click.stop="deleteFactorConfirm(factor.name)"></el-button>
              </div>
            </div>
          </div>
        </nav>
      </aside>

      <main class="factor-content">
        <div class="factor-panel">
          <div class="factor-panel-header">
            <h2>已选因子 ({{ selectedFactors.length }})</h2>
            <div class="factor-panel-actions">
              <el-button size="small" @click="selectAll">全选</el-button>
              <el-button size="small" @click="clearAll">清空</el-button>
              <el-button size="small" type="success" @click="batchSaveConfig">批量保存</el-button>
            </div>
          </div>
          <div v-if="selectedFactors.length === 0" class="factor-empty">
            <el-empty description="请从左侧选择要计算的因子" />
          </div>
          <div v-else class="factor-selected-grid">
            <el-tag v-for="factor in selectedFactors" :key="factor" closable @close="removeFactor(factor)" class="factor-tag">
              {{ getFactorDisplayName(factor) }}
            </el-tag>
          </div>
        </div>

        <div v-if="computeResult" class="factor-result-panel">
          <div class="factor-panel-header">
            <h2>计算结果</h2>
            <div class="factor-panel-actions">
              <el-button size="small" type="primary" @click="exportData">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
            </div>
          </div>
          <el-tabs v-model="activeResultTab" type="border-card">
            <el-tab-pane label="统计信息" name="stats">
              <div class="factor-stats-grid">
                <div v-for="(stats, factorName) in computeResult.factors" :key="factorName" class="factor-stats-card">
                  <h3>{{ getFactorDisplayName(factorName) }}</h3>
                  <div class="factor-stats-items">
                    <div class="factor-stats-item">
                      <span class="factor-stats-label">均值</span>
                      <span class="factor-stats-value">{{ stats.stats.mean.toFixed(4) }}</span>
                    </div>
                    <div class="factor-stats-item">
                      <span class="factor-stats-label">标准差</span>
                      <span class="factor-stats-value">{{ stats.stats.std.toFixed(4) }}</span>
                    </div>
                    <div class="factor-stats-item">
                      <span class="factor-stats-label">最小值</span>
                      <span class="factor-stats-value">{{ stats.stats.min.toFixed(4) }}</span>
                    </div>
                    <div class="factor-stats-item">
                      <span class="factor-stats-label">最大值</span>
                      <span class="factor-stats-value">{{ stats.stats.max.toFixed(4) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="数据预览" name="preview">
              <el-table :data="previewData" height="400" stripe>
                <el-table-column prop="date" label="日期" width="120"></el-table-column>
                <el-table-column v-for="factor in selectedFactors" :key="factor" :prop="factor" :label="getFactorDisplayName(factor)" width="120">
                  <template #default="{ row }">
                    {{ row[factor] !== null ? Number(row[factor]).toFixed(4) : '-' }}
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="相关性矩阵" name="correlation">
              <div class="factor-correlation-matrix">
                <table class="correlation-table">
                  <thead>
                    <tr>
                      <th></th>
                      <th v-for="factor in selectedFactors" :key="factor">{{ getFactorDisplayName(factor) }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="rowFactor in selectedFactors" :key="rowFactor">
                      <td>{{ getFactorDisplayName(rowFactor) }}</td>
                      <td v-for="colFactor in selectedFactors" :key="colFactor">
                        <span :class="['correlation-value', getCorrelationClass(getCorrelation(rowFactor, colFactor))]">
                          {{ getCorrelation(rowFactor, colFactor).toFixed(2) }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </main>
    </div>

    <el-dialog :title="isEditMode ? '编辑因子' : '新增因子'" :visible.sync="showAddModal" width="500px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="因子名称" prop="factor_name">
          <el-input v-model="formData.factor_name" :disabled="isEditMode" placeholder="请输入因子名称"></el-input>
        </el-form-item>
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="formData.display_name" placeholder="请输入显示名称"></el-input>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input type="textarea" v-model="formData.description" placeholder="请输入因子描述"></el-input>
        </el-form-item>
        <el-form-item label="类别" prop="category">
          <el-select v-model="formData.category">
            <el-option value="趋势" label="趋势"></el-option>
            <el-option value="动量" label="动量"></el-option>
            <el-option value="波动" label="波动"></el-option>
            <el-option value="风险" label="风险"></el-option>
            <el-option value="统计" label="统计"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="缺失值处理">
          <el-select v-model="formData.missing_method">
            <el-option value="ffill" label="前向填充"></el-option>
            <el-option value="mean" label="均值填充"></el-option>
            <el-option value="median" label="中位数填充"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="去极值方法">
          <el-select v-model="formData.outlier_method">
            <el-option value="mad" label="MAD法"></el-option>
            <el-option value="iqr" label="IQR法"></el-option>
            <el-option value="percentile" label="百分位法"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="标准化方法">
          <el-select v-model="formData.normalize_method">
            <el-option value="zscore" label="Z-score"></el-option>
            <el-option value="minmax" label="Min-Max"></el-option>
            <el-option value="rank" label="排名"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="formData.enabled"></el-switch>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="showAddModal = false">取消</el-button>
        <el-button type="primary" @click="saveFactorConfig" :loading="saving">{{ isEditMode ? '更新' : '保存' }}</el-button>
      </div>
    </el-dialog>

    <el-dialog title="确认删除" :visible.sync="showDeleteModal">
      <p>确定要删除因子「{{ deletingFactorName }}」吗？</p>
      <div slot="footer" class="dialog-footer">
        <el-button @click="showDeleteModal = false">取消</el-button>
        <el-button type="danger" @click="deleteFactor" :loading="deleting">删除</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, Download, ArrowDown, ArrowRight, Plus, RefreshRight, Edit, Delete } from '@element-plus/icons-vue'
import SymbolSelector from './SymbolSelector.vue'
import factorService from '../services/factor'

export default {
  name: 'FactorManagement',
  components: {
    Cpu,
    Download,
    ArrowDown,
    ArrowRight,
    Plus,
    RefreshRight,
    Edit,
    Delete,
    SymbolSelector
  },
  setup() {
    const form = reactive({
      symbol: '',
      start_date: '',
      end_date: '',
      missing_method: 'ffill',
      outlier_method: 'mad',
      normalize_method: 'zscore'
    })

    const formData = reactive({
      factor_name: '',
      display_name: '',
      description: '',
      category: '趋势',
      missing_method: 'ffill',
      outlier_method: 'mad',
      normalize_method: 'zscore',
      params: {},
      enabled: true
    })

    const computing = ref(false)
    const saving = ref(false)
    const deleting = ref(false)
    const computeResult = ref(null)
    const activeResultTab = ref('stats')
    const previewData = ref([])
    const showAddModal = ref(false)
    const showDeleteModal = ref(false)
    const isEditMode = ref(false)
    const deletingFactorName = ref('')

    const factorCategories = ref([
      {
        name: '趋势类',
        expanded: true,
        factors: [
          { name: 'ma5', display_name: '5日均线', selected: false },
          { name: 'ma10', display_name: '10日均线', selected: false },
          { name: 'ma20', display_name: '20日均线', selected: false },
          { name: 'ma60', display_name: '60日均线', selected: false },
          { name: 'ema12', display_name: '12日指数均线', selected: false },
          { name: 'ema26', display_name: '26日指数均线', selected: false },
          { name: 'rolling_slope', display_name: '滚动斜率', selected: false }
        ]
      },
      {
        name: '动量类',
        expanded: true,
        factors: [
          { name: 'macd', display_name: 'MACD', selected: false },
          { name: 'rsi', display_name: 'RSI', selected: false },
          { name: 'cmo', display_name: 'CMO动量', selected: false },
          { name: 'residual_momentum', display_name: '残差动量', selected: false }
        ]
      },
      {
        name: '波动类',
        expanded: false,
        factors: [
          { name: 'bollinger', display_name: '布林带', selected: false },
          { name: 'atr', display_name: 'ATR', selected: false }
        ]
      },
      {
        name: '风险类',
        expanded: false,
        factors: [
          { name: 'rolling_beta', display_name: '滚动Beta', selected: false },
          { name: 'rolling_zscore', display_name: '滚动ZScore', selected: false }
        ]
      },
      {
        name: '统计类',
        expanded: false,
        factors: [
          { name: 'rolling_percentile', display_name: '滚动分位排名', selected: false }
        ]
      }
    ])

    const selectedFactors = computed(() => {
      const selected = []
      factorCategories.value.forEach(cat => {
        cat.factors.forEach(factor => {
          if (factor.selected) {
            selected.push(factor.name)
          }
        })
      })
      return selected
    })

    const getFactorDisplayName = (name) => {
      for (const cat of factorCategories.value) {
        const factor = cat.factors.find(f => f.name === name)
        if (factor) return factor.display_name
      }
      return name
    }

    const toggleFactor = (name) => {
      const cat = factorCategories.value.find(c => c.factors.some(f => f.name === name))
      if (cat) {
        const factor = cat.factors.find(f => f.name === name)
        if (factor) {
          factor.selected = !factor.selected
        }
      }
    }

    const handleFactorToggle = (name) => {
      toggleFactor(name)
    }

    const removeFactor = (name) => {
      const cat = factorCategories.value.find(c => c.factors.some(f => f.name === name))
      if (cat) {
        const factor = cat.factors.find(f => f.name === name)
        if (factor) {
          factor.selected = false
        }
      }
    }

    const selectAll = () => {
      factorCategories.value.forEach(cat => {
        cat.factors.forEach(factor => {
          factor.selected = true
        })
      })
    }

    const clearAll = () => {
      factorCategories.value.forEach(cat => {
        cat.factors.forEach(factor => {
          factor.selected = false
        })
      })
    }

    const handleCompute = async () => {
      if (!form.symbol) {
        ElMessage.warning('请选择标的')
        return
      }
      if (selectedFactors.value.length === 0) {
        ElMessage.warning('请选择至少一个因子')
        return
      }
      if (!form.start_date || !form.end_date) {
        ElMessage.warning('请选择日期范围')
        return
      }

      computing.value = true
      try {
        const response = await factorService.compute({
          symbol: form.symbol,
          start_date: form.start_date,
          end_date: form.end_date,
          factors: selectedFactors.value,
          params: {
            missing_method: form.missing_method,
            outlier_method: form.outlier_method,
            normalize_method: form.normalize_method
          }
        })

        if (response.code === 200) {
          computeResult.value = response.data
          generatePreviewData()
          ElMessage.success('因子计算完成')
        } else {
          ElMessage.error(response.message || '计算失败')
        }
      } catch (error) {
        ElMessage.error(error.message || '计算失败')
      } finally {
        computing.value = false
      }
    }

    const generatePreviewData = () => {
      if (!computeResult.value) return

      const factors = computeResult.value.factors
      const dates = Object.values(factors)[0]?.dates || []

      previewData.value = dates.map((date, idx) => {
        const row = { date }
        selectedFactors.value.forEach(factorName => {
          if (factors[factorName] && factors[factorName].values[idx] !== undefined) {
            row[factorName] = factors[factorName].values[idx]
          } else {
            row[factorName] = null
          }
        })
        return row
      })
    }

    const getCorrelation = (factor1, factor2) => {
      if (!computeResult.value || !previewData.value.length) return 0

      const col1 = previewData.value.map(r => r[factor1]).filter(v => v !== null && !isNaN(v))
      const col2 = previewData.value.map(r => r[factor2]).filter(v => v !== null && !isNaN(v))

      if (col1.length !== col2.length || col1.length < 2) return 0

      const mean1 = col1.reduce((a, b) => a + b, 0) / col1.length
      const mean2 = col2.reduce((a, b) => a + b, 0) / col2.length

      const cov = col1.reduce((sum, v, i) => sum + (v - mean1) * (col2[i] - mean2), 0)
      const std1 = Math.sqrt(col1.reduce((sum, v) => sum + (v - mean1) ** 2, 0))
      const std2 = Math.sqrt(col2.reduce((sum, v) => sum + (v - mean2) ** 2, 0))

      if (std1 === 0 || std2 === 0) return 0
      return cov / (std1 * std2)
    }

    const getCorrelationClass = (corr) => {
      if (corr > 0.7) return 'correlation-high-pos'
      if (corr < -0.7) return 'correlation-high-neg'
      return 'correlation-low'
    }

    const exportData = () => {
      if (!previewData.value.length) {
        ElMessage.warning('没有数据可导出')
        return
      }

      const headers = ['日期', ...selectedFactors.value.map(getFactorDisplayName)]
      const rows = previewData.value.map(row => [
        row.date,
        ...selectedFactors.value.map(f => row[f] !== null ? Number(row[f]).toFixed(6) : '')
      ])

      const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
      const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `因子数据_${form.symbol}_${form.start_date}_${form.end_date}.csv`
      link.click()
      URL.revokeObjectURL(url)

      ElMessage.success('导出成功')
    }

    const editFactor = (factor) => {
      isEditMode.value = true
      formData.factor_name = factor.name
      formData.display_name = factor.display_name
      formData.description = ''
      formData.category = factorCategories.value.find(c => c.factors.some(f => f.name === factor.name))?.name.replace('类', '') || '趋势'
      formData.missing_method = 'ffill'
      formData.outlier_method = 'mad'
      formData.normalize_method = 'zscore'
      formData.enabled = true
      showAddModal.value = true
    }

    const saveFactorConfig = async () => {
      if (!formData.factor_name) {
        ElMessage.warning('请输入因子名称')
        return
      }
      if (!formData.display_name) {
        ElMessage.warning('请输入显示名称')
        return
      }

      saving.value = true
      try {
        let response
        if (isEditMode.value) {
          response = await factorService.updateConfig(formData.factor_name, {
            display_name: formData.display_name,
            description: formData.description,
            category: formData.category,
            missing_method: formData.missing_method,
            outlier_method: formData.outlier_method,
            normalize_method: formData.normalize_method,
            enabled: formData.enabled
          })
        } else {
          response = await factorService.saveConfig({
            factor_name: formData.factor_name,
            display_name: formData.display_name,
            description: formData.description,
            category: formData.category,
            missing_method: formData.missing_method,
            outlier_method: formData.outlier_method,
            normalize_method: formData.normalize_method,
            params: {},
            enabled: formData.enabled
          })
        }

        if (response.code === 200) {
          ElMessage.success(response.message)
          showAddModal.value = false
          syncFactorConfigs()
        } else {
          ElMessage.error(response.message || '保存失败')
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || error.message || '保存失败')
      } finally {
        saving.value = false
      }
    }

    const deleteFactorConfirm = (factorName) => {
      deletingFactorName.value = getFactorDisplayName(factorName)
      showDeleteModal.value = true
    }

    const deleteFactor = async () => {
      deleting.value = true
      try {
        const response = await factorService.deleteConfig(deletingFactorName.value)
        if (response.code === 200) {
          ElMessage.success('删除成功')
          showDeleteModal.value = false
          syncFactorConfigs()
        } else {
          ElMessage.error('删除失败')
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || error.message || '删除失败')
      } finally {
        deleting.value = false
      }
    }

    const batchSaveConfig = async () => {
      if (selectedFactors.value.length === 0) {
        ElMessage.warning('请选择要保存的因子')
        return
      }

      saving.value = true
      try {
        const configs = selectedFactors.value.map(name => {
          const cat = factorCategories.value.find(c => c.factors.some(f => f.name === name))
          const factor = cat?.factors.find(f => f.name === name)
          return {
            factor_name: name,
            display_name: factor?.display_name || name,
            description: '',
            category: cat?.name.replace('类', '') || '趋势',
            missing_method: 'ffill',
            outlier_method: 'mad',
            normalize_method: 'zscore',
            params: {},
            enabled: true
          }
        })

        const response = await factorService.batchSave(configs)
        if (response.code === 200) {
          ElMessage.success(`${response.data.saved} 个因子保存成功，${response.data.skipped} 个已存在`)
        } else {
          ElMessage.error('批量保存失败')
        }
      } catch (error) {
        ElMessage.error(error.message || '批量保存失败')
      } finally {
        saving.value = false
      }
    }

    const syncFactorConfigs = async () => {
      try {
        const response = await factorService.list()
        if (response.code === 200 && response.data.factors) {
          response.data.factors.forEach(config => {
            for (const cat of factorCategories.value) {
              const factor = cat.factors.find(f => f.name === config.factor_name)
              if (factor) {
                factor.display_name = config.display_name
              }
            }
          })
        }
      } catch (error) {
        console.log('同步因子配置失败:', error)
      }
    }

    onMounted(() => {
      const today = new Date()
      const threeMonthsAgo = new Date()
      threeMonthsAgo.setMonth(today.getMonth() - 3)

      form.end_date = today.toISOString().split('T')[0]
      form.start_date = threeMonthsAgo.toISOString().split('T')[0]
    })

    return {
      form,
      formData,
      computing,
      saving,
      deleting,
      computeResult,
      activeResultTab,
      previewData,
      showAddModal,
      showDeleteModal,
      isEditMode,
      deletingFactorName,
      factorCategories,
      selectedFactors,
      getFactorDisplayName,
      toggleFactor,
      handleFactorToggle,
      removeFactor,
      selectAll,
      clearAll,
      handleCompute,
      getCorrelation,
      getCorrelationClass,
      exportData,
      editFactor,
      saveFactorConfig,
      deleteFactorConfirm,
      deleteFactor,
      batchSaveConfig,
      syncFactorConfigs
    }
  }
}
</script>

<style scoped>
.factor-management-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 70px - 56px);
  background: #f5f7fa;
}

.factor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: #fff;
}

.factor-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.factor-title {
  font-size: 20px;
  font-weight: 600;
}

.factor-header-right {
  display: flex;
  gap: 12px;
}

.factor-header-right .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #fff;
}

.factor-header-right .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.factor-status-bar {
  background: #fff;
  padding: 12px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.factor-status-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.factor-status-row + .factor-status-row {
  margin-top: 8px;
}

.factor-status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.factor-status-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.factor-status-value {
  font-size: 13px;
  color: #334155;
  font-weight: 600;
}

.factor-status-divider {
  width: 1px;
  height: 24px;
  background: #e2e8f0;
}

.factor-status-selector {
  width: 160px;
}

.factor-status-date {
  width: 140px;
}

.factor-status-select {
  width: 120px;
}

.factor-main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.factor-sidebar {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  overflow-y: auto;
}

.factor-sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.factor-nav {
  padding: 8px;
}

.factor-nav-category {
  margin-bottom: 4px;
}

.factor-nav-category-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  transition: all 0.2s;
}

.factor-nav-category-title:hover {
  background: #f1f5f9;
}

.factor-nav-count {
  margin-left: auto;
  background: #e2e8f0;
  color: #64748b;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}

.factor-nav-items {
  padding-left: 24px;
}

.factor-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  font-size: 13px;
  color: #64748b;
  transition: all 0.2s;
}

.factor-nav-item:hover {
  background: #f1f5f9;
}

.factor-nav-active {
  background: #eef2ff;
  color: #4f46e5;
}

.factor-nav-item-name {
  flex: 1;
}

.factor-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.factor-panel {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.factor-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.factor-panel-header h2 {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
  margin: 0;
}

.factor-panel-actions {
  display: flex;
  gap: 8px;
}

.factor-empty {
  padding: 40px;
}

.factor-selected-grid {
  padding: 16px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.factor-tag {
  font-size: 13px;
}

.factor-result-panel {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.factor-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  padding: 20px;
}

.factor-stats-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
}

.factor-stats-card h3 {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.factor-stats-items {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.factor-stats-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.factor-stats-label {
  font-size: 12px;
  color: #64748b;
}

.factor-stats-value {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  font-family: 'Monaco', 'Menlo', monospace;
}

.factor-correlation-matrix {
  padding: 20px;
  overflow-x: auto;
}

.correlation-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.correlation-table th,
.correlation-table td {
  padding: 8px 12px;
  text-align: center;
  border: 1px solid #e2e8f0;
}

.correlation-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
}

.correlation-value {
  font-family: 'Monaco', 'Menlo', monospace;
  font-weight: 600;
}

.correlation-high-pos {
  color: #10b981;
}

.correlation-high-neg {
  color: #ef4444;
}

.correlation-low {
  color: #64748b;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
