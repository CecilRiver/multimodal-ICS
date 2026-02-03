"""
ICS安全分析工具集
提供Web搜索、安全要素计算、用户交互等工具
"""

import json
import os
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv


class ICSToolkit:
    """工业控制系统安全分析工具集"""
    
    def __init__(self, tavily_api_key: Optional[str] = None):
        """
        初始化工具集
        
        Args:
            tavily_api_key: Tavily搜索API密钥（可选，如果不提供则从环境变量TAVILY_API_KEY读取）
        """
        load_dotenv()
        self.tavily_api_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
    
    # ==================== 工具1: Web搜索工具 ====================
    
    def web_search(self, query: str, num_results: int = 5, search_depth: str = "basic") -> Dict[str, Any]:
        """
        Web搜索工具 - 使用Tavily Search API
        
        Args:
            query: 搜索查询字符串
            num_results: 返回结果数量，默认5条
            search_depth: 搜索深度，"basic"或"advanced"，默认"basic"
            
        Returns:
            搜索结果字典，包含：
            - success: bool - 是否成功
            - results: List[Dict] - 搜索结果列表
            - error: str - 错误信息（如果失败）
        """
        try:
            # 检查API密钥
            if not self.tavily_api_key:
                return {
                    "success": False,
                    "query": query,
                    "error": "Tavily API密钥未设置。请设置环境变量TAVILY_API_KEY或在初始化时传入tavily_api_key参数",
                    "results": []
                }
            
            # 使用Tavily Search API
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": search_depth,
                "max_results": num_results,
                "include_answer": True,
                "include_raw_content": False,
                "include_images": False
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 解析结果
            results = []
            
            # 处理搜索结果
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0),  # Tavily提供相关性评分
                    "published_date": item.get("published_date", "")
                })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
                "answer": data.get("answer", ""),  # Tavily提供的AI总结答案
                "search_depth": search_depth
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP错误: {e}"
            try:
                error_detail = e.response.json()
                error_msg = f"HTTP错误: {error_detail.get('detail', str(e))}"
            except:
                pass
            return {
                "success": False,
                "query": query,
                "error": error_msg,
                "results": []
            }
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": []
            }
    
    # ==================== 工具2: 信息安全性计算工具 ====================

    import math

    def normalize_value(self,x, zero_decimal_places):
        """
        改变数值大小，使结果满足：
        - 小数点后 zero_decimal_places 个 0
        - 第 zero_decimal_places+1 位为非 0
        """
        if x == 0:
            return 0.0

        # 科学计数法
        exponent = math.floor(math.log10(abs(x)))
        mantissa = x / (10 ** exponent)   # 1 ≤ mantissa < 10

        # 把 mantissa 放到第 zero_decimal_places+1 位
        new_exponent = -zero_decimal_places - 1
        y = mantissa * (10 ** new_exponent)

        return y
    
    def calculate_information_security(self, C: int, I: int, A: int) -> Dict[str, Any]:
        """
        信息安全性要素计算工具
        
        Args:
            C: int - 机密性 (Confidentiality)
            I: int - 完整性 (Integrity)
            A: int - 可用性 (Availability)
            
        Returns:
            计算结果字典，包含：
            - info_security_value: int - 信息安全要素值 (C * I * A)
            - components: Dict - 输入的各要素值
            - formula: str - 计算公式
        """
        try:
            # 计算信息安全要素值
            info_security_value = C * I * A
            # info_security_value = self.normalize_value(info_security_value, 5)
            return {
                "success": True,
                "info_security_value": info_security_value,
                "components": {
                    "confidentiality": C,
                    "integrity": I,
                    "availability": A
                },
                "formula": f"{C} × {I} × {A} = {info_security_value}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== 工具3: 可靠性要素计算工具 ====================
    
    def calculate_reliability(self, P: int, H: int, L: int) -> Dict[str, Any]:
        """
        可靠性要素计算工具
        
        Args:
            P: int - 危险失效平均概率或每小时危险失效平均频率
            H: int - 人因错误 (Human Error)
            L: int - 合规性的等级量化数值 (Legal Compliance)
            
        Returns:
            计算结果字典，包含：
            - reliability_value: int - 可靠性要素值 (P * H * L)
            - components: Dict - 输入的各要素值
            - formula: str - 计算公式
        """
        try:
            # 计算可靠性要素值
            reliability_value = P * H * L
            # reliability_value = self.normalize_value(reliability_value, 3)
            
            return {
                "success": True,
                "reliability_value": reliability_value,
                "components": {
                    "probability": P,
                    "human_error": H,
                    "legal_compliance": L
                },
                "formula": f"{P} × {H} × {L} = {reliability_value}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== 工具4: 与用户交互工具 ====================
    
    def collect_safety_requirements(
        self, 
        safety_functions: List[Dict[str, Any]],
        interactive: bool = True
    ) -> Dict[str, Any]:
        """
        与用户交互收集安全功能要求
        
        Args:
            safety_functions: 安全功能列表，每个包含：
                - id: str - 功能编号
                - description: str - 功能描述
                - actual: Dict - 实际要素值 (reliability, realtime, info_security)
            interactive: bool - 是否交互式输入（默认True）
                            如果False，则返回模板供大模型填充
            
        Returns:
            包含required字段的完整安全功能列表
        """
        try:
            result_functions = []
            
            if interactive:
                print("\n" + "="*80)
                print("安全功能要素值收集")
                print("="*80)
                print("\n请为以下安全功能输入要求的要素值：\n")
                
                for func in safety_functions:
                    print(f"\n{'='*80}")
                    print(f"功能编号: {func['id']}")
                    print(f"功能描述: {func['description']}")
                    print(f"\n当前实际值:")
                    print(f"  - 可靠性: {func['actual']['reliability']}")
                    print(f"  - 实时性: {func['actual']['realtime']}")
                    print(f"  - 信息安全性: {func['actual']['info_security']}")
                    print(f"\n请输入要求值:")
                    
                    # 收集用户输入
                    try:
                        reliability_req = float(input("  可靠性要求 (默认0.001): ") or "0.001")
                        
                        # 实时性要求只能输入特定值
                        allowed_realtime_values = [0, 0.25, 0.5, 0.75, 1]
                        while True:
                            realtime_input = input(f"  实时性要求 (只能输入: 0, 0.25, 0.5, 0.75, 1，默认0.25): ") or "0.25"
                            try:
                                realtime_req = float(realtime_input)
                                if realtime_req in allowed_realtime_values:
                                    break
                                else:
                                    print(f"  ✗ 输入值 {realtime_req} 无效！请输入以下值之一: {', '.join(map(str, allowed_realtime_values))}")
                            except ValueError:
                                print(f"  ✗ 输入格式错误！请输入数字")
                        
                        info_security_req = float(input("  信息安全性要求 (默认1e-5): ") or "1e-5")
                        
                        # 添加required字段
                        func_with_req = func.copy()
                        func_with_req["required"] = {
                            "reliability": reliability_req,
                            "realtime": realtime_req,
                            "info_security": info_security_req
                        }
                        result_functions.append(func_with_req)
                        
                        print(f"✓ 已记录 {func['id']} 的要求值")
                        
                    except ValueError as e:
                        print(f"✗ 输入格式错误，使用默认值")
                        func_with_req = func.copy()
                        func_with_req["required"] = {
                            "reliability": 0.001,
                            "realtime": 0.25,
                            "info_security": 1e-5
                        }
                        result_functions.append(func_with_req)
                
                print(f"\n{'='*80}")
                print("✓ 所有安全功能要求值收集完成")
                print(f"{'='*80}\n")
                
            else:
                # 非交互模式：返回带有默认required的模板
                for func in safety_functions:
                    func_with_req = func.copy()
                    func_with_req["required"] = {
                        "reliability": 0.001,
                        "realtime": 0.25,
                        "info_security": 1e-5
                    }
                    result_functions.append(func_with_req)
            
            return {
                "success": True,
                "safety_functions": result_functions,
                "count": len(result_functions)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== 辅助方法 ====================
    
    def display_safety_functions(self, safety_functions: List[Dict[str, Any]]):
        """
        美化显示安全功能列表
        
        Args:
            safety_functions: 安全功能列表
        """
        print("\n" + "="*80)
        print("安全功能列表")
        print("="*80)
        
        for func in safety_functions:
            print(f"\n【{func['id']}】{func['description']}")
            print(f"\n  实际值:")
            print(f"    可靠性: {func['actual']['reliability']}")
            print(f"    实时性: {func['actual']['realtime']}")
            print(f"    信息安全性: {func['actual']['info_security']}")
            
            if "required" in func:
                print(f"\n  要求值:")
                print(f"    可靠性: {func['required']['reliability']}")
                print(f"    实时性: {func['required']['realtime']}")
                print(f"    信息安全性: {func['required']['info_security']}")
                
                # 判断是否满足要求
                meets_req = (
                    func['actual']['reliability'] >= func['required']['reliability'] and
                    func['actual']['realtime'] >= func['required']['realtime'] and
                    func['actual']['info_security'] >= func['required']['info_security']
                )
                
                status = "✓ 满足要求" if meets_req else "✗ 不满足要求"
                print(f"\n  状态: {status}")
        
        print("\n" + "="*80)
    
    # ==================== 工具定义（用于OpenAI Function Calling）====================
    
    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """
        获取工具定义，用于OpenAI Function Calling
        
        Returns:
            工具定义列表
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "使用Tavily Search在互联网上搜索信息，获取相关资料和文档，并提供AI总结答案",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询字符串，例如：'工业控制系统安全标准'"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "返回结果数量，默认5条",
                                "default": 5
                            },
                            "search_depth": {
                                "type": "string",
                                "description": "搜索深度，'basic'为快速搜索，'advanced'为深度搜索，默认'basic'",
                                "enum": ["basic", "advanced"],
                                "default": "basic"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_information_security",
                    "description": "计算信息安全要素值，公式为 C × I × A（机密性 × 完整性 × 可用性）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "C": {
                                "type": "integer",
                                "description": "机密性 (Confidentiality) 的量化值"
                            },
                            "I": {
                                "type": "integer",
                                "description": "完整性 (Integrity) 的量化值"
                            },
                            "A": {
                                "type": "integer",
                                "description": "可用性 (Availability) 的量化值"
                            }
                        },
                        "required": ["C", "I", "A"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_reliability",
                    "description": "计算可靠性要素值，公式为 P × H × L（失效概率 × 人因错误 × 合规性）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "P": {
                                "type": "integer",
                                "description": "危险失效平均概率或每小时危险失效平均频率"
                            },
                            "H": {
                                "type": "integer",
                                "description": "人因错误 (Human Error) 的量化值"
                            },
                            "L": {
                                "type": "integer",
                                "description": "合规性 (Legal Compliance) 的等级量化数值"
                            }
                        },
                        "required": ["P", "H", "L"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "collect_safety_requirements",
                    "description": "收集用户对安全功能的要素值要求（可靠性、实时性、信息安全性）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "safety_functions": {
                                "type": "array",
                                "description": "安全功能列表",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "description": {"type": "string"},
                                        "actual": {
                                            "type": "object",
                                            "properties": {
                                                "reliability": {"type": "number"},
                                                "realtime": {"type": "number"},
                                                "info_security": {"type": "number"}
                                            }
                                        }
                                    }
                                }
                            },
                            "interactive": {
                                "type": "boolean",
                                "description": "是否交互式输入，默认True",
                                "default": True
                            }
                        },
                        "required": ["safety_functions"]
                    }
                }
            }
        ]


def main():
    """使用示例"""
    
    # 创建工具集实例
    toolkit = ICSToolkit()
    
    print("="*80)
    print("ICS 安全分析工具集 - 使用示例")
    print("="*80)
    
    # ==================== 示例1: Web搜索工具 ====================
    print("\n【示例1】Web搜索工具 (Tavily Search)")
    print("-"*80)
    result = toolkit.web_search("工业控制系统安全", num_results=3)
    print(f"搜索状态: {'成功' if result['success'] else '失败'}")
    if result['success']:
        print(f"搜索关键词: {result['query']}")
        print(f"找到结果数: {result['total_results']}")
        if result.get('answer'):
            print(f"\nAI总结答案: {result['answer'][:200]}...")
        for i, res in enumerate(result['results'], 1):
            print(f"\n结果 {i}:")
            print(f"  标题: {res.get('title', 'N/A')}")
            print(f"  摘要: {res.get('snippet', 'N/A')[:100]}...")
            print(f"  链接: {res.get('url', 'N/A')}")
            print(f"  相关性: {res.get('score', 0):.2f}")
    else:
        print(f"错误: {result.get('error', 'Unknown error')}")
    
    # ==================== 示例2: 信息安全性计算 ====================
    print("\n\n【示例2】信息安全性计算工具")
    print("-"*80)
    result = toolkit.calculate_information_security(C=5, I=4, A=3)
    if result['success']:
        print(f"机密性 (C): {result['components']['confidentiality']}")
        print(f"完整性 (I): {result['components']['integrity']}")
        print(f"可用性 (A): {result['components']['availability']}")
        print(f"计算公式: {result['formula']}")
        print(f"信息安全要素值: {result['info_security_value']}")
    
    # ==================== 示例3: 可靠性要素计算 ====================
    print("\n\n【示例3】可靠性要素计算工具")
    print("-"*80)
    result = toolkit.calculate_reliability(P=2, H=3, L=4)
    if result['success']:
        print(f"失效概率 (P): {result['components']['probability']}")
        print(f"人因错误 (H): {result['components']['human_error']}")
        print(f"合规性 (L): {result['components']['legal_compliance']}")
        print(f"计算公式: {result['formula']}")
        print(f"可靠性要素值: {result['reliability_value']}")
    
    # ==================== 示例4: 用户交互工具（非交互模式）====================
    print("\n\n【示例4】用户交互工具（非交互模式）")
    print("-"*80)
    
    # 示例数据
    sample_data = [
        {
            "id": "F01",
            "description": "保证气站附近发生泄露时，高压切断阀正常关闭；且泄露修复后，高压切断阀正常打开",
            "actual": {
                "reliability": 0.0001,
                "realtime": 1,
                "info_security": 1e-6,
            },
        },
        {
            "id": "F02",
            "description": "保证高压切断阀与中压切断阀间发生泄露时，高压切断阀与中压切断阀均正常关闭",
            "actual": {
                "reliability": 0.0001,
                "realtime": 1,
                "info_security": 1e-6,
            },
        }
    ]
    
    result = toolkit.collect_safety_requirements(sample_data, interactive=True)
    if result['success']:
        print(f"处理了 {result['count']} 个安全功能")
        toolkit.display_safety_functions(result['safety_functions'])
    
    # ==================== 工具定义（用于LLM）====================
    print("\n\n【工具定义】用于OpenAI Function Calling")
    print("-"*80)
    tools = ICSToolkit.get_tool_definitions()
    print(f"共定义 {len(tools)} 个工具:")
    for tool in tools:
        print(f"  - {tool['function']['name']}: {tool['function']['description']}")
    
    print("\n" + "="*80)
    print("示例完成!")
    print("="*80)


if __name__ == "__main__":
    main()

