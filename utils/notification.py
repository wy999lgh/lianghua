"""
消息通知模块

基于企业微信群机器人 Webhook 发送消息，支持：
- 文本消息、Markdown 消息、图文消息
- 交易信号、风险告警、系统异常、每日汇总等通知模板
- 频率控制（同类消息间隔限制）
- 异步发送（后台线程不阻塞主业务）
- 重试机制（失败自动重试，间隔递增）
- 优雅降级（无 Webhook URL 或 enabled=false 时静默返回）
"""

import time
import threading
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

from utils.logger import TradingLogger
from utils.config_manager import ConfigManager


class NotificationManager:
    """消息通知管理器 - 企业微信 Webhook"""

    def __init__(self):
        """
        初始化通知管理器

        从 ConfigManager 读取 notification 配置：
        - enabled: 是否启用通知
        - wechat_webhook_url: 企业微信 Webhook URL
        - rate_limit: 同类消息最小发送间隔（秒）
        - notify_on_error: 是否发送错误通知
        - notify_on_trade: 是否发送交易通知
        """
        self._logger = TradingLogger('notification')
        self._config = ConfigManager()

        # 加载通知配置
        self._enabled = self._config.get('notification.enabled', False)
        self._webhook_url = self._config.get(
            'notification.wechat_webhook_url', '')
        self._rate_limit = self._config.get('notification.rate_limit', 60)
        self._notify_on_error = self._config.get(
            'notification.notify_on_error', True)
        self._notify_on_trade = self._config.get(
            'notification.notify_on_trade', True)

        # 频率控制：记录各类消息最后发送时间
        self._last_sent: Dict[str, float] = {}

        # 检查配置有效性
        if not self._enabled:
            self._logger.info("消息通知功能已禁用 (enabled=false)")
        elif not self._webhook_url:
            self._logger.warning("消息通知功能未配置 Webhook URL，将静默降级")
            self._enabled = False

    def _is_available(self) -> bool:
        """检查通知功能是否可用"""
        return self._enabled and bool(self._webhook_url)

    def _check_rate_limit(self, msg_type: str) -> bool:
        """
        检查同类消息是否超过频率限制

        Args:
            msg_type: 消息类型标识（如 'trade', 'risk', 'error' 等）

        Returns:
            bool: True 表示可以发送，False 表示被限流
        """
        now = time.time()
        last_time = self._last_sent.get(msg_type, 0)

        if now - last_time < self._rate_limit:
            self._logger.debug(
                f"消息被限流: type={msg_type}, "
                f"距上次发送 {now - last_time:.1f}s < {self._rate_limit}s"
            )
            return False

        # 更新最后发送时间
        self._last_sent[msg_type] = now
        return True

    def _send(self, data: Dict[str, Any]) -> bool:
        """
        底层发送方法，处理 HTTP 请求、重试、异常

        Args:
            data: 要发送的消息数据（已符合企业微信 API 格式）

        Returns:
            bool: 发送是否成功
        """
        if not self._is_available():
            return False

        max_retries = 3
        retry_delays = [1, 2, 4]  # 递增重试间隔

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self._webhook_url,
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('errcode') == 0:
                        self._logger.info(
                            f"消息发送成功: type={data.get('msgtype')}"
                        )
                        return True
                    else:
                        self._logger.warning(
                            f"消息发送失败: errcode={result.get('errcode')}, "
                            f"errmsg={result.get('errmsg')}"
                        )
                else:
                    self._logger.warning(
                        f"消息发送失败: HTTP {response.status_code}"
                    )

            except requests.exceptions.Timeout:
                self._logger.warning(
                    f"消息发送超时: attempt={attempt + 1}/{max_retries}"
                )
            except requests.exceptions.RequestException as e:
                self._logger.warning(
                    f"消息发送异常: {type(e).__name__}: {e}, "
                    f"attempt={attempt + 1}/{max_retries}"
                )
            except Exception as e:
                self._logger.error(
                    f"消息发送未知异常: {type(e).__name__}: {e}"
                )
                return False

            # 重试等待
            if attempt < max_retries - 1:
                delay = retry_delays[attempt]
                self._logger.debug(f"等待 {delay}s 后重试...")
                time.sleep(delay)

        self._logger.error(
            f"消息发送失败: 已达到最大重试次数 ({max_retries})"
        )
        return False

    def send_text(
        self,
        content: str,
        mentioned_list: Optional[List[str]] = None
    ) -> bool:
        """
        发送文本消息

        Args:
            content: 消息内容
            mentioned_list: @成员列表（如 ["user1", "@all"]）

        Returns:
            bool: 发送是否成功
        """
        if not self._is_available():
            return False

        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }

        if mentioned_list:
            data["text"]["mentioned_list"] = mentioned_list

        return self._send(data)

    def send_markdown(self, content: str) -> bool:
        """
        发送 Markdown 消息

        Args:
            content: Markdown 格式内容

        Returns:
            bool: 发送是否成功
        """
        if not self._is_available():
            return False

        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

        return self._send(data)

    def send_news(self, articles: List[Dict[str, str]]) -> bool:
        """
        发送图文消息

        Args:
            articles: 图文列表，每项包含 {title, description, url, picurl}

        Returns:
            bool: 发送是否成功
        """
        if not self._is_available():
            return False

        if not articles:
            self._logger.warning("图文消息内容为空，跳过发送")
            return False

        data = {
            "msgtype": "news",
            "news": {
                "articles": articles
            }
        }

        return self._send(data)

    def notify_trade(
        self,
        symbol: str,
        action: str,
        price: float,
        quantity: int,
        **kwargs
    ) -> bool:
        """
        交易信号通知模板

        Args:
            symbol: 股票/交易品种代码
            action: 交易动作 (BUY/SELL 等)
            price: 交易价格
            quantity: 交易数量
            **kwargs: 其他信息（如 strategy, cost, profit 等）

        Returns:
            bool: 发送是否成功
        """
        if not self._notify_on_trade:
            self._logger.debug("交易通知已禁用 (notify_on_trade=false)")
            return False

        if not self._check_rate_limit('trade'):
            return False

        # 构建 Markdown 消息
        action_emoji = "🟢" if action.upper() in ['BUY', '买入'] else "🔴"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        content = f"""### {action_emoji} 交易信号
> **品种**: {symbol}
> **操作**: {action}
> **价格**: {price:.4f}
> **数量**: {quantity}
> **时间**: {timestamp}"""

        # 添加额外信息
        if kwargs:
            extra_lines = '\n'.join(
                f"> **{k}**: {v}" for k, v in kwargs.items())
            content += f"\n{extra_lines}"

        return self.send_markdown(content)

    def notify_risk(
        self,
        risk_type: str,
        message: str,
        **kwargs
    ) -> bool:
        """
        风险告警通知模板

        Args:
            risk_type: 风险类型 (POSITION_LIMIT/DRAWDOWN/VOLATILITY 等)
            message: 风险描述信息
            **kwargs: 其他信息（如 level, threshold, current_value 等）

        Returns:
            bool: 发送是否成功
        """
        if not self._check_rate_limit('risk'):
            return False

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        content = f"""### ⚠️ 风险告警
> **类型**: {risk_type}
> **描述**: {message}
> **时间**: {timestamp}"""

        # 添加额外信息
        if kwargs:
            extra_lines = '\n'.join(
                f"> **{k}**: {v}" for k, v in kwargs.items())
            content += f"\n{extra_lines}"

        return self.send_markdown(content)

    def notify_error(
        self,
        error_msg: str,
        source: Optional[str] = None
    ) -> bool:
        """
        系统异常通知模板

        Args:
            error_msg: 错误信息
            source: 错误来源（模块/函数名）

        Returns:
            bool: 发送是否成功
        """
        if not self._notify_on_error:
            self._logger.debug("错误通知已禁用 (notify_on_error=false)")
            return False

        if not self._check_rate_limit('error'):
            return False

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        content = f"""### 🚨 系统异常
> **来源**: {source or '未知'}
> **错误**: {error_msg}
> **时间**: {timestamp}"""

        return self.send_markdown(content)

    def notify_daily_report(self, report_data: Dict[str, Any]) -> bool:
        """
        每日汇总通知模板

        Args:
            report_data: 汇总数据，支持以下字段：
                - date: 日期
                - total_profit: 总盈亏
                - profit_rate: 收益率
                - trade_count: 交易次数
                - win_rate: 胜率
                - max_drawdown: 最大回撤
                - positions: 持仓列表
                - 其他自定义字段

        Returns:
            bool: 发送是否成功
        """
        if not self._check_rate_limit('daily_report'):
            return False

        date = report_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        total_profit = report_data.get('total_profit', 0)
        profit_rate = report_data.get('profit_rate', 0)
        trade_count = report_data.get('trade_count', 0)
        win_rate = report_data.get('win_rate', 0)
        max_drawdown = report_data.get('max_drawdown', 0)

        # 盈亏颜色
        profit_emoji = "📈" if total_profit >= 0 else "📉"

        content = f"""### {profit_emoji} 每日汇总 ({date})
> **总盈亏**: {total_profit:+.2f}
> **收益率**: {profit_rate:+.2%}
> **交易次数**: {trade_count}
> **胜率**: {win_rate:.2%}
> **最大回撤**: {max_drawdown:.2%}"""

        # 添加持仓信息
        positions = report_data.get('positions', [])
        if positions:
            content += "\n\n**当前持仓**:"
            for pos in positions[:5]:  # 最多显示5个
                symbol = pos.get('symbol', '')
                qty = pos.get('quantity', 0)
                pnl = pos.get('pnl', 0)
                pnl_emoji = "🟢" if pnl >= 0 else "🔴"
                content += f"\n> {pnl_emoji} {symbol}: {qty}股, 盈亏{pnl:+.2f}"

        # 添加其他自定义字段
        excluded_keys = {'date', 'total_profit', 'profit_rate', 'trade_count',
                         'win_rate', 'max_drawdown', 'positions'}
        extra_data = {k: v for k, v in report_data.items()
                      if k not in excluded_keys}
        if extra_data:
            content += "\n"
            for k, v in extra_data.items():
                content += f"\n> **{k}**: {v}"

        return self.send_markdown(content)

    def send_async(
        self,
        send_func: Callable[..., bool],
        *args,
        **kwargs
    ) -> None:
        """
        在后台线程中发送消息，不阻塞主业务

        Args:
            send_func: 发送函数（如 self.send_text, self.notify_trade 等）
            *args: 传递给发送函数的位置参数
            **kwargs: 传递给发送函数的关键字参数
        """
        def _async_send():
            try:
                send_func(*args, **kwargs)
            except Exception as e:
                self._logger.error(
                    f"异步发送消息异常: {type(e).__name__}: {e}"
                )

        thread = threading.Thread(target=_async_send, daemon=True)
        thread.start()


# 全局单例实例
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """
    获取全局 NotificationManager 实例

    Returns:
        NotificationManager: 通知管理器单例实例
    """
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
