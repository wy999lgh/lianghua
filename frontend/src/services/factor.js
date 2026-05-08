/**
 * 因子管理服务
 * 提供因子计算、配置和管理相关的API调用
 */

import api from './api'

const factorService = {
  /**
   * 获取因子模板列表
   */
  getTemplates() {
    return api.get('/factors/templates')
  },

  /**
   * 获取处理方法选项
   */
  getMethods() {
    return api.get('/factors/methods')
  },

  /**
   * 计算因子
   * @param {Object} params - 计算参数
   */
  compute(params) {
    return api.post('/factors/compute', params)
  },

  /**
   * 获取因子列表
   */
  list() {
    return api.get('/factors/list')
  },

  /**
   * 获取单个因子配置
   * @param {string} factorName - 因子名称
   */
  get(factorName) {
    return api.get(`/factors/${factorName}`)
  },

  /**
   * 保存因子配置
   * @param {Object} config - 因子配置
   */
  saveConfig(config) {
    return api.post('/factors/config', config)
  },

  /**
   * 更新因子配置
   * @param {string} factorName - 因子名称
   * @param {Object} config - 更新的配置
   */
  updateConfig(factorName, config) {
    return api.put(`/factors/${factorName}`, config)
  },

  /**
   * 删除因子配置
   * @param {string} factorName - 因子名称
   */
  deleteConfig(factorName) {
    return api.delete(`/factors/${factorName}`)
  },

  /**
   * 批量保存因子配置
   * @param {Array} configs - 因子配置列表
   */
  batchSave(configs) {
    return api.post('/factors/batch', configs)
  },

  /**
   * 预览因子数据
   * @param {string} symbol - 标的代码
   * @param {string} factorName - 因子名称
   * @param {number} days - 预览天数
   */
  preview(symbol, factorName, days = 30) {
    return api.get('/factors/preview', {
      params: { symbol, factor_name: factorName, days }
    })
  }
}

export default factorService
