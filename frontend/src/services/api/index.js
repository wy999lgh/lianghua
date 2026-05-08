/**
 * API 服务层统一封装
 * 将散落在各组件中的 $axios 调用集中管理，便于维护和版本升级
 */

import api from '../api.js'

/** 系统相关接口 */
export const systemApi = {
  /** 健康检查 */
  health() {
    return api.get('/api/health')
  },
  /** 用户登录 */
  login(username, password) {
    return api.post('/api/login', { username, password })
  }
}

/** 数据管理接口 */
export const dataApi = {
  /** 获取行情数据 */
  fetchData(payload) {
    return api.post('/api/fetch', payload)
  },
  /** 获取可用标的列表 */
  getSymbols(params) {
    return api.get('/data/symbols', { params })
  },
  /** 获取标的详细信息列表 */
  getSymbolList(params) {
    return api.get('/data/symbols/list', { params })
  },
  /** 同步标的列表 */
  syncSymbols(params) {
    return api.post('/data/symbols/sync', params)
  }
}

/** 行情数据接口 */
export const stockDataApi = {
  /** 获取历史K线数据 */
  getKLine(params) {
    return api.get('/stock-data', { params })
  },
  /** 获取股票统计信息 */
  getStats(symbol, params) {
    return api.get(`/stock-data/stats/${symbol}`, { params })
  },
  /** 获取EMA指标数据 */
  getEMA(params) {
    return api.get('/ema-data', { params })
  }
}

/** 策略配置接口 */
export const strategyApi = {
  /** 保存策略配置 */
  saveConfig(payload) {
    return api.post('/strategies/config', payload)
  },
  /** 获取所有策略配置 */
  getConfigs(params) {
    return api.get('/strategies/configs', { params })
  },
  /** 删除策略配置 */
  deleteConfig(configId) {
    return api.delete(`/strategies/config/${configId}`)
  }
}

/** 回测接口 */
export const backtestApi = {
  /** 执行回测 */
  run(payload) {
    return api.post('/backtest/run', payload)
  },
  /** 获取回测结果 */
  getResult(backtestId) {
    return api.get(`/backtest/results/${backtestId}`)
  },
  /** 获取回测历史列表 */
  getHistory(params) {
    return api.get('/backtest/history', { params })
  }
}
