"""配置管理模块

提供 YAML 配置文件的读取、解析和管理功能，支持：
- 单例模式确保全局配置一致性
- 点分隔的嵌套键访问（如 'database.stock_data_db'）
- 环境变量覆盖（QUANT_ 前缀）
- 配置校验（基于 schema 定义）
- 配置变更监听（回调函数）
- 多文件合并（主配置 + 本地配置）
- 配置导出（运行时配置导出为 YAML）
"""

import os
import yaml
from typing import Any, Optional, List, Dict, Callable
import copy


class ConfigManager:
    """
    配置管理器 - 读取 YAML 配置并支持环境变量覆盖

    使用单例模式确保全局配置一致性。

    Example:
        >>> config = ConfigManager()
        >>> config.load()
        >>> db_path = config.get('database.stock_data_db')
        >>> port = config.get('api.port', 8000)
    """

    _instance = None
    _config = None
    _config_path = None
    _extra_paths = None
    _listeners: Dict[str, List[Callable]] = {}

    # 默认配置校验 schema
    DEFAULT_SCHEMA = {
        'database': {
            'type': 'dict',
            'required': True,
            'properties': {
                'stock_data_db': {'type': 'str', 'required': True},
                'trading_system_db': {'type': 'str', 'required': True},
            }
        },
        'data_fetcher': {
            'type': 'dict',
            'required': False,
            'properties': {
                'retry_count': {'type': 'int', 'required': False},
                'retry_delay': {'type': 'int', 'required': False},
                'column_mapping': {'type': 'dict', 'required': False},
            }
        },
        'trading': {
            'type': 'dict',
            'required': False,
            'properties': {
                'commission': {'type': 'dict', 'required': False},
                'slippage': {'type': 'dict', 'required': False},
            }
        },
        'grid_default': {
            'type': 'dict',
            'required': False,
        },
        'api': {
            'type': 'dict',
            'required': True,
            'properties': {
                'host': {'type': 'str', 'required': True},
                'port': {'type': 'int', 'required': True},
                'debug': {'type': 'bool', 'required': False},
                'title': {'type': 'str', 'required': False},
                'version': {'type': 'str', 'required': False},
                'cors_origins': {'type': 'list', 'required': False},
            }
        },
        'logging': {
            'type': 'dict',
            'required': True,
            'properties': {
                'level': {'type': 'str', 'required': True},
                'format': {'type': 'str', 'required': False},
                'console': {'type': 'bool', 'required': False},
                'file': {'type': 'bool', 'required': False},
                'file_path': {'type': 'str', 'required': False},
                'max_size': {'type': 'int', 'required': False},
                'backup_count': {'type': 'int', 'required': False},
            }
        },
        'notification': {
            'type': 'dict',
            'required': False,
            'properties': {
                'enabled': {'type': 'bool', 'required': False},
                'wechat_webhook_url': {'type': 'str', 'required': False},
                'rate_limit': {'type': 'int', 'required': False},
                'notify_on_error': {'type': 'bool', 'required': False},
                'notify_on_trade': {'type': 'bool', 'required': False},
            }
        },
        'scheduler': {
            'type': 'dict',
            'required': False,
            'properties': {
                'enabled': {'type': 'bool', 'required': False},
                'tasks': {'type': 'dict', 'required': False},
            }
        },
    }

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: Optional[str] = None, extra_paths: Optional[List[str]] = None) -> dict:
        """
        加载 YAML 配置文件，支持多文件合并

        Args:
            config_path: 主配置文件路径，默认为 config/config.yaml
            extra_paths: 额外配置文件路径列表，这些配置会覆盖主配置中的同名项
                         如果未指定，会自动检测并加载 config.local.yaml（如果存在）

        Returns:
            dict: 合并后的配置字典

        Raises:
            FileNotFoundError: 主配置文件不存在
            yaml.YAMLError: YAML 解析错误
        """
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))

        if config_path is None:
            config_path = os.path.join(project_root, 'config', 'config.yaml')

        # 处理相对路径
        if not os.path.isabs(config_path):
            config_path = os.path.join(project_root, config_path)

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        # 加载主配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f) or {}

        self._config_path = config_path

        # 处理额外配置文件
        if extra_paths is None:
            # 自动检测 config.local.yaml
            config_dir = os.path.dirname(config_path)
            local_config_path = os.path.join(config_dir, 'config.local.yaml')
            if os.path.exists(local_config_path):
                extra_paths = [local_config_path]
            else:
                extra_paths = []

        self._extra_paths = extra_paths

        # 合并额外配置文件
        for extra_path in extra_paths:
            # 处理相对路径
            if not os.path.isabs(extra_path):
                extra_path = os.path.join(project_root, extra_path)

            if os.path.exists(extra_path):
                with open(extra_path, 'r', encoding='utf-8') as f:
                    extra_config = yaml.safe_load(f) or {}
                self._merge_configs(self._config, extra_config)

        # 应用环境变量覆盖
        self._apply_env_overrides()

        return self._config

    def _merge_configs(self, base: dict, override: dict) -> dict:
        """
        递归合并两个配置字典，override 中的值会覆盖 base 中的同名项

        Args:
            base: 基础配置字典（会被修改）
            override: 覆盖配置字典

        Returns:
            dict: 合并后的配置字典（即修改后的 base）
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # 递归合并嵌套字典
                self._merge_configs(base[key], value)
            else:
                # 直接覆盖
                base[key] = value
        return base

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点分隔的嵌套键

        Args:
            key: 配置键，支持点分隔（如 'database.stock_data_db'）
            default: 默认值，键不存在时返回

        Returns:
            配置值或默认值

        Example:
            >>> config.get('api.port')  # 获取 api 下的 port
            8000
            >>> config.get('database.stock_data_db', 'default.db')
            'data/stock_data.db'
        """
        if self._config is None:
            self.load()

        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default

    def get_section(self, section: str) -> dict:
        """
        获取配置的某个完整节

        Args:
            section: 节名称（如 'database', 'trading'）

        Returns:
            dict: 该节的配置字典，不存在则返回空字典
        """
        if self._config is None:
            self.load()

        return self._config.get(section, {})

    def _apply_env_overrides(self):
        """
        应用环境变量覆盖

        环境变量格式：QUANT_<SECTION>_<KEY>
        例如：QUANT_API_PORT=9000 将覆盖 api.port 的值
        """
        for env_key, env_value in os.environ.items():
            if env_key.startswith('QUANT_'):
                # 移除 QUANT_ 前缀并转换为小写
                config_key = env_key[6:].lower()

                # 将 _ 分隔转换为嵌套结构
                keys = config_key.split('_')

                # 尝试设置配置值
                self._set_nested_value(keys, env_value)

    def _set_nested_value(self, keys: list, value: str):
        """
        设置嵌套配置值

        Args:
            keys: 键列表
            value: 要设置的值（字符串，会尝试转换类型）
        """
        if not keys or self._config is None:
            return

        # 转换值类型
        converted_value = self._convert_value(value)

        # 导航到目标位置
        current = self._config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 设置最终值
        if isinstance(current, dict):
            current[keys[-1]] = converted_value

    def _convert_value(self, value: str) -> Any:
        """
        尝试将字符串值转换为适当的类型

        Args:
            value: 字符串值

        Returns:
            转换后的值
        """
        # 布尔值
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # 整数
        try:
            return int(value)
        except ValueError:
            pass

        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass

        # 保持字符串
        return value

    def reload(self) -> dict:
        """
        重新加载配置文件，并触发变更回调

        Returns:
            dict: 重新加载后的配置字典
        """
        old_config = copy.deepcopy(self._config) if self._config else {}

        if self._config_path:
            self.load(self._config_path, self._extra_paths)
        else:
            self.load()

        # 触发变更回调
        self._notify_changes(old_config, self._config)

        return self._config

    def on_change(self, key: str, callback: Callable[[Any, Any], None]) -> None:
        """
        注册配置变更回调函数

        当指定的配置键发生变化时，回调函数会被调用。

        Args:
            key: 要监听的配置键，支持点分隔（如 'database.stock_data_db'）
                 使用 '*' 监听所有顶级配置节的变化
            callback: 回调函数，接收两个参数 (old_value, new_value)

        Example:
            >>> def on_port_change(old_val, new_val):
            ...     print(f"端口从 {old_val} 变更为 {new_val}")
            >>> config.on_change('api.port', on_port_change)
        """
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

    def _notify_changes(self, old_config: dict, new_config: dict) -> None:
        """
        对比配置差异并触发相应的回调函数

        Args:
            old_config: 旧配置字典
            new_config: 新配置字典
        """
        if not self._listeners:
            return

        # 检查每个监听的键
        for key, callbacks in self._listeners.items():
            if key == '*':
                # 监听所有顶级配置节的变化
                all_keys = set(old_config.keys()) | set(new_config.keys())
                for top_key in all_keys:
                    old_val = old_config.get(top_key)
                    new_val = new_config.get(top_key)
                    if old_val != new_val:
                        for callback in callbacks:
                            try:
                                callback(old_val, new_val)
                            except Exception:
                                pass  # 忽略回调中的异常
            else:
                old_val = self._get_nested_value(old_config, key)
                new_val = self._get_nested_value(new_config, key)
                if old_val != new_val:
                    for callback in callbacks:
                        try:
                            callback(old_val, new_val)
                        except Exception:
                            pass  # 忽略回调中的异常

    def _get_nested_value(self, config: dict, key: str) -> Any:
        """
        从配置字典中获取嵌套键的值

        Args:
            config: 配置字典
            key: 点分隔的键

        Returns:
            键对应的值，不存在则返回 None
        """
        keys = key.split('.')
        value = config
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    return None
            return value
        except (KeyError, TypeError):
            return None

    def validate(self, schema: Optional[dict] = None) -> List[Dict[str, str]]:
        """
        基于 schema 定义验证配置项类型和必填项

        Args:
            schema: 校验 schema 字典，默认使用 DEFAULT_SCHEMA
                    格式: {
                        'section_name': {
                            'type': 'dict',  # str/int/float/bool/list/dict
                            'required': True,
                            'properties': {
                                'key': {'type': 'str', 'required': True},
                            }
                        }
                    }

        Returns:
            List[Dict]: 校验结果列表，每项包含 {'key': str, 'error': str}
                        空列表表示校验通过

        Example:
            >>> errors = config.validate()
            >>> if errors:
            ...     for err in errors:
            ...         print(f"{err['key']}: {err['error']}")
        """
        if self._config is None:
            self.load()

        if schema is None:
            schema = self.DEFAULT_SCHEMA

        errors = []
        self._validate_section(self._config, schema, '', errors)
        return errors

    def _validate_section(self, config: dict, schema: dict, prefix: str, errors: List[Dict[str, str]]) -> None:
        """
        递归校验配置节

        Args:
            config: 当前配置字典
            schema: 当前 schema 字典
            prefix: 当前键前缀
            errors: 错误列表（会被修改）
        """
        type_map = {
            'str': str,
            'int': int,
            'float': (int, float),
            'bool': bool,
            'list': list,
            'dict': dict,
        }

        for key, rules in schema.items():
            full_key = f"{prefix}.{key}" if prefix else key
            value = config.get(key) if config else None

            # 检查必填项
            if rules.get('required', False) and value is None:
                errors.append({'key': full_key, 'error': '必填项缺失'})
                continue

            if value is None:
                continue

            # 检查类型
            expected_type = rules.get('type')
            if expected_type and expected_type in type_map:
                if not isinstance(value, type_map[expected_type]):
                    errors.append({
                        'key': full_key,
                        'error': f'类型错误，期望 {expected_type}，实际为 {type(value).__name__}'
                    })
                    continue

            # 递归校验嵌套属性
            if rules.get('type') == 'dict' and 'properties' in rules and isinstance(value, dict):
                self._validate_section(
                    value, rules['properties'], full_key, errors)

    def export(self, output_path: str, include_env: bool = False) -> None:
        """
        导出当前运行时配置为 YAML 文件

        Args:
            output_path: 输出文件路径
            include_env: 是否包含环境变量覆盖的值（默认已包含，此参数用于标记）

        Raises:
            ValueError: 配置尚未加载

        Example:
            >>> config.export('config/config.backup.yaml')
            >>> config.export('config/config.full.yaml', include_env=True)
        """
        if self._config is None:
            raise ValueError("配置尚未加载，请先调用 load() 方法")

        # 处理相对路径
        if not os.path.isabs(output_path):
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))
            output_path = os.path.join(project_root, output_path)

        # 确保目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 导出配置
        config_to_export = copy.deepcopy(self._config)

        # 添加导出元信息（作为注释）
        header = "# 运行时配置导出\n"
        header += f"# 导出自: {self._config_path}\n"
        if self._extra_paths:
            header += f"# 额外配置: {', '.join(self._extra_paths)}\n"
        if include_env:
            header += "# 包含环境变量覆盖\n"
        header += "\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(header)
            yaml.dump(
                config_to_export,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )

    @property
    def config(self) -> dict:
        """获取完整配置字典"""
        if self._config is None:
            self.load()
        return self._config

    def __repr__(self) -> str:
        return f"<ConfigManager(path={self._config_path}, loaded={self._config is not None})>"


# 便捷函数
def get_config() -> ConfigManager:
    """
    获取 ConfigManager 单例实例

    Returns:
        ConfigManager: 配置管理器实例
    """
    return ConfigManager()
