<template>
  <div class="symbol-selector">
    <el-select
      v-model="selectedSymbol"
      :filterable="filterable"
      :remote="remote"
      :remote-method="handleSearch"
      :placeholder="placeholder"
      :disabled="disabled"
      :clearable="clearable"
      :loading="loading"
      class="full-width"
      @change="handleChange"
    >
      <el-option
        v-for="item in filteredSymbols"
        :key="item.code"
        :label="formatSymbolLabel(item)"
        :value="item.code"
      >
        <div class="symbol-option">
          <span class="symbol-type" :class="'type-' + item.type">
            {{ getTypeLabel(item.type) }}
          </span>
          <span class="symbol-code">{{ item.code }}</span>
          <span class="symbol-name">{{ item.name }}</span>
        </div>
      </el-option>
    </el-select>
  </div>
</template>

<script>
/**
 * 标的选择组件
 * 
 * 功能说明：
 * - 从数据库加载标的列表（类型、代码、名称）
 * - 支持按类型筛选
 * - 支持搜索功能（代码或名称模糊匹配）
 * - 支持远程搜索（后端API搜索）
 * - 可复用组件，其他组件可直接调用
 * 
 * 使用示例：
 * ```vue
 * <SymbolSelector
 *   v-model="selectedSymbol"
 *   :type-filter="['stock', 'etf']"
 *   :filterable="true"
 *   :remote="true"
 *   @change="handleSymbolChange"
 * />
 * ```
 */
export default {
  name: 'SymbolSelector',
  props: {
    /**
     * 选中的标的代码（v-model）
     */
    modelValue: {
      type: String,
      default: ''
    },
    /**
     * 占位符文本
     */
    placeholder: {
      type: String,
      default: '请选择标的'
    },
    /**
     * 是否禁用
     */
    disabled: {
      type: Boolean,
      default: false
    },
    /**
     * 是否可清空
     */
    clearable: {
      type: Boolean,
      default: true
    },
    /**
     * 是否启用前端过滤
     */
    filterable: {
      type: Boolean,
      default: true
    },
    /**
     * 是否启用远程搜索
     */
    remote: {
      type: Boolean,
      default: false
    },
    /**
     * 类型筛选（如：['stock', 'etf']）
     */
    typeFilter: {
      type: Array,
      default: () => []
    },
    /**
     * 是否自动加载数据
     */
    autoLoad: {
      type: Boolean,
      default: true
    },
    /**
     * 搜索关键词（用于远程搜索）
     */
    searchKeyword: {
      type: String,
      default: ''
    }
  },
  emits: ['update:modelValue', 'change', 'loaded'],
  data() {
    return {
      loading: false,
      symbols: [],  // 完整标的列表
      filteredSymbols: [],  // 过滤后的列表
      searchTimeout: null
    }
  },
  computed: {
    selectedSymbol: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    }
  },
  watch: {
    searchKeyword: {
      handler(newVal) {
        if (this.remote && newVal !== undefined) {
          this.handleSearch(newVal)
        }
      }
    }
  },
  mounted() {
    if (this.autoLoad) {
      this.loadSymbols()
    }
  },
  methods: {
    /**
     * 加载标的列表
     */
    async loadSymbols() {
      if (this.loading) return
      
      this.loading = true
      try {
        const params = { limit: 2000, sync_if_empty: true }
        if (this.typeFilter.length > 0) {
          params.type = this.typeFilter.join(',')
        }
        
        const response = await this.$axios.get('/data/symbols/list', { params })
        
        if (response.data && response.data.data) {
          this.symbols = response.data.data
          this.filteredSymbols = [...this.symbols]
          this.$emit('loaded', this.symbols)
        }
      } catch (error) {
        console.error('加载标的列表失败:', error)
        this.$message.error('加载标的列表失败')
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 搜索处理
     */
    handleSearch(keyword) {
      if (this.remote) {
        this.handleRemoteSearch(keyword)
        return
      }
      if (!keyword || keyword.trim() === '') {
        this.filteredSymbols = [...this.symbols]
        return
      }
      
      const kw = keyword.toLowerCase().trim()
      this.filteredSymbols = this.symbols.filter(item => 
        item.code.toLowerCase().includes(kw) ||
        item.name.toLowerCase().includes(kw) ||
        item.type.toLowerCase().includes(kw)
      )
    },

    async handleRemoteSearch(keyword) {
      const kw = String(keyword || '').trim()
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout)
      }
      this.searchTimeout = setTimeout(async () => {
        this.loading = true
        try {
          const params = { limit: 2000, sync_if_empty: true }
          if (this.typeFilter.length > 0) {
            params.type = this.typeFilter.join(',')
          }
          if (kw) {
            params.keyword = kw
          }
          const response = await this.$axios.get('/data/symbols/list', { params })
          const rows = response.data && response.data.data ? response.data.data : []
          this.symbols = Array.isArray(rows) ? rows : []
          this.filteredSymbols = [...this.symbols]
          this.$emit('loaded', this.symbols)
        } catch (error) {
          console.error('远程搜索标的失败:', error)
          this.filteredSymbols = []
        } finally {
          this.loading = false
        }
      }, 300)
    },
    
    /**
     * 选择变更处理
     */
    handleChange(value) {
      const selected = this.symbols.find(s => s.code === value)
      this.$emit('change', {
        code: value,
        ...selected
      })
    },
    
    /**
     * 格式化标的标签
     */
    formatSymbolLabel(item) {
      return `${item.code} - ${item.name}`
    },
    
    /**
     * 获取类型标签
     */
    getTypeLabel(type) {
      const typeMap = {
        stock: '股票',
        etf: 'ETF',
        index: '指数'
      }
      return typeMap[type] || type
    },
    
    /**
     * 刷新标的列表
     */
    refresh() {
      this.loadSymbols()
    },
    
    /**
     * 按类型筛选
     */
    filterByType(type) {
      if (!type) {
        this.filteredSymbols = [...this.symbols]
        return
      }
      this.filteredSymbols = this.symbols.filter(item => item.type === type)
    },
    
    /**
     * 设置选中的标的
     */
    setSymbol(code) {
      this.selectedSymbol = code
    },
    
    /**
     * 获取完整标的信息
     */
    getSymbolInfo(code) {
      return this.symbols.find(s => s.code === code) || null
    }
  }
}
</script>

<style scoped>
.symbol-selector {
  width: 100%;
}

.full-width {
  width: 100%;
}

.symbol-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 4px;
}

.symbol-type {
  display: inline-block;
  padding: 0px 4px;
  border-radius: 2px;
  font-size: 9px;
  font-weight: 500;
  color: #fff;
  min-width: 26px;
  text-align: center;
  line-height: 14px;
  flex-shrink: 0;
}

.type-stock {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.type-etf {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.type-index {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.symbol-code {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
  flex-shrink: 0;
}

.symbol-name {
  color: #64748b;
  font-size: 12px;
  margin-left: auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
}
</style>
