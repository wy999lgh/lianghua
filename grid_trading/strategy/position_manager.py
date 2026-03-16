class PositionManager:
    """
    持仓管理类
    
    功能：
    - 最大持仓限制：超过时暂停买入
    - 最小底仓限制：低于时暂停卖出
    - 恢复条件：回到范围内恢复正常交易
    - 持仓状态监控
    """
    
    def __init__(self, max_position, min_position):
        """
        初始化持仓管理器
        
        参数：
        max_position: int - 最大持仓数量
        min_position: int - 最小底仓数量
        """
        self.max_position = max_position
        self.min_position = min_position
        self.current_position = min_position  # 初始持仓为最小底仓
        self.position_status = 'normal'  # 持仓状态：normal, max_reached, min_reached
    
    def update_position(self, amount, direction):
        """
        更新持仓数量
        
        参数：
        amount: int - 交易数量
        direction: str - 交易方向，'buy'或'sell'
        
        返回：
        dict - 包含更新结果的字典
        """
        if direction == 'buy':
            # 检查是否达到最大持仓
            if self.current_position + amount > self.max_position:
                return {
                    'success': False,
                    'reason': 'max_position_exceeded',
                    'message': f'当前持仓 {self.current_position}，加上买入 {amount} 会超过最大持仓 {self.max_position}',
                    'current_position': self.current_position
                }
            
            # 更新持仓
            self.current_position += amount
            
            # 更新持仓状态
            if self.current_position >= self.max_position:
                self.position_status = 'max_reached'
            else:
                self.position_status = 'normal'
                
        elif direction == 'sell':
            # 检查是否低于最小底仓
            if self.current_position - amount < self.min_position:
                return {
                    'success': False,
                    'reason': 'min_position_violation',
                    'message': f'当前持仓 {self.current_position}，减去卖出 {amount} 会低于最小底仓 {self.min_position}',
                    'current_position': self.current_position
                }
            
            # 更新持仓
            self.current_position -= amount
            
            # 更新持仓状态
            if self.current_position <= self.min_position:
                self.position_status = 'min_reached'
            else:
                self.position_status = 'normal'
        
        return {
            'success': True,
            'current_position': self.current_position,
            'position_status': self.position_status
        }
    
    def check_position(self, direction, amount):
        """
        检查持仓是否允许交易
        
        参数：
        direction: str - 交易方向，'buy'或'sell'
        amount: int - 交易数量
        
        返回：
        bool - 是否允许交易
        """
        if direction == 'buy':
            return self.current_position + amount <= self.max_position
        elif direction == 'sell':
            return self.current_position - amount >= self.min_position
        return False
    
    def get_position(self):
        """
        获取当前持仓
        
        返回：
        int - 当前持仓数量
        """
        return self.current_position
    
    def get_position_status(self):
        """
        获取持仓状态
        
        返回：
        str - 持仓状态
        """
        return self.position_status
    
    def is_max_position_reached(self):
        """
        检查是否达到最大持仓
        
        返回：
        bool - 是否已达到最大持仓
        """
        return self.current_position >= self.max_position
    
    def is_min_position_reached(self):
        """
        检查是否达到最小持仓
        
        返回：
        bool - 是否已达到最小持仓
        """
        return self.current_position <= self.min_position
    
    def reset_position(self):
        """
        重置持仓到最小底仓
        """
        self.current_position = self.min_position
        self.position_status = 'normal'
    
    def update_limits(self, max_position=None, min_position=None):
        """
        更新持仓限制
        
        参数：
        max_position: int - 新的最大持仓数量
        min_position: int - 新的最小底仓数量
        """
        if max_position is not None:
            self.max_position = max_position
        
        if min_position is not None:
            self.min_position = min_position
            # 确保当前持仓不低于新的最小底仓
            self.current_position = max(self.current_position, min_position)
        
        # 更新持仓状态
        if self.current_position >= self.max_position:
            self.position_status = 'max_reached'
        elif self.current_position <= self.min_position:
            self.position_status = 'min_reached'
        else:
            self.position_status = 'normal'

class BasePriceManager:
    """
    基准价管理类
    
    功能：
    - 触发价更新：以触发委托的价格更新基准价
    - 成交价更新：以实际成交价格更新基准价
    - 部分成交处理：未全部成交时基准价不更新
    - 基准价状态监控
    - 交易驱动更新：仅在交易成功执行后更新基准价
    """
    
    def __init__(self, initial_base_price, update_method='trigger_price'):
        """
        初始化基准价管理器
        
        参数：
        initial_base_price: float - 初始基准价
        update_method: str - 基准价更新方式，'trigger_price'或'execution_price'
        """
        self.base_price = initial_base_price
        self.update_method = update_method
        self.last_update_time = None
        self.last_update_price = None
        self.update_history = []  # 基准价更新历史
    
    def update_base_price(self, price, is_partial=False):
        """
        更新基准价
        
        参数：
        price: float - 新的基准价
        is_partial: bool - 是否为部分成交
        
        返回：
        dict - 包含更新结果的字典
        """
        # 部分成交时不更新基准价
        if is_partial:
            return {
                'success': False,
                'reason': 'partial_execution',
                'message': '部分成交，基准价不更新',
                'current_base_price': self.base_price
            }
        
        # 更新基准价
        old_base_price = self.base_price
        self.base_price = price
        self.last_update_price = price
        self.last_update_time = None  # 可以在这里添加时间戳
        
        # 记录更新历史
        update_record = {
            'timestamp': None,  # 可以在这里添加时间戳
            'old_base_price': old_base_price,
            'new_base_price': self.base_price,
            'update_method': self.update_method
        }
        self.update_history.append(update_record)
        
        return {
            'success': True,
            'old_base_price': old_base_price,
            'new_base_price': self.base_price,
            'update_method': self.update_method,
            'message': f'基准价已更新：{old_base_price} → {self.base_price}'
        }
    
    def get_base_price(self):
        """
        获取当前基准价
        
        返回：
        float - 当前基准价
        """
        return self.base_price
    
    def get_update_method(self):
        """
        获取基准价更新方式
        
        返回：
        str - 基准价更新方式
        """
        return self.update_method
    
    def reset_base_price(self, initial_base_price):
        """
        重置基准价
        
        参数：
        initial_base_price: float - 新的初始基准价
        """
        self.base_price = initial_base_price
        self.last_update_price = None
        self.last_update_time = None
        self.update_history = []
    
    def get_update_history(self):
        """
        获取基准价更新历史
        
        返回：
        list - 更新历史记录
        """
        return self.update_history
    
    def update_update_method(self, method):
        """
        更新基准价更新方式
        
        参数：
        method: str - 新的更新方式，'trigger_price'或'execution_price'
        """
        if method in ['trigger_price', 'execution_price']:
            self.update_method = method
            return True
        return False

# 测试代码
if __name__ == "__main__":
    # 测试持仓管理器
    print("=== 测试持仓管理器 ===")
    position_manager = PositionManager(max_position=10000, min_position=1000)
    
    # 测试正常买入
    result = position_manager.update_position(1000, 'buy')
    print(f"正常买入 1000: {result}")
    
    # 测试达到最大持仓
    result = position_manager.update_position(9000, 'buy')
    print(f"买入 9000 达到最大持仓: {result}")
    
    # 测试超过最大持仓
    result = position_manager.update_position(1000, 'buy')
    print(f"尝试超过最大持仓: {result}")
    
    # 测试正常卖出
    result = position_manager.update_position(1000, 'sell')
    print(f"正常卖出 1000: {result}")
    
    # 测试达到最小持仓
    result = position_manager.update_position(8000, 'sell')
    print(f"卖出 8000 达到最小持仓: {result}")
    
    # 测试低于最小持仓
    result = position_manager.update_position(1000, 'sell')
    print(f"尝试低于最小持仓: {result}")
    
    # 测试基准价管理器
    print("\n=== 测试基准价管理器 ====")
    base_price_manager = BasePriceManager(initial_base_price=2.8, update_method='trigger_price')
    
    # 测试正常更新
    result = base_price_manager.update_base_price(2.85)
    print(f"正常更新基准价: {result}")
    
    # 测试部分成交
    result = base_price_manager.update_base_price(2.9, is_partial=True)
    print(f"部分成交更新基准价: {result}")
    
    # 测试重置基准价
    base_price_manager.reset_base_price(2.7)
    print(f"重置基准价后: {base_price_manager.get_base_price()}")
    
    # 测试更新方式
    result = base_price_manager.update_update_method('execution_price')
    print(f"更新基准价更新方式: {result}")
    print(f"当前更新方式: {base_price_manager.get_update_method()}")
    
    # 测试更新历史
    print(f"基准价更新历史: {base_price_manager.get_update_history()}")
