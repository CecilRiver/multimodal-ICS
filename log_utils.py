"""
日志工具模块
提供同时输出到终端和文件的功能
"""

import sys
import os
from datetime import datetime
from typing import Optional


class TeeOutput:
    """同时输出到终端和文件的类"""
    
    def __init__(self, filename: str, mode: str = 'w'):
        """
        初始化TeeOutput
        
        Args:
            filename: 输出文件路径
            mode: 文件打开模式 ('w'覆盖, 'a'追加)
        """
        self.terminal = sys.stdout
        self.log = open(filename, mode, encoding='utf-8')
    
    def write(self, message):
        """写入消息到终端和文件"""
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()  # 立即刷新到文件
    
    def flush(self):
        """刷新缓冲区"""
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        """关闭文件"""
        self.log.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


def setup_logging(stage_name: str, log_dir: str = "output/logs") -> tuple:
    """
    设置日志记录
    
    Args:
        stage_name: 阶段名称，如 "stage_1", "stage_2", "stage_3"
        log_dir: 日志目录
        
    Returns:
        (log_file, tee, original_stdout) 元组
    """
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 生成日志文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{stage_name}_execution_{timestamp}.log")
    
    # 保存原始stdout
    original_stdout = sys.stdout
    
    # 创建TeeOutput并重定向
    tee = TeeOutput(log_file, mode='w')
    sys.stdout = tee
    
    # 打印日志信息
    print(f"📝 日志文件: {log_file}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return log_file, tee, original_stdout


def teardown_logging(log_file: str, tee: TeeOutput, original_stdout):
    """
    清理日志记录
    
    Args:
        log_file: 日志文件路径
        tee: TeeOutput对象
        original_stdout: 原始stdout
    """
    # 打印结束信息
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📝 完整日志已保存到: {log_file}")
    
    # 恢复标准输出并关闭日志文件
    sys.stdout = original_stdout
    tee.close()
    
    # 在终端显示保存信息
    print(f"\n✅ 日志文件已保存: {log_file}")

