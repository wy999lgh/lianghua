<template>
  <div class="jq-backtest-container">
    <header class="jq-header">
      <div class="jq-header-left">
        <span class="jq-title">回测系统</span>
      </div>
      <div class="jq-header-right">
        <el-button type="primary" :loading="loading" @click="runBacktest" class="jq-btn-primary">
          <el-icon><PlayCircle /></el-icon>
          <span>策略交易</span>
        </el-button>
      </div>
    </header>
    
    <div class="jq-status-bar">
      <div class="jq-status-row">
        <div class="jq-status-item">
          <span class="jq-status-label">策略:</span>
          <el-select v-model="form.strategy_type" class="jq-status-select" @change="handleStrategyTypeChange">
            <el-option v-for="s in strategyTypes" :key="s.type" :value="s.type">{{ s.name }}</el-option>
          </el-select>
        </div>
        <div class="jq-status-divider"></div>
        <div class="jq-status-item">
          <span class="jq-status-label">标的:</span>
          <SymbolSelector v-model="form.symbol" :type-filter="['stock', 'etf', 'index']" :remote="true" placeholder="选择标的" class="jq-status-selector"></SymbolSelector>
        </div>
        <div class="jq-status-divider"></div>
        <div class="jq-status-item">
          <span class="jq-status-label">开始:</span>
          <el-date-picker v-model="form.start_date" type="date" placeholder="开始日期" class="jq-status-date" value-format="YYYY-MM-DD"></el-date-picker>
        </div>
        <div class="jq-status-divider"></div>
        <div class="jq-status-item">
          <span class="jq-status-label">结束:</span>
          <el-date-picker v-model="form.end_date" type="date" placeholder="结束日期" class="jq-status-date" value-format="YYYY-MM-DD"></el-date-picker>
        </div>
        <div class="jq-status-divider"></div>
        <div class="jq-status-item">
          <span class="jq-status-label">资金:</span>
          <span class="jq-status-value">¥{{ form.initial_cash.toLocaleString() }}</span>
        </div>
      </div>
      <div class="jq-status-row">
        <div class="jq-status-item">
          <span class="jq-status-label">频率:</span>
          <el-select v-model="form.frequency" class="jq-status-select" style="width: 80px;">
            <el-option value="daily" label="每天"></el-option>
            <el-option value="weekly" label="每周"></el-option>
            <el-option value="monthly" label="每月"></el-option>
          </el-select>
        </div>
        <div class="jq-status-divider"></div>
        <div class="jq-status-item">
          <span class="jq-status-label">状态:</span>
          <span :class="['jq-status-value', statusClass]">{{ statusText }}</span>
        </div>
        <div v-if="backtestTime" class="jq-status-divider"></div>
        <div v-if="backtestTime" class="jq-status-item">
          <span class="jq-status-label">耗时:</span>
          <span class="jq-status-value">{{ backtestTime }}</span>
        </div>
      </div>
    </div>

    <div class="jq-main-content">
      <aside class="jq-sidebar">
        <nav class="jq-nav">
          <div
            v-for="item in navItems"
            :key="item.id"
            :class="['jq-nav-item', { 'jq-nav-active': activeTab === item.id }]"
            @click="activeTab = item.id"
          >
            <el-icon><component :is="item.icon"></component></el-icon>
            <span>{{ item.label }}</span>
          </div>
        </nav>
      </aside>

      <main class="jq-content">
        <div v-if="activeTab === 'config'" class="jq-panel">
          <div class="jq-panel-header">
            <h2>回测配置</h2>
          </div>
          <div class="jq-config-form">
            <div class="jq-form-section">
              <div class="jq-form-section-title">策略设置</div>
              <div class="jq-form-grid">
                <div class="jq-form-item">
                  <label>策略类型</label>
                  <el-select v-model="form.strategy_type" class="jq-form-select" @change="handleStrategyTypeChange">
                    <el-option v-for="s in strategyTypes" :key="s.type" :value="s.type">{{ s.name }}</el-option>
                  </el-select>
                </div>
                <div class="jq-form-item">
                  <label>策略名称</label>
                  <el-input v-model="form.strategy_name" placeholder="输入策略名称" class="jq-form-input"></el-input>
                </div>
                <div class="jq-form-item">
                  <label>回测标的</label>
                  <SymbolSelector v-model="form.symbol" :type-filter="['stock', 'etf', 'index']" :remote="true" placeholder="输入代码或名称搜索" class="jq-form-input"></SymbolSelector>
                </div>
              </div>
            </div>

            <div class="jq-form-section">
              <div class="jq-form-section-title">时间范围</div>
              <div class="jq-form-grid">
                <div class="jq-form-item">
                  <label>开始日期</label>
                  <el-date-picker v-model="form.start_date" type="date" placeholder="选择开始日期" class="jq-form-input" value-format="YYYY-MM-DD"></el-date-picker>
                </div>
                <div class="jq-form-item">
                  <label>结束日期</label>
                  <el-date-picker v-model="form.end_date" type="date" placeholder="选择结束日期" class="jq-form-input" value-format="YYYY-MM-DD"></el-date-picker>
                </div>
                <div class="jq-form-item">
                  <label>初始资金</label>
                  <el-input-number v-model="form.initial_cash" :min="1000" :step="10000" :controls="false" class="jq-form-input"></el-input-number>
                </div>
              </div>
            </div>

            <div v-if="form.strategy_type === 'grid'" class="jq-form-section">
              <div class="jq-form-section-title">网格策略参数</div>
              <div class="jq-form-grid">
                <div class="jq-form-item">
                  <label>基准价格</label>
                  <el-input-number v-model="form.base_price" :min="0.01" :step="0.01" :precision="2" :controls="false" class="jq-form-input"></el-input-number>
                </div>
                <div class="jq-form-item">
                  <label>上步长(%)</label>
                  <el-input-number v-model="form.upper_step" :min="0.01" :max="50" :step="0.1" :precision="2" :controls="false" class="jq-form-input"></el-input-number>
                </div>
                <div class="jq-form-item">
                  <label>下步长(%)</label>
                  <el-input-number v-model="form.lower_step" :min="0.01" :max="50" :step="0.1" :precision="2" :controls="false" class="jq-form-input"></el-input-number>
                </div>
                <div class="jq-form-item">
                  <label>上限格数</label>
                  <el-input-number v-model="form.upper_count" :min="1" :max="20" :step="1" :controls="false" class="jq-form-input"></el-input-number>
                </div>
                <div class="jq-form-item">
                  <label>下限格数</label>
                  <el-input-number v-model="form.lower_count" :min="1" :max="20" :step="1" :controls="false" class="jq-form-input"></el-input-number>
                </div>
                <div class="jq-form-item">
                  <label>买入数量</label>
                  <el-input-number v-model="form.buy_quantity" :min="1" :step="10" :controls="false" class="jq-form-input"></el-input-number>
                </div>
                <div class="jq-form-item">
                  <label>卖出数量</label>
                  <el-input-number v-model="form.sell_quantity" :min="1" :step="10" :controls="false" class="jq-form-input"></el-input-number>
                </div>
                <div class="jq-form-item">
                  <label>最大持仓</label>
                  <el-input-number v-model="form.max_position" :min="0" :step="100" :controls="false" class="jq-form-input" placeholder="无限制"></el-input-number>
                </div>
                <div class="jq-form-item">
                  <label>最小持仓</label>
                  <el-input-number v-model="form.min_position" :min="0" :step="100" :controls="false" class="jq-form-input" placeholder="无限制"></el-input-number>
                </div>
                <div class="jq-form-item">
                  <label>佣金率</label>
                  <el-input-number v-model="form.commission_rate" :min="0" :max="0.1" :step="0.0001" :precision="4" :controls="false" class="jq-form-input"></el-input-number>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'overview' && result" class="jq-panel">
          <div class="jq-panel-header">
            <h2>回测结果 - 收益概述</h2>
          </div>

          <div class="jq-metrics-section">
            <div class="jq-metrics-row">
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">策略收益</div>
                <div class="jq-metric-value" :class="getValueClass(result.total_return)">
                  {{ formatPercent(result.total_return) }}
                </div>
              </div>
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">策略年化收益</div>
                <div class="jq-metric-value" :class="getValueClass(result.annual_return)">
                  {{ formatPercent(result.annual_return) }}
                </div>
              </div>
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">超额收益</div>
                <div class="jq-metric-value" :class="getValueClass(result.excess_return)">
                  {{ formatPercent(result.excess_return) }}
                </div>
              </div>
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">基准收益</div>
                <div class="jq-metric-value" :class="getValueClass(result.benchmark_return)">
                  {{ formatPercent(result.benchmark_return) }}
                </div>
              </div>
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">阿尔法</div>
                <div class="jq-metric-value" :class="getAlphaClass(result.alpha)">
                  {{ formatRatio(result.alpha) }}
                </div>
              </div>
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">贝塔</div>
                <div class="jq-metric-value">{{ formatRatio(result.beta) }}</div>
              </div>
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">夏普比率</div>
                <div class="jq-metric-value" :class="getRatioClass(result.sharpe_ratio)">
                  {{ formatRatio(result.sharpe_ratio) }}
                </div>
              </div>
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">胜率</div>
                <div class="jq-metric-value" :class="getValueClass(result.win_rate)">
                  {{ formatPercent(result.win_rate) }}
                </div>
              </div>
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">盈亏比</div>
                <div class="jq-metric-value">{{ formatRatio(result.profit_loss_ratio) }}</div>
              </div>
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">最大回撤</div>
                <div class="jq-metric-value negative">{{ formatPercent(result.max_drawdown) }}</div>
              </div>
              <div class="jq-metric-card primary">
                <div class="jq-metric-label">索提诺比率</div>
                <div class="jq-metric-value" :class="getRatioClass(result.sortino_ratio)">
                  {{ formatRatio(result.sortino_ratio) }}
                </div>
              </div>
            </div>
          </div>

          <div class="jq-metrics-section secondary">
            <div class="jq-metrics-row">
              <div class="jq-metric-card">
                <div class="jq-metric-label">日均超额收益</div>
                <div class="jq-metric-value" :class="getValueClass(result.daily_excess_return)">
                  {{ formatPercent(result.daily_excess_return) }}
                </div>
              </div>
              <div class="jq-metric-card">
                <div class="jq-metric-label">超额收益最大回撤</div>
                <div class="jq-metric-value negative">{{ formatPercent(result.excess_max_drawdown) }}</div>
              </div>
              <div class="jq-metric-card">
                <div class="jq-metric-label">超额收益夏普比率</div>
                <div class="jq-metric-value" :class="getRatioClass(result.information_ratio)">
                  {{ formatRatio(result.information_ratio) }}
                </div>
              </div>
              <div class="jq-metric-card">
                <div class="jq-metric-label">日胜率</div>
                <div class="jq-metric-value" :class="getValueClass(result.daily_win_rate)">
                  {{ formatPercent(result.daily_win_rate) }}
                </div>
              </div>
              <div class="jq-metric-card">
                <div class="jq-metric-label">盈利次数</div>
                <div class="jq-metric-value positive">{{ result.win_count ?? '--' }}</div>
              </div>
              <div class="jq-metric-card">
                <div class="jq-metric-label">亏损次数</div>
                <div class="jq-metric-value negative">{{ result.loss_count ?? '--' }}</div>
              </div>
              <div class="jq-metric-card">
                <div class="jq-metric-label">信息比率</div>
                <div class="jq-metric-value" :class="getRatioClass(result.information_ratio)">
                  {{ formatRatio(result.information_ratio) }}
                </div>
              </div>
              <div class="jq-metric-card">
                <div class="jq-metric-label">策略波动率</div>
                <div class="jq-metric-value">{{ formatPercent(result.volatility) }}</div>
              </div>
              <div class="jq-metric-card">
                <div class="jq-metric-label">基准波动率</div>
                <div class="jq-metric-value">{{ formatPercent(result.benchmark_volatility) }}</div>
              </div>
              <div class="jq-metric-card">
                <div class="jq-metric-label">最大回撤区间</div>
                <div class="jq-metric-value">{{ result.max_drawdown_duration ?? '--' }}</div>
              </div>
            </div>
          </div>

          <div class="jq-chart-section">
            <div class="jq-chart-controls">
              <div class="jq-chart-title">收益曲线</div>
              <div class="jq-chart-buttons">
                <span class="jq-chart-label">缩放:</span>
                <el-button size="small" :type="chartTimeRange === '1m'" @click="chartTimeRange = '1m'">1个月</el-button>
                <el-button size="small" :type="chartTimeRange === '1y'" @click="chartTimeRange = '1y'">1年</el-button>
                <el-button size="small" :type="chartTimeRange === 'all'" @click="chartTimeRange = 'all'">全部</el-button>
                <el-divider direction="vertical"></el-divider>
                <span class="jq-chart-legend">
                  <span class="jq-legend-item"><span class="jq-legend-color" style="background: #3B82F6;"></span>策略收益</span>
                  <span class="jq-legend-item"><span class="jq-legend-color" style="background: #FF4757;"></span>基准收益</span>
                  <span class="jq-legend-item"><span class="jq-legend-color" style="background: #f59e0b;"></span>超额收益</span>
                </span>
                <el-divider direction="vertical"></el-divider>
                <span class="jq-chart-axis">
                  <el-radio v-model="chartAxisType" label="normal" size="small">普通轴</el-radio>
                  <el-radio v-model="chartAxisType" label="log" size="small">对数轴</el-radio>
                </span>
              </div>
              <div class="jq-chart-time-range">
                <span class="jq-chart-label">时间:</span>
                <el-input v-model="chartStartDate" type="date" size="small" style="width: 140px;"></el-input>
                <span class="jq-chart-separator">-</span>
                <el-input v-model="chartEndDate" type="date" size="small" style="width: 140px;"></el-input>
              </div>
            </div>
            <v-chart :option="chartOption" autoresize class="jq-chart" style="height: 400px;"></v-chart>
          </div>
        </div>

        <div v-if="activeTab === 'overview' && !result" class="jq-panel">
          <div class="jq-empty-state">
            <el-icon class="jq-empty-icon"><dataanalysis></dataanalysis></el-icon>
            <p>暂无回测结果，请先运行回测</p>
          </div>
        </div>

        <!-- 交易详情面板 -->
        <div v-if="activeTab === 'trades'" class="jq-panel">
          <div class="jq-panel-header">
            <h2>交易详情</h2>
          </div>
          <div v-if="result?.trades?.length" class="jq-table-wrapper">
            <el-table :data="sortedTrades" stripe size="small" class="jq-table" :header-cell-class-name="'jq-table-header'">
              <el-table-column prop="datetime" label="时间" width="180"></el-table-column>
              <el-table-column prop="signal" label="信号" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.signal === 'buy' ? 'success' : 'danger'" size="small">{{ getSignalLabel(row.signal) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="price" label="价格" width="120">
                <template #default="{ row }">{{ row.price?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="amount" label="数量" width="120">
                <template #default="{ row }">{{ row.amount?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="position" label="持仓" width="120">
                <template #default="{ row }">{{ row.position?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="commission" label="手续费" width="120">
                <template #default="{ row }">{{ row.commission?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="cash" label="现金" width="140">
                <template #default="{ row }">{{ row.cash?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="market_value" label="市值" width="140">
                <template #default="{ row }">{{ row.market_value?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="total_asset" label="总资产" width="140">
                <template #default="{ row }">{{ row.total_asset?.toFixed(2) }}</template>
              </el-table-column>
            </el-table>
          </div>
          <div v-else class="jq-placeholder-state">
            <el-icon class="jq-placeholder-icon"><list></list></el-icon>
            <p>暂无数据</p>
          </div>
        </div>

        <!-- 每日持仓面板 -->
        <div v-if="activeTab === 'positions'" class="jq-panel">
          <div class="jq-panel-header">
            <h2>每日持仓</h2>
          </div>
          <div v-if="result?.position_details?.length" class="jq-table-wrapper">
            <el-table :data="result.position_details" stripe size="small" class="jq-table" :header-cell-class-name="'jq-table-header'">
              <el-table-column prop="datetime" label="日期" width="140"></el-table-column>
              <el-table-column prop="position" label="持仓" width="120">
                <template #default="{ row }">{{ row.position?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="price" label="价格" width="120">
                <template #default="{ row }">{{ row.price?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="market_value" label="市值" width="140">
                <template #default="{ row }">{{ row.market_value?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="cash" label="现金" width="140">
                <template #default="{ row }">{{ row.cash?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="total_asset" label="总资产" width="140">
                <template #default="{ row }">{{ row.total_asset?.toFixed(2) }}</template>
              </el-table-column>
              <el-table-column prop="profit_loss" label="盈亏" width="120">
                <template #default="{ row }">
                  <span :class="row.profit_loss >= 0 ? 'positive' : 'negative'">{{ row.profit_loss >= 0 ? '+' : '' }}{{ row.profit_loss?.toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="return" label="收益率" width="120">
                <template #default="{ row }">
                  <span :class="row.return >= 0 ? 'positive' : 'negative'">{{ formatPercent(row.return) }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div v-else class="jq-placeholder-state">
            <el-icon class="jq-placeholder-icon"><calendar></calendar></el-icon>
            <p>暂无数据</p>
          </div>
        </div>

        <div v-if="activeTab === 'logs'" class="jq-panel">
          <div class="jq-panel-header">
            <h2>日志输出</h2>
          </div>
          <div class="jq-placeholder-state">
            <el-icon class="jq-placeholder-icon"><document></document></el-icon>
            <p>回测完成后显示运行日志</p>
          </div>
        </div>

        <div v-if="activeTab === 'analysis'" class="jq-panel">
          <div class="jq-panel-header">
            <h2>性能分析</h2>
          </div>
          
          <div v-if="result" class="jq-analysis-content">
            <div class="jq-analysis-sidebar">
              <div class="jq-analysis-nav">
                <div 
                  v-for="item in analysisNavItems" 
                  :key="item.id"
                  :class="['jq-analysis-nav-item', { 'jq-analysis-nav-active': activeAnalysisTab === item.id }]"
                  @click="activeAnalysisTab = item.id"
                >
                  <el-icon :component="item.icon"></el-icon>
                  <span>{{ item.label }}</span>
                </div>
              </div>
            </div>
            
            <div class="jq-analysis-main">
              <div v-if="activeAnalysisTab === 'strategy_return'" class="jq-analysis-section">
                <h3 class="jq-analysis-section-title">策略收益</h3>
                <div class="jq-rolling-table-wrapper">
                  <el-table 
                    :data="rollingReturnsData" 
                    stripe 
                    size="small" 
                    class="jq-rolling-table"
                    :header-cell-class-name="'jq-table-header'"
                  >
                    <el-table-column prop="date" label="日期" width="100"></el-table-column>
                    <el-table-column prop="1_month" label="1个月" width="120">
                      <template #default="{ row }">
                        <span :class="row['1_month'] >= 0 ? 'positive' : 'negative'">{{ formatRatio(row['1_month']) }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="3_month" label="3个月" width="120">
                      <template #default="{ row }">
                        <span :class="row['3_month'] >= 0 ? 'positive' : 'negative'">{{ formatRatio(row['3_month']) }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="6_month" label="6个月" width="120">
                      <template #default="{ row }">
                        <span :class="row['6_month'] >= 0 ? 'positive' : 'negative'">{{ formatRatio(row['6_month']) }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="12_month" label="12个月" width="120">
                      <template #default="{ row }">
                        <span :class="row['12_month'] >= 0 ? 'positive' : 'negative'">{{ formatRatio(row['12_month']) }}</span>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
              
              <div v-if="activeAnalysisTab === 'benchmark_return'" class="jq-analysis-section">
                <h3 class="jq-analysis-section-title">基准收益</h3>
                <div class="jq-analysis-metrics">
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">基准收益率</span>
                    <span :class="['jq-analysis-metric-value', result.benchmark_return >= 0 ? 'positive' : 'negative']">
                      {{ formatPercent(result.benchmark_return) }}
                    </span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">基准波动率</span>
                    <span class="jq-analysis-metric-value">{{ formatPercent(result.benchmark_volatility) }}</span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">相关系数</span>
                    <span class="jq-analysis-metric-value">{{ formatRatio(result.correlation) }}</span>
                  </div>
                </div>
              </div>
              
              <div v-if="activeAnalysisTab === 'alpha'" class="jq-analysis-section">
                <h3 class="jq-analysis-section-title">阿尔法</h3>
                <div class="jq-analysis-metrics">
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">Alpha值</span>
                    <span :class="['jq-analysis-metric-value', result.alpha >= 0 ? 'positive' : 'negative']">
                      {{ formatRatio(result.alpha) }}
                    </span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">年化Alpha</span>
                    <span :class="['jq-analysis-metric-value', result.alpha >= 0 ? 'positive' : 'negative']">
                      {{ formatPercent(result.alpha) }}
                    </span>
                  </div>
                </div>
              </div>
              
              <div v-if="activeAnalysisTab === 'beta'" class="jq-analysis-section">
                <h3 class="jq-analysis-section-title">贝塔</h3>
                <div class="jq-analysis-metrics">
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">Beta值</span>
                    <span class="jq-analysis-metric-value">{{ formatRatio(result.beta) }}</span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">市场敏感度</span>
                    <span class="jq-analysis-metric-value">
                      {{ result.beta >= 1 ? '高于市场' : result.beta > 0 ? '跟随市场' : '逆市场' }}
                    </span>
                  </div>
                </div>
              </div>
              
              <div v-if="activeAnalysisTab === 'sharpe'" class="jq-analysis-section">
                <h3 class="jq-analysis-section-title">夏普比率</h3>
                <div class="jq-analysis-metrics">
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">夏普比率</span>
                    <span :class="['jq-analysis-metric-value', result.sharpe_ratio > 1 ? 'positive' : 'negative']">
                      {{ formatRatio(result.sharpe_ratio) }}
                    </span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">索提诺比率</span>
                    <span :class="['jq-analysis-metric-value', result.sortino_ratio > 1 ? 'positive' : 'negative']">
                      {{ formatRatio(result.sortino_ratio) }}
                    </span>
                  </div>
                </div>
              </div>
              
              <div v-if="activeAnalysisTab === 'sortino'" class="jq-analysis-section">
                <h3 class="jq-analysis-section-title">索提诺比率</h3>
                <div class="jq-analysis-metrics">
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">索提诺比率</span>
                    <span :class="['jq-analysis-metric-value', result.sortino_ratio > 1 ? 'positive' : 'negative']">
                      {{ formatRatio(result.sortino_ratio) }}
                    </span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">下行偏差</span>
                    <span class="jq-analysis-metric-value">{{ formatPercent(result.downside_deviation || 0) }}</span>
                  </div>
                </div>
              </div>
              
              <div v-if="activeAnalysisTab === 'information'" class="jq-analysis-section">
                <h3 class="jq-analysis-section-title">信息比率</h3>
                <div class="jq-analysis-metrics">
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">信息比率</span>
                    <span :class="['jq-analysis-metric-value', result.information_ratio > 0.5 ? 'positive' : 'negative']">
                      {{ formatRatio(result.information_ratio) }}
                    </span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">跟踪误差</span>
                    <span class="jq-analysis-metric-value">{{ formatPercent(result.tracking_error || 0) }}</span>
                  </div>
                </div>
              </div>
              
              <div v-if="activeAnalysisTab === 'volatility'" class="jq-analysis-section">
                <h3 class="jq-analysis-section-title">波动率</h3>
                <div class="jq-analysis-metrics">
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">策略波动率</span>
                    <span class="jq-analysis-metric-value">{{ formatPercent(result.volatility) }}</span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">基准波动率</span>
                    <span class="jq-analysis-metric-value">{{ formatPercent(result.benchmark_volatility) }}</span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">波动率比率</span>
                    <span class="jq-analysis-metric-value">{{ formatRatio((result.volatility / result.benchmark_volatility) || 0) }}</span>
                  </div>
                </div>
              </div>
              
              <div v-if="activeAnalysisTab === 'benchmark_volatility'" class="jq-analysis-section">
                <h3 class="jq-analysis-section-title">基准波动率</h3>
                <div class="jq-analysis-metrics">
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">基准波动率</span>
                    <span class="jq-analysis-metric-value">{{ formatPercent(result.benchmark_volatility) }}</span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">策略波动率</span>
                    <span class="jq-analysis-metric-value">{{ formatPercent(result.volatility) }}</span>
                  </div>
                </div>
              </div>
              
              <div v-if="activeAnalysisTab === 'max_drawdown'" class="jq-analysis-section">
                <h3 class="jq-analysis-section-title">最大回撤</h3>
                <div class="jq-analysis-metrics">
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">最大回撤</span>
                    <span class="jq-analysis-metric-value negative">{{ formatPercent(result.max_drawdown) }}</span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">回撤周期</span>
                    <span class="jq-analysis-metric-value">{{ result.max_drawdown_duration }} 天</span>
                  </div>
                  <div class="jq-analysis-metric">
                    <span class="jq-analysis-metric-label">卡玛比率</span>
                    <span :class="['jq-analysis-metric-value', result.calmar_ratio > 1 ? 'positive' : 'negative']">
                      {{ formatRatio(result.calmar_ratio) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="jq-placeholder-state">
            <el-icon class="jq-placeholder-icon"><dataline></dataline></el-icon>
            <p>回测完成后显示详细性能分析</p>
          </div>
        </div>

        <div v-if="activeTab === 'code'" class="jq-panel">
          <div class="jq-panel-header">
            <h2>策略代码</h2>
          </div>
          <div class="jq-placeholder-state">
            <el-icon class="jq-placeholder-icon"><code></code></el-icon>
            <p>显示策略源代码</p>
          </div>
        </div>
      </main>
    </div>

    <el-dialog v-model="showExportDialog" title="导出数据" width="400px">
      <div class="jq-export-options">
        <el-button type="primary" @click="exportCSV" style="width: 100%; margin-bottom: 10px;">导出 CSV 格式</el-button>
        <el-button type="success" @click="exportMarkdown" style="width: 100%;">导出 Markdown 格式</el-button>
      </div>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAnalysis" title="归因分析" width="800px">
      <div class="jq-analysis-content">
        <h3>收益归因分析</h3>
        <p>归因分析功能开发中...</p>
      </div>
      <template #footer>
        <el-button @click="showAnalysis = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { PieChart, TrendCharts, DataAnalysis, DataBoard, DataLine, ArrowUp, Coffee, Monitor, Setting, Wallet } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import SymbolSelector from './SymbolSelector.vue'
import { backtestService } from '../services/backtest.js'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
])

export default {
  name: 'BacktestUniversal',
  components: {
    SymbolSelector,
    VChart
  },
  setup() {
    const navItems = ref([
      { id: 'overview', label: '收益概述', icon: 'Wallet' },
      { id: 'trades', label: '交易详情', icon: 'List' },
      { id: 'positions', label: '每日持仓&收益', icon: 'Calendar' },
      { id: 'logs', label: '日志输出', icon: 'Document' },
      { id: 'analysis', label: '性能分析', icon: 'DataLine' },
      { id: 'code', label: '策略代码', icon: 'Code' }
    ])

    const analysisNavItems = ref([
      { id: 'strategy_return', label: '策略收益', icon: ArrowUp },
      { id: 'benchmark_return', label: '基准收益', icon: PieChart },
      { id: 'alpha', label: '阿尔法', icon: TrendCharts },
      { id: 'beta', label: '贝塔', icon: DataBoard },
      { id: 'sharpe', label: '夏普比率', icon: DataAnalysis },
      { id: 'sortino', label: '索提诺比率', icon: DataLine },
      { id: 'information', label: '信息比率', icon: Monitor },
      { id: 'volatility', label: '波动率', icon: Coffee },
      { id: 'benchmark_volatility', label: '基准波动率', icon: Setting },
      { id: 'max_drawdown', label: '最大回撤', icon: Wallet }
    ])

    const activeTab = ref('overview')
    const activeAnalysisTab = ref('strategy_return')
    const backtestId = ref(null)
    const chartTimeRange = ref('all')
    const chartAxisType = ref('normal')
    const chartStartDate = ref('')
    const chartEndDate = ref('')
    const showExportDialog = ref(false)

    const form = reactive({
      strategy_type: 'grid',
      strategy_name: '',
      symbol: '',
      start_date: '',
      end_date: '',
      initial_cash: 1000000,
      frequency: 'daily',
      base_price: 10000,
      upper_step: 1,
      lower_step: 1,
      upper_count: 5,
      lower_count: 5,
      buy_quantity: 100,
      sell_quantity: 100,
      max_position: null,
      min_position: null,
      commission_rate: 0.0001
    })

    const strategyTypes = ref([])

    const loading = ref(false)
    const statusText = ref('待运行')
    const statusClass = ref('')
    const backtestTime = ref(null)
    const result = ref(null)
    const showAnalysis = ref(false)
    const chartOption = ref(null)

    const getStatusClass = () => {
      if (loading.value) return 'status-running'
      if (result.value) return 'status-success'
      return ''
    }

    const formatPercent = (value) => {
      if (value === null || value === undefined) return '--'
      const sign = value < 0 ? '-' : ''
      return sign + Math.abs(value).toFixed(2) + '%'
    }

    const formatRatio = (value) => {
      if (value === null || value === undefined) return '--'
      return value.toFixed(2)
    }

    const formatCurrency = (value) => {
      if (value === null || value === undefined) return '--'
      return '¥' + value.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
    }

    const getValueClass = (value) => {
      if (value === null || value === undefined) return ''
      if (value > 0) return 'positive'
      if (value < 0) return 'negative'
      return ''
    }

    const getRatioClass = (value) => {
      if (value === null || value === undefined) return ''
      if (value > 0) return 'positive'
      return ''
    }

    const getAlphaClass = (value) => {
      if (value === null || value === undefined) return ''
      if (value > 0) return 'positive'
      if (value < 0) return 'negative'
      return ''
    }

    const getSignalLabel = (signal) => {
      return signal === 'buy' ? '买入' : signal === 'sell' ? '卖出' : signal
    }

    const getSignalClass = (signal) => {
      return signal === 'buy' ? 'signal-buy' : signal === 'sell' ? 'signal-sell' : ''
    }

    const loadStrategies = async () => {
      try {
        const data = await backtestService.getStrategies()
        strategyTypes.value = data.strategies || []
      } catch (error) {
        console.error('加载策略列表失败:', error)
      }
    }

    const updateChart = () => {
      if (!result.value) return

      const { equity_curve, benchmark_curve } = result.value
      
      let equityData = equity_curve || []
      let benchmarkData = benchmark_curve || []
      
      // 确保基准数据与策略数据长度一致
      if (benchmarkData.length < equityData.length) {
        const lastBmValue = benchmarkData[benchmarkData.length - 1]?.return || 0
        while (benchmarkData.length < equityData.length) {
          benchmarkData.push({ datetime: '', return: lastBmValue })
        }
      } else if (benchmarkData.length > equityData.length) {
        benchmarkData = benchmarkData.slice(0, equityData.length)
      }
      
      if (chartTimeRange.value === '1m' && equityData.length > 30) {
        equityData = equityData.slice(-30)
        benchmarkData = benchmarkData.slice(-30)
      } else if (chartTimeRange.value === '1y' && equityData.length > 365) {
        equityData = equityData.slice(-365)
        benchmarkData = benchmarkData.slice(-365)
      }

      const strategySeries = {
        name: '策略收益',
        type: 'line',
        data: equityData.map(d => [d.datetime, d.return || 0]),
        smooth: true,
        itemStyle: { color: '#3B82F6' },
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59, 130, 246, 0.2)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
            ]
          }
        }
      }

      const benchmarkSeries = {
        name: '沪深300',
        type: 'line',
        data: benchmarkData.map(d => [d.datetime, d.return || 0]),
        smooth: true,
        itemStyle: { color: '#dc2626' },
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(220, 38, 38, 0.15)' },
              { offset: 1, color: 'rgba(220, 38, 38, 0.03)' }
            ]
          }
        }
      }

      const excessSeries = {
        name: '超额收益',
        type: 'line',
        data: equityData.map((d, i) => {
          const bmReturn = benchmarkData[i]?.return || 0
          return [d.datetime, (d.return || 0) - bmReturn]
        }),
        smooth: true,
        itemStyle: { color: '#f59e0b' },
        lineStyle: { width: 2, type: 'dashed' }
      }

      chartOption.value = {
        title: { text: '收益曲线', left: 'center', textStyle: { fontSize: 16, fontWeight: 600 } },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            let result = params[0].axisValue + '<br/>'
            params.forEach(param => {
              result += `${param.marker}${param.seriesName}: ${param.value[1]?.toFixed(2)}%<br/>`
            })
            return result
          }
        },
        legend: { show: false },
        grid: { left: '3%', right: '4%', bottom: '3%', top: 80, containLabel: true },
        xAxis: { type: 'category', boundaryGap: false },
        yAxis: { 
          type: chartAxisType.value === 'log' ? 'log' : 'value', 
          axisLabel: { formatter: '{value}%' },
          min: chartAxisType.value === 'log' ? 0.1 : null
        },
        dataZoom: [
          { type: 'inside', start: 0, end: 100 },
          { start: 0, end: 100 }
        ],
        series: [strategySeries, benchmarkSeries, excessSeries]
      }
    }

    const handleStrategyTypeChange = () => {
    }

    const runBacktest = async () => {
      if (!form.symbol) {
        ElMessage.warning('请选择回测标的')
        return
      }
      if (!form.start_date || !form.end_date) {
        ElMessage.warning('请选择回测时间范围')
        return
      }

      const startTime = Date.now()
      loading.value = true
      statusText.value = '回测中...'
      statusClass.value = 'status-running'

      try {
        const params = {
          strategy_type: form.strategy_type,
          symbol: form.symbol,
          initial_cash: form.initial_cash,
          start_date: form.start_date,
          end_date: form.end_date,
          base_price: form.base_price,
          upper_step: form.upper_step,
          lower_step: form.lower_step,
          upper_count: form.upper_count,
          lower_count: form.lower_count,
          buy_quantity: form.buy_quantity,
          sell_quantity: form.sell_quantity,
          commission_rate: form.commission_rate
        }

        if (form.max_position) params.max_position = form.max_position
        if (form.min_position) params.min_position = form.min_position

        const response = await backtestService.runDirect(params)

        if (response.status === 'success') {
          backtestId.value = response.backtest_id
          
          await nextTick()
          const resultData = await backtestService.getResults(response.backtest_id)
          result.value = resultData.data
          
          const duration = ((Date.now() - startTime) / 1000).toFixed(2)
          backtestTime.value = duration + '秒'
          
          statusText.value = '已完成'
          statusClass.value = 'status-success'
          activeTab.value = 'overview'
          
          await nextTick()
          updateChart()
          
          ElMessage.success('回测完成')
        } else {
          throw new Error(response.message || '回测失败')
        }
      } catch (error) {
        statusText.value = '失败'
        statusClass.value = 'status-error'
        ElMessage.error(error.message || '回测请求失败')
      } finally {
        loading.value = false
      }
    }

    const exportCSV = () => {
      showExportDialog.value = false
      if (!result.value) return
      
      let csvContent = ''
      
      if (activeTab.value === 'trades' && result.value.trades) {
        csvContent = '时间,信号,价格,数量,持仓,手续费,现金,市值,总资产\n'
        result.value.trades.forEach(trade => {
          csvContent += `${trade.datetime},${trade.signal},${trade.price},${trade.amount},${trade.position},${trade.commission},${trade.cash},${trade.market_value},${trade.total_asset}\n`
        })
      } else if (activeTab.value === 'positions' && result.value.position_details) {
        csvContent = '时间,持仓,价格,市值,现金,总资产,盈亏\n'
        result.value.position_details.forEach(pos => {
          csvContent += `${pos.datetime},${pos.position},${pos.price},${pos.market_value},${pos.cash},${pos.total_asset},${pos.profit_loss}\n`
        })
      } else {
        const r = result.value
        csvContent = '指标,值\n'
        csvContent += `策略收益,${r.total_return}%\n`
        csvContent += `年化收益,${r.annual_return}%\n`
        csvContent += `超额收益,${r.excess_return}%\n`
        csvContent += `基准收益,${r.benchmark_return}%\n`
        csvContent += `Alpha,${r.alpha}\n`
        csvContent += `Beta,${r.beta}\n`
        csvContent += `夏普比率,${r.sharpe_ratio}\n`
        csvContent += `胜率,${r.win_rate}%\n`
        csvContent += `盈亏比,${r.profit_loss_ratio}\n`
        csvContent += `最大回撤,${r.max_drawdown}%\n`
        csvContent += `索提诺比率,${r.sortino_ratio}\n`
        csvContent += `卡玛比率,${r.calmar_ratio}\n`
      }
      
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `backtest_${backtestId.value || Date.now()}.csv`
      link.click()
      
      ElMessage.success('导出成功')
    }

    const exportMarkdown = () => {
      showExportDialog.value = false
      if (!result.value) return
      
      const r = result.value
      let md = `# 回测报告\n\n`
      md += `## 策略收益\n\n`
      md += `| 指标 | 值 |\n|------|-----|\n`
      md += `| 策略收益 | ${r.total_return?.toFixed(2)}% |\n`
      md += `| 年化收益 | ${r.annual_return?.toFixed(2)}% |\n`
      md += `| 超额收益 | ${r.excess_return?.toFixed(2)}% |\n`
      md += `| 基准收益 | ${r.benchmark_return?.toFixed(2)}% |\n\n`
      
      md += `## 风险指标\n\n`
      md += `| 指标 | 值 |\n|------|-----|\n`
      md += `| Alpha | ${r.alpha?.toFixed(4)} |\n`
      md += `| Beta | ${r.beta?.toFixed(4)} |\n`
      md += `| 夏普比率 | ${r.sharpe_ratio?.toFixed(4)} |\n`
      md += `| 索提诺比率 | ${r.sortino_ratio?.toFixed(4)} |\n`
      md += `| 卡玛比率 | ${r.calmar_ratio?.toFixed(4)} |\n`
      md += `| 最大回撤 | ${r.max_drawdown?.toFixed(2)}% |\n\n`
      
      md += `## 交易统计\n\n`
      md += `| 指标 | 值 |\n|------|-----|\n`
      md += `| 胜率 | ${r.win_rate?.toFixed(2)}% |\n`
      md += `| 盈亏比 | ${r.profit_loss_ratio?.toFixed(4)} |\n`
      md += `| 盈利次数 | ${r.win_count} |\n`
      md += `| 亏损次数 | ${r.loss_count} |\n`
      md += `| 日胜率 | ${r.daily_win_rate?.toFixed(2)}% |\n\n`
      
      const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `backtest_${backtestId.value || Date.now()}.md`
      link.click()
      
      ElMessage.success('导出成功')
    }

    const handleExport = () => {
      if (!result.value) {
        ElMessage.warning('请先运行回测')
        return
      }
      showExportDialog.value = true
    }

    // 交易数据按时间倒序排列
    const sortedTrades = computed(() => {
      if (!result.value?.trades) return []
      return [...result.value.trades].sort((a, b) => {
        return new Date(b.datetime) - new Date(a.datetime)
      })
    })

    // 滚动收益数据（按月去重）
    const rollingReturnsData = computed(() => {
      if (!result.value?.rolling_returns) return []
      
      const rollingData = result.value.rolling_returns
      const monthlyMap = new Map()
      
      rollingData.forEach(item => {
        const date = item.date
        if (!monthlyMap.has(date)) {
          monthlyMap.set(date, item)
        }
      })
      
      return Array.from(monthlyMap.values()).sort((a, b) => a.date.localeCompare(b.date))
    })

    watch(chartTimeRange, () => {
      updateChart()
    })

    watch(chartAxisType, () => {
      updateChart()
    })

    onMounted(() => {
      loadStrategies()
    })

    return {
      navItems,
      analysisNavItems,
      activeTab,
      activeAnalysisTab,
      form,
      strategyTypes,
      loading,
      statusText,
      statusClass,
      backtestTime,
      result,
      showAnalysis,
      chartOption,
      chartTimeRange,
      chartAxisType,
      chartStartDate,
      chartEndDate,
      showExportDialog,
      rollingReturnsData,
      getStatusClass,
      formatPercent,
      formatRatio,
      formatCurrency,
      getValueClass,
      getRatioClass,
      getAlphaClass,
      getSignalLabel,
      handleStrategyTypeChange,
      runBacktest,
      exportCSV,
      exportMarkdown,
      handleExport,
      sortedTrades,
      PieChart,
      TrendCharts,
      DataAnalysis,
      DataBoard,
      DataLine,
      ArrowUp,
      Coffee,
      Monitor,
      Setting,
      Wallet
    }
  }
}
</script>

<style scoped>
.jq-backtest-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #F8F9FA;
}

.jq-status-bar {
  display: flex;
  flex-direction: column;
  padding: 8px 24px;
  background: #fff;
  border-bottom: 1px solid #E9ECEF;
  font-size: 13px;
  gap: 8px;
}

.jq-status-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

:deep(.jq-status-select) {
  width: 120px;
  font-size: 13px;
}

:deep(.jq-status-selector) {
  width: 150px;
  font-size: 13px;
}

:deep(.jq-status-date) {
  width: 140px;
  font-size: 13px;
}

.jq-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.jq-header-left {
  display: flex;
  align-items: center;
}

.jq-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.jq-header-center {
  display: flex;
  align-items: center;
  gap: 16px;
}

.jq-strategy-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: #F8F9FA;
  border-radius: 6px;
}

.jq-strategy-label,
.jq-symbol-label {
  font-size: 12px;
  color: #909399;
}

.jq-strategy-value,
.jq-symbol-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.jq-strategy-divider {
  width: 1px;
  height: 16px;
  background: #DCDFE6;
  margin: 0 8px;
}

.jq-status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.jq-status-label {
  font-size: 13px;
  color: #909399;
}

.jq-status-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.jq-status-value.status-success {
  color: #2ED573;
}

.jq-status-value.status-error {
  color: #FF4757;
}

.jq-status-value.status-running {
  color: #FF4757;
}

.jq-status-divider {
  width: 1px;
  height: 20px;
  background: #e4e7ed;
}

.jq-badge {
  padding: 4px 12px;
  background: #4CAF50;
  color: #fff;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.jq-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

:deep(.jq-btn-primary) {
  background: #FF4757;
  border-color: #FF4757;
}

:deep(.jq-btn-primary:hover) {
  background: #E8384E;
  border-color: #E8384E;
}

:deep(.jq-btn-secondary) {
  background: #fff;
  border-color: #e4e7ed;
  color: #606266;
}

:deep(.jq-btn-secondary:hover) {
  background: #f5f7fa;
  border-color: #4f46e5;
  color: #4f46e5;
}

.jq-main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.jq-sidebar {
  width: 140px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  padding: 16px 0;
}

.jq-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 8px;
}

.jq-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 0;
  cursor: pointer;
  color: #303133;
  transition: all 0.3s;
  margin: 0 4px;
}

.jq-nav-item:hover {
  background: #F0F5FF;
  color: #3B82F6;
}

.jq-nav-active {
  background: #3B82F6;
  color: #fff;
  font-weight: 500;
  border-radius: 4px;
}

.jq-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.jq-panel {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.jq-panel-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.jq-panel-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.jq-config-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.jq-form-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.jq-form-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  padding-left: 12px;
  border-left: 3px solid #4f46e5;
}

.jq-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.jq-form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.jq-form-item label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

:deep(.jq-form-input) {
  width: 100%;
}

:deep(.jq-form-select) {
  width: 100%;
}

.jq-metrics-section {
  margin-bottom: 20px;
}

.jq-metrics-section.secondary {
  margin-top: 20px;
}

.jq-metrics-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

.jq-metrics-section.secondary .jq-metrics-row {
  grid-template-columns: repeat(5, 1fr);
}

.jq-metric-card {
  background: #fff;
  border: 1px solid #E9ECEF;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}

.jq-metric-card:hover {
  border-color: #3B82F6;
}

.jq-metric-card.primary {
  background: #fff;
  padding: 20px;
}

.jq-metric-label {
  font-size: 12px;
  color: #636E72;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.jq-metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #2D3436;
}

.jq-metric-card.primary .jq-metric-value {
  font-size: 24px;
}

.jq-metric-value.positive {
  color: #2ED573;
}

.jq-metric-value.negative {
  color: #FF4757;
}

.jq-chart-section {
  margin-top: 32px;
}

.jq-chart-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.jq-chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.jq-chart-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

.jq-chart-label {
  font-size: 13px;
  color: #606266;
  margin-right: 4px;
}

.jq-chart-legend {
  display: flex;
  gap: 16px;
}

.jq-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

.jq-legend-color {
  width: 12px;
  height: 3px;
  border-radius: 2px;
}

.jq-chart-axis {
  display: flex;
  gap: 8px;
}

.jq-chart-time-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.jq-chart-separator {
  color: #c0c4cc;
}

.jq-chart {
  width: 100%;
}

.jq-table-container {
  margin-top: 16px;
}

.jq-signal-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.jq-signal-tag.signal-buy {
  background: #d1fae5;
  color: #059669;
}

.jq-signal-tag.signal-sell {
  background: #fee2e2;
  color: #dc2626;
}

.jq-profit-value {
  font-weight: 500;
}

.jq-profit-value.positive {
  color: #2ED573;
}

.jq-profit-value.negative {
  color: #FF4757;
}

.jq-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.jq-empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #c0c4cc;
}

.jq-empty-state p {
  font-size: 14px;
  margin: 0;
}

.jq-placeholder-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #909399;
}

.jq-placeholder-icon {
  font-size: 56px;
  margin-bottom: 16px;
  color: #c0c4cc;
}

.jq-placeholder-state p {
  font-size: 14px;
  margin: 0;
}

.jq-export-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.jq-analysis-content {
  display: flex;
  min-height: 500px;
}

.jq-analysis-sidebar {
  width: 180px;
  border-right: 1px solid #ebeef5;
  padding-right: 16px;
}

.jq-analysis-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.jq-analysis-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  transition: all 0.2s;
}

.jq-analysis-nav-item:hover {
  background-color: #F8F9FA;
  color: #3B82F6;
}

.jq-analysis-nav-active {
  background-color: #DBEAFE;
  color: #3B82F6;
  font-weight: 500;
}

.jq-analysis-main {
  flex: 1;
  padding-left: 20px;
}

.jq-analysis-section {
  min-height: 300px;
}

.jq-analysis-section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.jq-rolling-table-wrapper {
  overflow-x: auto;
}

.jq-rolling-table {
  width: 100%;
}

:deep(.jq-table-header) {
  background-color: #fafafa;
  font-weight: 600;
  color: #606266;
}

.jq-analysis-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.jq-analysis-metric {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background-color: #fafafa;
  border-radius: 8px;
}

.jq-analysis-metric-label {
  font-size: 13px;
  color: #909399;
}

.jq-analysis-metric-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.jq-analysis-metric-value.positive {
  color: #67c23a;
}

.jq-analysis-metric-value.negative {
  color: #f56c6c;
}
</style>