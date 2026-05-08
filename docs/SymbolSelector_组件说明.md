# SymbolSelector 标的选择组件

> 📅 创建日期：2026-04-26  
> 📌 版本：v1.0.0  
> 📁 位置：`frontend/src/components/SymbolSelector.vue`

---

## 概述

通用标的选择组件，用于从数据库中选择股票、ETF、指数等交易标的。支持搜索、筛选、远程加载等功能。

---

## 功能特性

- ✅ 自动从数据库加载标的列表
- ✅ 支持按类型筛选（股票/ETF/指数）
- ✅ 支持前端过滤搜索（代码、名称模糊匹配）
- ✅ 支持远程搜索（后端API搜索）
- ✅ 支持 v-model 双向绑定
- ✅ 支持自定义占位符、禁用、清空
- ✅ 标的类型标签颜色区分
- ✅ 可复用组件，方便其他组件调用

---

## 安装使用

### 1. 注册组件

在 `main.js` 中全局注册：

```javascript
import SymbolSelector from './components/SymbolSelector.vue'

app.component('SymbolSelector', SymbolSelector)
```

或在单个组件中局部注册：

```javascript
import SymbolSelector from '@/components/SymbolSelector.vue'

export default {
  components: {
    SymbolSelector
  }
}
```

### 2. 基本使用

```vue
<template>
  <SymbolSelector v-model="selectedSymbol" />
</template>

<script>
export default {
  data() {
    return {
      selectedSymbol: ''  // 选中的标的代码
    }
  }
}
</script>
```

---

## Props 属性

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `modelValue` | String | `''` | 选中的标的代码（v-model） |
| `placeholder` | String | `'请选择标的'` | 占位符文本 |
| `disabled` | Boolean | `false` | 是否禁用 |
| `clearable` | Boolean | `true` | 是否可清空 |
| `filterable` | Boolean | `true` | 是否启用前端过滤 |
| `remote` | Boolean | `false` | 是否启用远程搜索 |
| `typeFilter` | Array | `[]` | 类型筛选，如 `['stock', 'etf']` |
| `autoLoad` | Boolean | `true` | 是否自动加载数据 |
| `searchKeyword` | String | `''` | 搜索关键词（远程搜索） |

---

## Events 事件

| 事件名 | 参数 | 说明 |
|--------|------|------|
| `update:modelValue` | `code: String` | 选中值变更（v-model） |
| `change` | `{ code, name, type, table_name }` | 选择变更，返回完整标的信息 |
| `loaded` | `symbols: Array` | 数据加载完成 |

---

## Methods 方法

| 方法名 | 参数 | 说明 |
|--------|------|------|
| `loadSymbols()` | 无 | 加载标的列表 |
| `refresh()` | 无 | 刷新标的列表 |
| `filterByType(type)` | `type: String` | 按类型筛选 |
| `setSymbol(code)` | `code: String` | 设置选中的标的 |
| `getSymbolInfo(code)` | `code: String` | 获取完整标的信息 |

---

## 使用示例

### 示例1: 基本使用

```vue
<template>
  <SymbolSelector v-model="selectedSymbol" />
</template>

<script>
export default {
  data() {
    return {
      selectedSymbol: '159633'
    }
  }
}
</script>
```

### 示例2: 类型筛选

```vue
<template>
  <!-- 只显示股票和ETF -->
  <SymbolSelector 
    v-model="selectedSymbol" 
    :type-filter="['stock', 'etf']" 
  />
</template>
```

### 示例3: 监听选择变更

```vue
<template>
  <SymbolSelector 
    v-model="selectedSymbol" 
    @change="handleSymbolChange" 
  />
</template>

<script>
export default {
  methods: {
    handleSymbolChange(symbolInfo) {
      console.log('选中标的:', symbolInfo)
      // symbolInfo = {
      //   code: '159633',
      //   name: '科创50ETF',
      //   type: 'etf',
      //   table_name: 'etf_daily_159633'
      // }
    }
  }
}
</script>
```

### 示例4: 手动控制加载

```vue
<template>
  <SymbolSelector 
    ref="selector"
    v-model="selectedSymbol" 
    :auto-load="false"
  />
  <el-button @click="loadSymbols">加载数据</el-button>
</template>

<script>
export default {
  methods: {
    loadSymbols() {
      this.$refs.selector.loadSymbols()
    }
  }
}
</script>
```

### 示例5: 与回测组件集成

```vue
<template>
  <el-form-item label="回测标的">
    <SymbolSelector 
      v-model="form.symbol" 
      @change="handleSymbolChange"
    />
  </el-form-item>
</template>

<script>
import SymbolSelector from '@/components/SymbolSelector.vue'

export default {
  components: {
    SymbolSelector
  },
  data() {
    return {
      form: {
        symbol: ''
      }
    }
  },
  methods: {
    handleSymbolChange(symbolInfo) {
      console.log('选择标的:', symbolInfo.code, symbolInfo.name)
      // 可以在这里加载该标的的数据
      this.loadStockData(symbolInfo.code)
    }
  }
}
</script>
```

---

## 后端API

### 获取标的列表

**接口地址：** `GET /api/data/symbols/list`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `type` | String | 否 | 标的类型筛选 (stock/etf/index) |
| `keyword` | String | 否 | 搜索关键词 |

**响应示例：**

```json
{
  "count": 10,
  "data": [
    {
      "code": "000001",
      "name": "平安银行",
      "type": "stock",
      "table_name": "stock_daily_000001"
    },
    {
      "code": "159633",
      "name": "科创50ETF",
      "type": "etf",
      "table_name": "etf_daily_159633"
    }
  ]
}
```

---

## 样式说明

组件使用渐变色区分不同类型的标的：

- **股票**：紫色渐变 `#667eea → #764ba2`
- **ETF**：粉色渐变 `#f093fb → #f5576c`
- **指数**：蓝色渐变 `#4facfe → #00f2fe`

---

## 注意事项

1. 确保后端服务已启动并运行
2. 确保数据库中有标的数据表（如 `stock_daily_*`, `etf_daily_*`）
3. 组件会自动处理加载状态和错误提示
4. 支持键盘搜索和鼠标点选

---

## 更新日志

### v1.0.0 (2026-04-26)
- ✅ 初始版本
- ✅ 支持标的列表加载
- ✅ 支持类型筛选
- ✅ 支持搜索功能
- ✅ 支持 v-model 双向绑定
