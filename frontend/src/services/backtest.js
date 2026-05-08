import api from './api.js'

export const backtestService = {
  async runDirect(params) {
    const response = await api.post('/backtest/run-direct', null, { params })
    return response.data
  },

  async getResults(backtestId) {
    const response = await api.get(`/backtest/results/${backtestId}`)
    return response.data
  },

  async getStrategies() {
    const response = await api.get('/backtest/strategies')
    return response.data
  }
}
