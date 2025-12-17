"""
LLM工作流基类
提取各阶段工作流的共同逻辑，提高代码复用性
"""

import json
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from abc import ABC, abstractmethod


class LLMWorkflowBase(ABC):
    """LLM工作流基类 - 提供通用的LLM调用和文件操作功能"""
    
    def __init__(self, auto_load_env: bool = True):
        """
        初始化基类
        
        Args:
            auto_load_env: 是否自动加载环境变量
        """
        if auto_load_env:
            load_dotenv()
        
        # 初始化OpenAI客户端
        self.client = self._init_openai_client()
    
    def _init_openai_client(self) -> OpenAI:
        """初始化OpenAI客户端"""
        return OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.environ.get("OPENAI_BASE_URL")
        )
    
    def load_table_files(
        self,
        table_dir: str,
        table_files: Dict[str, str]
    ) -> Dict[str, str]:
        """
        加载表格文件内容
        
        Args:
            table_dir: 表格目录路径
            table_files: 表格文件映射 {key: filename}
            
        Returns:
            表格内容字典 {key: content}
        """
        tables = {}
        base_dir = Path(table_dir)
        
        for key, filename in table_files.items():
            file_path = base_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    tables[key] = f.read()
            else:
                print(f"警告: 找不到文件 {file_path}")
        
        return tables
    
    def save_json(
        self,
        data: Any,
        filename: str,
        message: Optional[str] = None
    ) -> None:
        """
        保存数据到JSON文件（自动创建目录）
        
        Args:
            data: 要保存的数据
            filename: 文件名（可包含路径）
            message: 保存成功后的提示消息
        """
        # 确保目录存在
        file_path = Path(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if message:
            print(message)
        else:
            print(f"💾 结果已保存到: {filename}")
    
    def load_json(self, filename: str) -> Any:
        """
        从JSON文件加载数据
        
        Args:
            filename: 文件名
            
        Returns:
            加载的数据
        """
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def print_section(self, title: str, width: int = 80, char: str = "=") -> None:
        """
        打印分节标题
        
        Args:
            title: 标题文本
            width: 总宽度
            char: 分隔字符
        """
        print("\n" + char * width)
        print(title)
        print(char * width)


class ToolBasedWorkflow(LLMWorkflowBase):
    """基于工具调用的工作流基类"""
    
    def __init__(self, auto_load_env: bool = True):
        """初始化工作流"""
        super().__init__(auto_load_env)
        self.tools = self.get_tool_definitions()
    
    @abstractmethod
    def get_tool_definitions(self) -> List[Dict]:
        """
        获取工具定义（子类必须实现）
        
        Returns:
            工具定义列表
        """
        pass
    
    @abstractmethod
    def execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        执行工具调用（子类必须实现）
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        pass
    
    def call_llm_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> Any:
        """
        调用LLM（带工具）
        
        Args:
            messages: 消息历史
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            LLM响应
        """
        kwargs = {
            "model": model,
            "messages": messages,
            "tools": self.tools,
            "tool_choice": "auto",
            "temperature": temperature
        }
        
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        
        return self.client.chat.completions.create(**kwargs)
    
    def iterate_llm_with_tools(
        self,
        initial_messages: List[Dict[str, str]],
        max_iterations: int = 20,
        on_tool_call: Optional[callable] = None,
        on_assistant_message: Optional[callable] = None,
        completion_check: Optional[callable] = None,
        model: str = "gpt-4o",
        temperature: float = 0.3
    ) -> tuple[List[Dict], Dict[str, Any]]:
        """
        迭代调用LLM并处理工具调用
        
        Args:
            initial_messages: 初始消息列表
            max_iterations: 最大迭代次数
            on_tool_call: 工具调用回调函数 (tool_name, tool_args, tool_result) -> None
            on_assistant_message: 助手消息回调函数 (message) -> None
            completion_check: 完成检查函数 (messages, iteration) -> bool
            model: 模型名称
            temperature: 温度参数
            
        Returns:
            (messages, metadata) 消息历史和元数据
        """
        messages = initial_messages.copy()
        metadata = {
            "iterations": 0,
            "tool_calls_count": 0,
            "completed": False
        }
        
        for iteration in range(max_iterations):
            metadata["iterations"] = iteration + 1
            
            print(f"\n{'='*80}")
            print(f"迭代 {iteration + 1}/{max_iterations}")
            print(f"{'='*80}")
            
            try:
                # 调用大模型
                response = self.call_llm_with_tools(
                    messages,
                    model=model,
                    temperature=temperature
                )
                
                assistant_message = response.choices[0].message
                
                # 显示助手回复
                if assistant_message.content:
                    print(f"\n🤖 助手: {assistant_message.content[:300]}...")
                    
                    if on_assistant_message:
                        on_assistant_message(assistant_message)
                
                # 添加到消息历史
                messages.append(assistant_message)
                
                # 处理工具调用
                if assistant_message.tool_calls:
                    print(f"\n📞 调用 {len(assistant_message.tool_calls)} 个工具")
                    metadata["tool_calls_count"] += len(assistant_message.tool_calls)
                    
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        print(f"\n🔧 执行工具: {tool_name}")
                        
                        # 执行工具
                        tool_result = self.execute_tool(tool_name, tool_args)
                        
                        # 回调
                        if on_tool_call:
                            on_tool_call(tool_name, tool_args, tool_result)
                        
                        # 将工具结果添加到消息历史
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result, ensure_ascii=False)
                        })
                
                else:
                    # 没有工具调用，检查是否完成
                    if assistant_message.content and ("完成" in assistant_message.content or "结束" in assistant_message.content):
                        print("\n✅ 大模型表示处理完成")
                        metadata["completed"] = True
                        break
                
                # 自定义完成检查
                if completion_check and completion_check(messages, iteration):
                    print("\n✅ 满足完成条件")
                    metadata["completed"] = True
                    break
                    
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                import traceback
                traceback.print_exc()
                metadata["error"] = str(e)
                break
        
        return messages, metadata


class DataLoaderMixin:
    """数据加载混入类 - 提供通用的数据加载功能"""
    
    @staticmethod
    def load_measures_data() -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        加载措施数据（功能安全和信息安全）
        
        Returns:
            措施数据字典
        """
        functional_safety_measures = {
            "设备（切断阀）冗余": {
                "reliability": 0.0099,
                "realtime": -0.25,
                "info_security": -0.0000009
            },
            "内存签名": {
                "reliability": 0.0009,
                "realtime": 0,
                "info_security": 0
            },
            "看门狗": {
                "reliability": 0.0009,
                "realtime": 0,
                "info_security": 0
            },
            "监视": {
                "reliability": 0.0009,
                "realtime": 0,
                "info_security": -0.0000009
            },
            "参考传感器": {
                "reliability": 0.0009,
                "realtime": -0.25,
                "info_security": 0
            },
            "信息冗余": {
                "reliability": 0.0009,
                "realtime": 0,
                "info_security": -0.0000009
            }
        }
        
        information_security_measures = {
            "防火墙": {
                "reliability": 0,
                "realtime": -0.25,
                "info_security": 0.000999
            },
            "加密技术": {
                "reliability": 0,
                "realtime": -0.25,
                "info_security": 0.000009
            },
            "安全更新和补丁": {
                "reliability": 0,
                "realtime": 0,
                "info_security": 0.000009
            },
            "控制系统备份": {
                "reliability": -0.00099,
                "realtime": 0,
                "info_security": 0.000009
            },
            "身份认证技术": {
                "reliability": 0,
                "realtime": -0.25,
                "info_security": 0.000009
            }
        }
        
        return {
            "functional_safety": functional_safety_measures,
            "information_security": information_security_measures
        }


class UserInteractionMixin:
    """用户交互混入类 - 提供通用的用户输入功能"""
    
    @staticmethod
    def get_float_input(
        prompt: str,
        default: Optional[float] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> float:
        """
        获取浮点数输入
        
        Args:
            prompt: 提示文本
            default: 默认值
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            用户输入的浮点数
        """
        while True:
            try:
                user_input = input(prompt).strip()
                
                if user_input == "" and default is not None:
                    return default
                
                value = float(user_input)
                
                if min_value is not None and value < min_value:
                    print(f"  ❌ 值必须 >= {min_value}，请重新输入")
                    continue
                
                if max_value is not None and value > max_value:
                    print(f"  ❌ 值必须 <= {max_value}，请重新输入")
                    continue
                
                return value
                
            except ValueError:
                print("  ❌ 输入无效，请输入一个数字")
    
    @staticmethod
    def get_confirmation(prompt: str, default: bool = True) -> bool:
        """
        获取确认输入
        
        Args:
            prompt: 提示文本
            default: 默认值
            
        Returns:
            用户确认结果
        """
        suffix = " [Y/n]: " if default else " [y/N]: "
        user_input = input(prompt + suffix).strip().lower()
        
        if user_input == "":
            return default
        
        return user_input in ['y', 'yes', '是']


# 导出所有类
__all__ = [
    'LLMWorkflowBase',
    'ToolBasedWorkflow',
    'DataLoaderMixin',
    'UserInteractionMixin'
]

