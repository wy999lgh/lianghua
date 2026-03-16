import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGridStore = defineStore('grid', () => {
  // 状态
  const config = ref({
    symbol: 'BTC/USDT',
    basePrice: 10000,
    upperStep: 1,
    lowerStep: 1,
    upperCount: 5,
    lowerCount: 5,
    maxPosition: 10000,
    minPosition: 1000
  })

  const backtestResults = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // 计算属性
  const totalGridLevels = computed(() => {
    return config.value.upperCount + config.value.lowerCount + 1
  })

  const priceRange = computed(() => {
    const upperPrice = config.value.basePrice * (1 + config.value.upperStep * config.value.upperCount / 100)
    const lowerPrice = config.value.basePrice * (1 - config.value.lowerStep * config.value.lowerCount / 100)
    return {
      upper: upperPrice,
      lower: lowerPrice,
      range: upperPrice - lowerPrice
    }
  })

  // 动作
  function updateConfig(newConfig) {
    config.value = { ...config.value, ...newConfig }
    error.value = null
  }

  function setBacktestResults(results) {
    backtestResults.value = results
  }

  function setLoading(status) {
    isLoading.value = status
  }

  function setError(err) {
    error.value = err
  }

  function resetError() {
    error.value = null
  }

  function resetBacktest() {
    backtestResults.value = null
    error.value = null
  }

  return {
    // 状态
    config,
    backtestResults,
    isLoading,
    error,
    
    // 计算属性
    totalGridLevels,
    priceRange,
    
    // 动作
    updateConfig,
    setBacktestResults,
    setLoading,
    setError,
    resetError,
    resetBacktest
  }
})