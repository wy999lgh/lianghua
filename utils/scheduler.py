"""
任务调度模块

使用 schedule 库实现定时任务调度，支持：
- 任务注册/取消注册
- 多种调度表达式（每天、每小时、每分钟、每周等）
- 任务执行包装（日志、异常捕获、失败通知）
- 后台线程运行
- 任务状态查询
- 内置常用任务
"""

import threading
import time
import re
from datetime import datetime
from typing import Optional, Callable, Dict, Any

# schedule 库依赖处理
try:
    import schedule
except ImportError:
    schedule = None
    _schedule_import_error = (
        "schedule 库未安装，请执行: pip install schedule\n"
        "任务调度功能将被禁用。"
    )

from utils.logger import get_logger
from utils.notification import get_notification_manager
from utils.config_manager import get_config


class TaskScheduler:
    """任务调度管理器"""

    def __init__(self):
        """
        初始化任务调度器

        从 ConfigManager 读取 scheduler 配置：
        - enabled: 是否启用调度器
        - tasks: 内置任务配置
        """
        self._logger = get_logger('scheduler')
        self._config = get_config()
        self._notification = get_notification_manager()

        # 检查 schedule 库是否可用
        if schedule is None:
            self._logger.warning(_schedule_import_error)
            self._enabled = False
        else:
            self._enabled = self._config.get('scheduler.enabled', False)

        # 任务注册表
        # {name: {func, schedule_str, enabled, job, last_run, next_run, last_status, run_count, error_count}}
        self._tasks: Dict[str, Dict[str, Any]] = {}

        # 调度器状态
        self._running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        if not self._enabled:
            self._logger.info("任务调度器已禁用 (enabled=false)")
        else:
            self._logger.info("任务调度器初始化完成")

    def register_task(
        self,
        name: str,
        func: Callable,
        schedule_str: str,
        enabled: bool = True
    ) -> bool:
        """
        注册定时任务

        Args:
            name: 任务名称
            func: 可调用对象
            schedule_str: 调度表达式，如 "every day at 18:00", "every 5 minutes", "every hour"
            enabled: 是否启用

        Returns:
            bool: 注册是否成功
        """
        if schedule is None:
            self._logger.error(f"无法注册任务 '{name}': schedule 库未安装")
            return False

        if name in self._tasks:
            self._logger.warning(f"任务 '{name}' 已存在，将被覆盖")
            self.unregister_task(name)

        # 解析调度表达式
        job = self._parse_schedule(schedule_str)
        if job is None:
            self._logger.error(f"无法解析调度表达式: '{schedule_str}'")
            return False

        # 包装任务函数
        wrapped_func = self._task_wrapper(name, func)

        # 设置任务执行函数
        job.do(wrapped_func)

        # 如果禁用任务，取消 job 的标签以便后续控制
        if not enabled:
            job.tag(f"disabled_{name}")
        else:
            job.tag(name)

        # 注册到任务表
        self._tasks[name] = {
            'func': func,
            'schedule_str': schedule_str,
            'enabled': enabled,
            'job': job,
            'last_run': None,
            'next_run': job.next_run if enabled else None,
            'last_status': 'pending',
            'run_count': 0,
            'error_count': 0,
        }

        self._logger.info(
            f"任务注册成功: name={name}, schedule='{schedule_str}', enabled={enabled}"
        )
        return True

    def unregister_task(self, name: str) -> bool:
        """
        取消注册任务

        Args:
            name: 任务名称

        Returns:
            bool: 取消是否成功
        """
        if name not in self._tasks:
            self._logger.warning(f"任务 '{name}' 不存在")
            return False

        task_info = self._tasks[name]
        job = task_info.get('job')

        if job and schedule is not None:
            schedule.cancel_job(job)

        del self._tasks[name]
        self._logger.info(f"任务已取消注册: {name}")
        return True

    def _parse_schedule(self, schedule_str: str) -> Optional[Any]:
        """
        解析调度表达式，返回 schedule.Job 对象

        支持的格式：
        - "every day at HH:MM"
        - "every N minutes"
        - "every N hours"
        - "every hour"
        - "every minute"
        - "every N seconds"
        - "every monday at HH:MM" 等星期

        Args:
            schedule_str: 调度表达式字符串

        Returns:
            schedule.Job 对象，解析失败返回 None
        """
        if schedule is None:
            return None

        schedule_str = schedule_str.strip().lower()

        try:
            # "every day at HH:MM"
            match = re.match(
                r'^every\s+day\s+at\s+(\d{1,2}:\d{2})$', schedule_str)
            if match:
                time_str = match.group(1)
                return schedule.every().day.at(time_str)

            # "every N minutes"
            match = re.match(r'^every\s+(\d+)\s+minutes?$', schedule_str)
            if match:
                minutes = int(match.group(1))
                return schedule.every(minutes).minutes

            # "every minute"
            if schedule_str == 'every minute':
                return schedule.every().minute

            # "every N hours"
            match = re.match(r'^every\s+(\d+)\s+hours?$', schedule_str)
            if match:
                hours = int(match.group(1))
                return schedule.every(hours).hours

            # "every hour"
            if schedule_str == 'every hour':
                return schedule.every().hour

            # "every N seconds"
            match = re.match(r'^every\s+(\d+)\s+seconds?$', schedule_str)
            if match:
                seconds = int(match.group(1))
                return schedule.every(seconds).seconds

            # "every second"
            if schedule_str == 'every second':
                return schedule.every().second

            # 星期几 at HH:MM
            weekday_map = {
                'monday': schedule.every().monday,
                'tuesday': schedule.every().tuesday,
                'wednesday': schedule.every().wednesday,
                'thursday': schedule.every().thursday,
                'friday': schedule.every().friday,
                'saturday': schedule.every().saturday,
                'sunday': schedule.every().sunday,
            }

            for weekday, job_func in weekday_map.items():
                match = re.match(
                    rf'^every\s+{weekday}\s+at\s+(\d{{1,2}}:\d{{2}})$', schedule_str)
                if match:
                    time_str = match.group(1)
                    return job_func.at(time_str)

            self._logger.warning(f"无法识别的调度表达式: '{schedule_str}'")
            return None

        except Exception as e:
            self._logger.error(f"解析调度表达式异常: {e}")
            return None

    def _task_wrapper(self, name: str, func: Callable) -> Callable:
        """
        任务执行包装器：记录日志、捕获异常、失败通知

        Args:
            name: 任务名称
            func: 原始任务函数

        Returns:
            包装后的函数
        """
        def wrapped():
            task_info = self._tasks.get(name)
            if not task_info:
                return

            # 检查任务是否启用
            if not task_info.get('enabled', True):
                return

            start_time = datetime.now()
            self._logger.info(
                f"[任务开始] {name} @ {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

            try:
                func()

                # 更新任务状态
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                task_info['last_run'] = end_time
                task_info['last_status'] = 'success'
                task_info['run_count'] = task_info.get('run_count', 0) + 1

                # 更新下次运行时间
                job = task_info.get('job')
                if job:
                    task_info['next_run'] = job.next_run

                self._logger.info(
                    f"[任务完成] {name} | 耗时: {duration:.2f}s"
                )

            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # 更新任务状态
                task_info['last_run'] = end_time
                task_info['last_status'] = f'error: {str(e)}'
                task_info['run_count'] = task_info.get('run_count', 0) + 1
                task_info['error_count'] = task_info.get('error_count', 0) + 1

                # 更新下次运行时间
                job = task_info.get('job')
                if job:
                    task_info['next_run'] = job.next_run

                self._logger.exception(
                    f"[任务失败] {name} | 耗时: {duration:.2f}s | 错误: {e}"
                )

                # 发送通知
                try:
                    self._notification.notify_error(
                        error_msg=str(e),
                        source=f"定时任务: {name}"
                    )
                except Exception as notify_err:
                    self._logger.warning(f"发送任务失败通知时出错: {notify_err}")

        return wrapped

    def start(self) -> bool:
        """
        在后台线程中启动调度器

        Returns:
            bool: 启动是否成功
        """
        if not self._enabled:
            self._logger.info("调度器未启用，start() 直接返回")
            return False

        if schedule is None:
            self._logger.error("schedule 库未安装，无法启动调度器")
            return False

        if self._running:
            self._logger.warning("调度器已在运行中")
            return False

        self._stop_event.clear()
        self._running = True

        self._thread = threading.Thread(
            target=self._run_loop,
            name="TaskScheduler",
            daemon=True
        )
        self._thread.start()

        self._logger.info("任务调度器已启动")
        return True

    def stop(self) -> bool:
        """
        停止调度器

        Returns:
            bool: 停止是否成功
        """
        if not self._running:
            self._logger.warning("调度器未在运行")
            return False

        self._stop_event.set()
        self._running = False

        # 等待线程结束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        self._logger.info("任务调度器已停止")
        return True

    def _run_loop(self):
        """调度循环（在后台线程中运行）"""
        self._logger.debug("调度循环开始")

        while not self._stop_event.is_set():
            try:
                schedule.run_pending()
            except Exception as e:
                self._logger.error(f"调度循环异常: {e}")

            # 每秒检查一次
            self._stop_event.wait(timeout=1)

        self._logger.debug("调度循环结束")

    def get_task_status(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            name: 任务名称，为 None 时返回所有任务状态

        Returns:
            dict: {name: {enabled, schedule, last_run, next_run, last_status, run_count, error_count}}
        """
        if name is not None:
            task_info = self._tasks.get(name)
            if not task_info:
                return {}

            return {
                name: {
                    'enabled': task_info.get('enabled', False),
                    'schedule': task_info.get('schedule_str', ''),
                    'last_run': task_info.get('last_run'),
                    'next_run': task_info.get('next_run'),
                    'last_status': task_info.get('last_status', 'pending'),
                    'run_count': task_info.get('run_count', 0),
                    'error_count': task_info.get('error_count', 0),
                }
            }

        # 返回所有任务状态
        result = {}
        for task_name, task_info in self._tasks.items():
            result[task_name] = {
                'enabled': task_info.get('enabled', False),
                'schedule': task_info.get('schedule_str', ''),
                'last_run': task_info.get('last_run'),
                'next_run': task_info.get('next_run'),
                'last_status': task_info.get('last_status', 'pending'),
                'run_count': task_info.get('run_count', 0),
                'error_count': task_info.get('error_count', 0),
            }
        return result

    def list_tasks(self) -> list:
        """
        列出所有已注册任务

        Returns:
            list: 任务名称列表
        """
        return list(self._tasks.keys())

    def register_builtin_tasks(self):
        """
        注册内置的常用任务

        从 config.yaml 的 scheduler.tasks 读取调度时间和启用状态
        """
        tasks_config = self._config.get('scheduler.tasks', {})

        # update_stock_data - 数据更新任务
        update_config = tasks_config.get('update_stock_data', {})
        update_schedule = update_config.get('schedule', 'every day at 18:00')
        update_enabled = update_config.get('enabled', True)

        self.register_task(
            name='update_stock_data',
            func=self._builtin_update_stock_data,
            schedule_str=update_schedule,
            enabled=update_enabled
        )

        # daily_report - 日报推送任务
        report_config = tasks_config.get('daily_report', {})
        report_schedule = report_config.get('schedule', 'every day at 20:00')
        report_enabled = report_config.get('enabled', True)

        self.register_task(
            name='daily_report',
            func=self._builtin_daily_report,
            schedule_str=report_schedule,
            enabled=report_enabled
        )

        self._logger.info(f"内置任务注册完成: {self.list_tasks()}")

    def _builtin_update_stock_data(self):
        """
        内置任务：数据更新

        占位实现，记录日志，后续可对接实际业务逻辑
        """
        self._logger.info("[内置任务] update_stock_data - 开始执行数据更新...")
        # TODO: 对接实际的数据更新逻辑
        # 例如: from core.data import DataFetcher; DataFetcher().update_all()
        self._logger.info("[内置任务] update_stock_data - 数据更新完成（占位实现）")

    def _builtin_daily_report(self):
        """
        内置任务：日报推送

        通过 NotificationManager 发送汇总，占位实现
        """
        self._logger.info("[内置任务] daily_report - 开始生成日报...")

        # 构建汇总数据（占位）
        report_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_profit': 0.0,
            'profit_rate': 0.0,
            'trade_count': 0,
            'win_rate': 0.0,
            'max_drawdown': 0.0,
            'note': '这是一条占位日报，后续将对接实际业务数据'
        }

        # 发送日报通知
        try:
            self._notification.notify_daily_report(report_data)
            self._logger.info("[内置任务] daily_report - 日报推送完成")
        except Exception as e:
            self._logger.warning(f"[内置任务] daily_report - 日报推送失败: {e}")

    @property
    def is_running(self) -> bool:
        """调度器是否正在运行"""
        return self._running

    @property
    def is_enabled(self) -> bool:
        """调度器是否启用"""
        return self._enabled


# 全局单例实例
_task_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """
    获取全局 TaskScheduler 实例

    Returns:
        TaskScheduler: 任务调度器单例实例
    """
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
    return _task_scheduler
