<template>
  <div class="strategy-management">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon><Setting /></el-icon>
        </div>
        <div class="header-text">
          <h1 class="page-title">策略管理</h1>
          <p class="page-subtitle">管理量化交易策略配置，支持创建、编辑和删除策略</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateModal = true" class="primary-btn">
          <el-icon><DocumentAdd /></el-icon>
          创建新策略
        </el-button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 策略列表 -->
      <el-card class="card strategy-list-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">策略列表</span>
            <div class="search-bar">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索策略名称或标的"
                prefix-icon="Document"
                class="search-input"
              />
              <el-button size="small" @click="testModal()" style="margin-left: 10px;">测试详情弹窗</el-button>
              <el-button size="small" type="warning" @click="testCreateModal()" style="margin-left: 10px;">测试创建弹窗</el-button>
              <span style="margin-left: 10px; color: #666;">详情弹窗: {{ showDetailModal }}</span>
              <span style="margin-left: 10px; color: #666;">创建弹窗: {{ showCreateModal }}</span>
            </div>
          </div>
        </template>

        <div v-if="strategies.length === 0" class="empty-state">
          <div class="empty-icon">
            <el-icon><Document /></el-icon>
          </div>
          <p>暂无策略配置</p>
          <el-button type="primary" @click="showCreateModal = true">创建第一个策略</el-button>
        </div>

        <el-table v-if="strategies.length > 0" :data="filteredStrategies" stripe class="strategy-table">
          <el-table-column prop="name" label="策略名称" min-width="200">
            <template #default="scope">
              <span class="strategy-name">{{ scope.row.name || '未命名策略' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="策略描述" min-width="250" />
          <el-table-column prop="version" label="版本" width="100" />
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button
                size="small"
                type="primary"
                @click="viewStrategyDetail(scope.row)"
                class="action-btn view-btn"
              >
                <el-icon><Edit /></el-icon>
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="strategies.length > 0"
          layout="total, prev, pager, next"
          :total="strategies.length"
          :page-size="10"
          :current-page="currentPage"
          @current-change="currentPage = $event"
          class="pagination"
        />
      </el-card>

    </div>

    <!-- 策略详情弹窗 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div 
        class="modal-content"
        :style="modalStyle"
        @mousedown="startDrag"
      >
        <div class="modal-header" @mousedown.stop="startDrag">
          <h3>策略详情</h3>
          <button class="modal-close" @click="showDetailModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="resize-handle" @mousedown.stop="startResize"></div>
          <div v-if="selectedStrategy">
            <div style="margin-bottom: 20px;">
              <h4 style="margin-bottom: 10px; color: #4f46e5; font-weight: 600;">策略信息</h4>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div><strong>策略名称:</strong> {{ selectedStrategy.name }}</div>
                <div><strong>版本:</strong> {{ selectedStrategy.version || '1.0.0' }}</div>
                <div style="grid-column: 1 / span 2;"><strong>描述:</strong> {{ selectedStrategy.description }}</div>
              </div>
            </div>

            <div>
              <h4 style="margin-bottom: 10px; color: #4f46e5; font-weight: 600;">策略配置参数</h4>
              <div style="display: flex; justify-content: flex-end; gap: 8px; margin-bottom: 10px;">
                <button
                  v-if="isEditingConfig"
                  style="padding: 5px 15px; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer;"
                  @click="saveConfigChanges()"
                >
                  保存修改
                </button>
                <button
                  v-if="isEditingConfig"
                  style="padding: 5px 15px; background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; border-radius: 4px; cursor: pointer;"
                  @click="cancelConfigEdit()"
                >
                  取消
                </button>
                <button
                  v-if="!isEditingConfig"
                  style="padding: 5px 15px; background: #4f46e5; color: white; border: none; border-radius: 4px; cursor: pointer;"
                  @click="startConfigEdit()"
                >
                  修改参数
                </button>
              </div>
              <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                  <tr style="background-color: #f8fafc;">
                    <th style="padding: 10px; text-align: left; border: 1px solid #e2e8f0; width: 100px;">参数名</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #e2e8f0; width: 140px;">中文名称</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #e2e8f0; width: 120px;">参数值</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #e2e8f0;">说明</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="param in configParams" :key="param.key" style="background-color: #fff;">
                    <td style="padding: 10px; border: 1px solid #e2e8f0;">{{ param.key }}</td>
                    <td style="padding: 10px; border: 1px solid #e2e8f0;">{{ param.name }}</td>
                    <td style="padding: 10px; border: 1px solid #e2e8f0;">
                      <input
                        v-if="isEditingConfig"
                        v-model="editableConfig[param.key]"
                        style="width: 100px; padding: 4px;"
                      />
                      <span v-else>{{ param.value }}</span>
                    </td>
                    <td style="padding: 10px; border: 1px solid #e2e8f0;">{{ param.desc }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div v-else>
            <p>请选择一个策略查看详情</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑策略弹窗 -->
    <el-dialog
      :title="isEditing ? '编辑策略' : '创建新策略'"
      :visible.sync="showCreateModal"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="strategyForm" :rules="formRules" ref="strategyForm" label-width="120px">
        <el-form-item label="策略名称" prop="strategy_name">
          <el-input
            v-model="strategyForm.strategy_name"
            placeholder="请输入策略名称（中文）"
          />
        </el-form-item>

        <el-form-item label="策略类型" prop="strategy_type">
          <el-select
            v-model="strategyForm.strategy_type"
            placeholder="请选择策略类型"
            style="width: 100%"
          >
            <el-option label="网格交易策略" value="grid" />
            <el-option label="均线牛熊策略" value="ma_regime" />
          </el-select>
        </el-form-item>

        <el-form-item label="交易标的" prop="symbol">
          <el-select
            v-model="strategyForm.symbol"
            placeholder="请选择交易标的"
            filterable
            remote
            :remote-method="searchSymbols"
            :loading="symbolLoading"
            style="width: 100%"
          >
            <el-option-group
              v-for="group in groupedSymbols"
              :key="group.type"
              :label="group.label"
            >
              <el-option
                v-for="item in group.items"
                :key="item.code"
                :label="`${item.code} - ${item.name}`"
                :value="item.code"
              />
            </el-option-group>
          </el-select>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="基准价格" prop="base_price">
              <el-input-number
                v-model="strategyForm.base_price"
                :min="0.01"
                :step="0.01"
                placeholder="请输入基准价格"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="上步长(%)" prop="upper_step">
              <el-input-number
                v-model="strategyForm.upper_step"
                :min="0.01"
                :step="0.01"
                placeholder="上涨步长百分比"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="下步长(%)" prop="lower_step">
              <el-input-number
                v-model="strategyForm.lower_step"
                :min="0.01"
                :step="0.01"
                placeholder="下跌步长百分比"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="初始资金">
              <el-input-number
                v-model="strategyForm.initial_cash"
                :min="1000"
                :max="10000000"
                :step="10000"
                placeholder="初始资金"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="上涨格数">
              <el-input-number
                v-model="strategyForm.upper_count"
                :min="1"
                :max="500"
                placeholder="上涨格数"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="下跌格数">
              <el-input-number
                v-model="strategyForm.lower_count"
                :min="1"
                :max="500"
                placeholder="下跌格数"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最大持仓">
              <el-input-number
                v-model="strategyForm.max_position"
                :min="1"
                :step="100"
                placeholder="最大持仓"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最小持仓">
              <el-input-number
                v-model="strategyForm.min_position"
                :min="0"
                :step="100"
                placeholder="最小持仓"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="showCreateModal = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveStrategy"
          :loading="saving"
          class="primary-btn"
        >
          {{ isEditing ? '保存修改' : '创建策略' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 删除确认弹窗 -->
    <el-dialog
      title="确认删除"
      :visible.sync="showDeleteModal"
      width="400px"
    >
      <p>确定要删除策略 <span class="highlight">{{ deletingStrategy?.strategy_name || '未命名策略' }}</span> 吗？</p>
      <p class="warning-text">此操作将同时删除该策略关联的回测结果和交易记录，且无法撤销。</p>
      <template #footer>
        <el-button @click="showDeleteModal = false">取消</el-button>
        <el-button
          type="danger"
          @click="confirmDelete"
          :loading="deleting"
        >
          确认删除
        </el-button>
      </template>
    </el-dialog>

    </div>
</template>

<script>
import {
  Setting, DocumentAdd, Document, List, Edit, RefreshRight, CaretRight, Grid, TrendCharts, Check, Close
} from '@element-plus/icons-vue'

export default {
  name: 'StrategyManagement',
  components: {
    Setting,
    DocumentAdd,
    Document,
    List,
    Edit,
    RefreshRight,
    CaretRight,
    Grid,
    TrendCharts,
    Check,
    Close
  },
  data() {
    return {
      // 策略列表
      strategies: [],
      searchKeyword: '',
      currentPage: 1,
      selectedStrategy: null,

      // 创建/编辑相关
      showCreateModal: false,
      showDeleteModal: false,
      isEditing: false,
      editingId: null,
      saving: false,
      deleting: false,
      deletingStrategy: null,

      // 表单数据
      strategyForm: {
        strategy_name: '',
        strategy_type: 'grid',
        symbol: '',
        base_price: 0,
        upper_step: 1,
        lower_step: 1,
        upper_count: 100,
        lower_count: 100,
        max_position: null,
        min_position: null,
        initial_cash: 1000000,
        buy_quantity: null,
        sell_quantity: null
      },

      // 表单验证规则
      formRules: {
        symbol: [{ required: true, message: '请选择交易标的', trigger: 'change' }],
        base_price: [
          { required: true, message: '请输入基准价格', trigger: 'blur' },
          { type: 'number', min: 0.01, message: '基准价格必须大于0', trigger: 'blur' }
        ],
        upper_step: [
          { required: true, message: '请输入上步长', trigger: 'blur' },
          { type: 'number', min: 0.01, message: '上步长必须大于0', trigger: 'blur' }
        ],
        lower_step: [
          { required: true, message: '请输入下步长', trigger: 'blur' },
          { type: 'number', min: 0.01, message: '下步长必须大于0', trigger: 'blur' }
        ]
      },

      // 标的选择相关
      symbolOptions: [],
      symbolType: '',
      symbolLoading: false,

      // 因子相关
      availableFactors: [],
      selectedFactors: [],

      // 参数修改相关
      showConfigEditModal: false,
      showDetailModal: false,
      editConfigForm: {},
      savingConfig: false,
      isEditingConfig: false,
      editableConfig: {},

      // 弹窗拖动相关
      modalX: 50,
      modalY: 50,
      modalWidth: 70,
      modalHeight: 85,
      isDragging: false,
      isResizing: false,
      dragStartX: 0,
      dragStartY: 0,
      modalStartX: 0,
      modalStartY: 0,
      resizeStartX: 0,
      resizeStartY: 0,
      modalStartWidth: 0,
      modalStartHeight: 0
    }
  },
  computed: {
    modalStyle() {
      return {
        marginLeft: `${this.modalX - 50}%`,
        marginTop: `${this.modalY - 50}%`,
        width: `${this.modalWidth}%`,
        maxHeight: `${this.modalHeight}vh`
      }
    },
    filteredStrategies() {
      if (!this.searchKeyword) {
        return this.strategies
      }
      const keyword = this.searchKeyword.toLowerCase()
      return this.strategies.filter(s =>
        (s.name && s.name.toLowerCase().includes(keyword)) ||
        (s.description && s.description.toLowerCase().includes(keyword))
      )
    },

    groupedSymbols() {
      const typeLabels = {
        'stock': '股票',
        'etf': 'ETF',
        'index': '指数'
      }

      const groups = {}
      this.symbolOptions.forEach(item => {
        const type = item.type || 'stock'
        const label = typeLabels[type] || '其他'
        if (!groups[type]) {
          groups[type] = { type, label, items: [] }
        }
        groups[type].items.push(item)
      })

      return Object.values(groups).sort((a, b) => {
        const order = ['stock', 'etf', 'index']
        return order.indexOf(a.type) - order.indexOf(b.type)
      })
    },

    configParams() {
      if (!this.selectedStrategy || !this.selectedStrategy.config) return []

      const config = this.selectedStrategy.config
      const descriptions = this.selectedStrategy.param_descriptions || {}

      return Object.keys(config).map(key => {
        const desc = descriptions[key] || {}
        return {
          key: key,
          name: desc.name || key,
          value: typeof config[key] === 'object' ? JSON.stringify(config[key]) : config[key],
          desc: desc.desc || ''
        }
      })
    },

    editConfigParams() {
      if (!this.selectedStrategy || !this.selectedStrategy.config) return []

      const config = this.selectedStrategy.config
      const descriptions = this.selectedStrategy.param_descriptions || {}

      return Object.keys(config).map(key => {
        const desc = descriptions[key] || {}
        return {
          key: key,
          name: desc.name || key,
          desc: desc.desc || ''
        }
      })
    }
  },
  mounted() {
    this.loadStrategies()
    this.loadSymbols()
    this.loadFactors()
  },
  methods: {
    // 加载策略列表（从后端策略层获取）
    async loadStrategies() {
      try {
        const response = await this.$axios.get('/strategies/list')
        if (response.data.status === 'success') {
          this.strategies = response.data.strategies
        }
      } catch (error) {
        console.error('加载策略列表失败:', error)
        this.$message.error('加载策略列表失败')
      }
    },

    // 加载标的列表
    async loadSymbols() {
      this.symbolLoading = true
      try {
        const params = this.symbolType ? { type: this.symbolType } : {}
        const response = await this.$axios.get('/data/symbols/list', { params })
        if (response.data.status === 'success') {
          this.symbolOptions = response.data.data
        }
      } catch (error) {
        console.error('加载标的列表失败:', error)
      } finally {
        this.symbolLoading = false
      }
    },

    // 搜索标的
    async searchSymbols(keyword) {
      if (!keyword) {
        await this.loadSymbols()
        return
      }
      this.symbolLoading = true
      try {
        const params = {
          keyword: keyword,
          type: this.symbolType || undefined
        }
        const response = await this.$axios.get('/data/symbols/list', { params })
        if (response.data.status === 'success') {
          this.symbolOptions = response.data.data
        }
      } catch (error) {
        console.error('搜索标的失败:', error)
      } finally {
        this.symbolLoading = false
      }
    },

    // 加载因子列表
    async loadFactors() {
      try {
        const response = await this.$axios.get('/factors/list')
        if (response.data.code === 200) {
          this.availableFactors = response.data.data.factors || []
        }
      } catch (error) {
        console.error('加载因子列表失败:', error)
      }
    },

    // 测试详情弹窗
    testModal() {
      console.log('=== 测试详情弹窗 ===')
      this.showDetailModal = true
      console.log('showDetailModal:', this.showDetailModal)
    },

    // 测试创建弹窗
    testCreateModal() {
      console.log('=== 测试创建弹窗 ===')
      this.showCreateModal = true
      console.log('showCreateModal:', this.showCreateModal)
    },

    // 查看策略详情（打开弹窗）
    viewStrategyDetail(strategy) {
      console.log('=== 点击详情按钮 ===')
      console.log('策略:', strategy)
      console.log('当前 showDetailModal:', this.showDetailModal)
      try {
        this.selectedStrategy = strategy
        this.isEditingConfig = false
        this.showDetailModal = true
        console.log('设置后 showDetailModal:', this.showDetailModal)
      } catch (e) {
        console.error('打开详情弹窗失败:', e)
      }
    },

    // 关闭弹窗
    handleModalClose() {
      this.showDetailModal = false
      this.isEditingConfig = false
      this.editableConfig = {}
    },

    // 开始编辑参数
    startConfigEdit() {
      if (!this.selectedStrategy || !this.selectedStrategy.config) {
        this.$message.warning('没有可修改的参数')
        return
      }

      // 清空旧数据
      Object.keys(this.editableConfig).forEach(key => {
        delete this.editableConfig[key]
      })

      // 复制当前配置到可编辑对象
      const config = this.selectedStrategy.config
      for (const key in config) {
        if (config.hasOwnProperty(key)) {
          const value = config[key]
          this.editableConfig[key] = typeof value === 'object' ? JSON.stringify(value) : String(value)
        }
      }

      this.isEditingConfig = true
      console.log('editableConfig已设置:', this.editableConfig)
    },

    // 取消编辑参数
    cancelConfigEdit() {
      this.isEditingConfig = false
      // 清空editableConfig
      Object.keys(this.editableConfig).forEach(key => {
        delete this.editableConfig[key]
      })
      console.log('编辑模式已取消, editableConfig:', this.editableConfig)
    },

    // 打开修改参数弹窗（保留旧方法兼容）
    openConfigEditModal() {
      this.startConfigEdit()
    },

    // 保存参数修改
    async saveConfigChanges() {
      if (!this.selectedStrategy || !this.editableConfig) return

      this.savingConfig = true
      try {
        const config = {}
        const formData = this.editableConfig
        for (const key in formData) {
          if (formData.hasOwnProperty(key)) {
            let value = formData[key]
            // 尝试解析数字
            if (!isNaN(value) && value !== '') {
              value = parseFloat(value)
            } else if (typeof value === 'string' && value.startsWith('[') && value.endsWith(']')) {
              // 尝试解析数组
              try {
                value = JSON.parse(value)
              } catch (e) {
                // 保持原样
              }
            }
            config[key] = value
          }
        }

        console.log('保存的配置:', config)

        // 调用后端API保存
        const response = await this.$axios.put(
          `/strategies/info/${this.selectedStrategy.name}`,
          { config: config }
        )

        if (response.data.status === 'success') {
          this.$message.success('参数修改成功')
          this.isEditingConfig = false
          this.editableConfig = {}
          // 重新加载策略列表验证更新
          await this.loadStrategies()
          // 重新选择当前策略以更新显示
          if (this.selectedStrategy) {
            const updatedStrategy = this.strategies.find(s => s.name === this.selectedStrategy.name)
            if (updatedStrategy) {
              this.selectedStrategy = updatedStrategy
            }
          }
        }
      } catch (error) {
        console.error('保存参数失败:', error)
        this.$message.error(error.response?.data?.detail || '保存参数失败')
      } finally {
        this.savingConfig = false
      }
    },

    // 显示创建弹窗
    showCreateForm() {
      this.isEditing = false
      this.editingId = null
      this.strategyForm = {
        strategy_name: '',
        strategy_type: 'grid',
        symbol: '',
        base_price: 0,
        upper_step: 1,
        lower_step: 1,
        upper_count: 100,
        lower_count: 100,
        max_position: null,
        min_position: null,
        initial_cash: 1000000,
        buy_quantity: null,
        sell_quantity: null
      }
      this.showCreateModal = true
    },

    // 编辑策略
    editStrategy(strategy) {
      this.isEditing = true
      this.editingId = strategy.id
      this.strategyForm = {
        strategy_name: strategy.strategy_name || '',
        strategy_type: strategy.strategy_type || 'grid',
        symbol: strategy.symbol,
        base_price: strategy.base_price,
        upper_step: strategy.upper_step,
        lower_step: strategy.lower_step,
        upper_count: strategy.upper_count,
        lower_count: strategy.lower_count,
        max_position: strategy.max_position,
        min_position: strategy.min_position,
        initial_cash: strategy.initial_cash || 1000000,
        buy_quantity: strategy.buy_quantity,
        sell_quantity: strategy.sell_quantity
      }
      this.showCreateModal = true
    },

    // 保存策略
    saveStrategy() {
      if (!this.$refs.strategyForm || typeof this.$refs.strategyForm.validate !== 'function') {
        this.executeSave()
        return
      }

      this.$refs.strategyForm.validate((valid) => {
        if (!valid) {
          this.$message.error('请检查表单填写是否正确')
          return
        }
        this.executeSave()
      })
    },

    async executeSave() {
      this.saving = true
      try {
        if (this.isEditing) {
          // 更新策略
          const response = await this.$axios.put(
            `/strategies/config/${this.editingId}`,
            this.strategyForm
          )
          if (response.data.status === 'success') {
            this.$message.success('策略更新成功')
            await this.loadStrategies()
          }
        } else {
          // 创建策略
          const response = await this.$axios.post('/strategies/config', this.strategyForm)
          if (response.data.status === 'success') {
            this.$message.success('策略创建成功')
            await this.loadStrategies()
          }
        }
        this.showCreateModal = false
      } catch (error) {
        console.error('保存策略失败:', error)
        this.$message.error(error.response?.data?.detail || '保存策略失败')
      } finally {
        this.saving = false
      }
    },

    // 删除确认
    deleteStrategyConfirm(strategy) {
      this.deletingStrategy = strategy
      this.showDeleteModal = true
    },

    // 确认删除
    async confirmDelete() {
      this.deleting = true
      try {
        const response = await this.$axios.delete(
          `/strategies/config/${this.deletingStrategy.id}`
        )
        if (response.data.status === 'success') {
          this.$message.success('策略删除成功')
          await this.loadStrategies()
          if (this.selectedStrategy?.id === this.deletingStrategy.id) {
            this.selectedStrategy = null
          }
        }
        this.showDeleteModal = false
      } catch (error) {
        console.error('删除策略失败:', error)
        this.$message.error(error.response?.data?.detail || '删除策略失败')
      } finally {
        this.deleting = false
      }
    },

    // 保存因子关联
    saveFactorAssociation() {
      this.$message.success(`已关联 ${this.selectedFactors.length} 个因子`)
    },

    // 格式化日期时间
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
    },

    // 开始拖动弹窗
    startDrag(e) {
      if (e.target.closest('.modal-header')) {
        this.isDragging = true
        this.dragStartX = e.clientX
        this.dragStartY = e.clientY
        this.modalStartX = this.modalX
        this.modalStartY = this.modalY
        
        document.addEventListener('mousemove', this.onDrag)
        document.addEventListener('mouseup', this.stopDrag)
      }
    },

    // 拖动中
    onDrag(e) {
      if (!this.isDragging) return
      
      const deltaX = ((e.clientX - this.dragStartX) / window.innerWidth) * 100
      const deltaY = ((e.clientY - this.dragStartY) / window.innerHeight) * 100
      
      let newX = this.modalStartX + deltaX
      let newY = this.modalStartY + deltaY
      
      // 限制在可视区域内（允许向右边拖动超出一部分）
      newX = Math.max(10, Math.min(newX, 90))
      newY = Math.max(10, Math.min(newY, 90))
      
      this.modalX = newX
      this.modalY = newY
    },

    // 停止拖动
    stopDrag() {
      this.isDragging = false
      document.removeEventListener('mousemove', this.onDrag)
      document.removeEventListener('mouseup', this.stopDrag)
    },

    // 开始调整大小
    startResize(e) {
      this.isResizing = true
      this.resizeStartX = e.clientX
      this.resizeStartY = e.clientY
      this.modalStartWidth = this.modalWidth
      this.modalStartHeight = this.modalHeight
      
      document.addEventListener('mousemove', this.onResize)
      document.addEventListener('mouseup', this.stopResize)
    },

    // 调整大小中
    onResize(e) {
      if (!this.isResizing) return
      
      const deltaWidth = ((e.clientX - this.resizeStartX) / window.innerWidth) * 100
      const deltaHeight = ((e.clientY - this.resizeStartY) / window.innerHeight) * 100
      
      let newWidth = this.modalStartWidth + deltaWidth
      let newHeight = this.modalStartHeight + deltaHeight
      
      // 限制最小和最大尺寸
      newWidth = Math.max(40, Math.min(newWidth, 90))
      newHeight = Math.max(50, Math.min(newHeight, 95))
      
      this.modalWidth = newWidth
      this.modalHeight = newHeight
    },

    // 停止调整大小
    stopResize() {
      this.isResizing = false
      document.removeEventListener('mousemove', this.onResize)
      document.removeEventListener('mouseup', this.stopResize)
    }
  }
}
</script>

<style scoped>
.strategy-management {
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
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
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

.header-actions {
  display: flex;
  gap: 12px;
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

.main-content {
  display: block;
  width: 100%;
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
}

.search-input {
  width: 200px;
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

.strategy-table {
  margin-top: 16px;
}

.strategy-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
  color: #1e293b;
}

.action-btn {
  margin-right: 8px;
}

.edit-btn {
  background: #f1f5f9 !important;
  border-color: #e2e8f0 !important;
  color: #4f46e5 !important;
}

.edit-btn:hover {
  background: #e2e8f0 !important;
}

.delete-btn {
  background: #fef2f2 !important;
  border-color: #fecaca !important;
  color: #dc2626 !important;
}

.delete-btn:hover {
  background: #fee2e2 !important;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.strategy-detail-card {
  position: sticky;
  top: 24px;
}

.close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 4px 8px;
}

.close-btn:hover {
  background: #f1f5f9;
}

.strategy-descriptions {
  margin-bottom: 24px;
}

.highlight {
  color: #4f46e5;
  font-weight: 600;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.grid-visualization {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.grid-chart-container {
  max-height: 300px;
  overflow-y: auto;
}

.grid-lines {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.grid-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #fff;
  border-radius: 8px;
  border-left: 4px solid #e2e8f0;
}

.grid-line.base-line {
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%);
  border-left-color: #4f46e5;
  font-weight: 600;
}

.grid-line.upper-line {
  border-left-color: #10b981;
}

.grid-line.lower-line {
  border-left-color: #ef4444;
}

.line-price {
  font-weight: 600;
  color: #1e293b;
}

.line-label {
  font-size: 12px;
  color: #64748b;
}

.factor-section {
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.empty-factors {
  color: #94a3b8;
  font-size: 14px;
}

.factor-select {
  width: 100%;
  margin-bottom: 12px;
}

.config-actions {
  display: flex;
  gap: 8px;
}

.save-config-btn {
  background: #10b981 !important;
  border-color: #10b981 !important;
}

.save-config-btn:hover {
  background: #059669 !important;
  border-color: #059669 !important;
}

.cancel-config-btn {
  background: #f1f5f9 !important;
  border-color: #e2e8f0 !important;
  color: #64748b !important;
}

.cancel-config-btn:hover {
  background: #e2e8f0 !important;
}

.config-input {
  width: 100%;
  padding: 4px 8px;
}

.config-value {
  color: #1e293b;
  font-weight: 500;
  font-family: 'Monaco', 'Consolas', monospace;
}

.config-table {
  font-size: 13px;
}

.config-table th {
  background-color: #f8fafc;
  font-weight: 600;
  color: #334155;
}

.config-table td {
  padding: 10px 12px;
  vertical-align: middle;
}

.config-table tr:nth-child(even) {
  background-color: #fafafa;
}

.config-table tr:hover {
  background-color: #f1f5f9;
}

.desc-tooltip {
  max-width: 100%;
  white-space: normal;
  word-break: break-all;
  color: #64748b;
  font-size: 12px;
  cursor: help;
}

.desc-tooltip:hover {
  color: #334155;
  text-decoration: underline;
}

.strategy-detail-modal {
  max-height: 85vh;
  overflow-y: auto;
}

.strategy-detail-modal .el-dialog__body {
  padding: 20px;
  max-height: calc(85vh - 120px);
  overflow-y: auto;
}

.save-factors-btn {
  background: #10b981 !important;
  border-color: #10b981 !important;
}

.warning-text {
  color: #f59e0b;
  font-size: 14px;
  margin-top: 8px;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .strategy-detail-card {
    position: static;
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.modal-content {
  background-color: white;
  width: 70%;
  max-height: 85vh;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body {
  padding: 20px;
  max-height: calc(85vh - 60px);
  overflow-y: auto;
  position: relative;
}

.resize-handle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  cursor: se-resize;
  border-radius: 0 0 12px 0;
}

.resize-handle::after {
  content: '';
  position: absolute;
  right: 4px;
  bottom: 4px;
  width: 8px;
  height: 8px;
  border-right: 2px solid rgba(255, 255, 255, 0.8);
  border-bottom: 2px solid rgba(255, 255, 255, 0.8);
}

.modal-header {
  cursor: move;
}

.modal-content {
  position: fixed;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
}
</style>
