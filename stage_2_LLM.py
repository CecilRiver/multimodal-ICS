"""
安全功能要素值计算工作流（重构版）
使用大模型自动调用工具计算安全功能的信息安全性、可靠性和实时性要素值
"""

import json
from typing import List, Dict, Any
from ics_tools import ICSToolkit
from llm_workflow_base import ToolBasedWorkflow


class SafetyFunctionWorkflow(ToolBasedWorkflow):
    """安全功能要素值计算工作流"""
    
    def __init__(self):
        """初始化工作流"""
        super().__init__()
        
        # 初始化工具集
        self.toolkit = ICSToolkit()
        
        # 加载量化表
        self.quantization_tables = self.load_table_files(
            table_dir="input_data/tables/stage 2",
            table_files={
                "info_security": "表 6 信息安全要素的等级描述与数值量化表.md",
                "reliability": "表 7 可靠性要素的等级描述与数值量化表.md",
                "realtime": "表 8 实时性要素的等级描述与数值量化表.md"
            }
        )
    
    def get_tool_definitions(self) -> List[Dict]:
        """获取工具定义"""
        return ICSToolkit.get_tool_definitions()
    
    def execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """执行工具调用"""
        print(f"📝 参数: {json.dumps(arguments, ensure_ascii=False, indent=2)}")
        
        if tool_name == "web_search":
            result = self.toolkit.web_search(**arguments)
        elif tool_name == "calculate_information_security":
            result = self.toolkit.calculate_information_security(**arguments)
        elif tool_name == "calculate_reliability":
            result = self.toolkit.calculate_reliability(**arguments)
        elif tool_name == "collect_safety_requirements":
            result = self.toolkit.collect_safety_requirements(**arguments)
        else:
            result = {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        print(f"✅ 执行完成")
        return result
    
    def calculate_safety_function_values(
        self, 
        safety_functions: List[Dict[str, Any]],
        max_iterations: int = 30
    ) -> List[Dict[str, Any]]:
        """
        计算安全功能的要素值
        
        Args:
            safety_functions: 安全功能列表
            max_iterations: 最大迭代次数
            
        Returns:
            包含actual值的安全功能列表
        """
        self.print_section("开始计算安全功能要素值")
        
        # 构建系统提示词
        system_prompt = f"""你是一个工业控制系统(ICS)安全分析专家。

你需要为每个安全功能计算三个要素值：信息安全性、可靠性和实时性。

**量化表参考**：

### 信息安全要素量化表
{self.quantization_tables.get('info_security', '')}

### 可靠性要素量化表
{self.quantization_tables.get('reliability', '')}

### 实时性要素量化表
{self.quantization_tables.get('realtime', '')}

**工作流程**：
对于每个安全功能，你需要：

1. **搜索相关知识**：
   - 使用web_search工具搜索该安全功能相关的标准、最佳实践
   - 搜索关键词应包含：功能描述、相关标准(如IEC 61508, IEC 62443)、安全要求

2. **计算信息安全性要素值**：
   - 根据搜索到的知识和功能描述，从量化表中确定机密性(C)、完整性(I)、可用性(A)的数值,请注意C、I、A的定级绝大部分为中，极少数情况下会达到较高，请根据实际情况进行选择
   - 使用calculate_information_security工具计算：info_security

3. **计算可靠性要素值**：
   - 根据搜索到的知识和功能描述，从量化表中确定：
     * P: 危险失效平均概率(SIL等级)
     * H: 人因错误等级
     * L: 合规性(0或1)
   - 使用calculate_reliability工具计算：reliability 

4. **确定实时性要素值**：
   - 根据功能描述和响应时间要求，从量化表中确定响应时间的数值量化值
   - 该值即为realtime的值(范围0-1)

**重要提示**：
- 每个安全功能都要独立分析和搜索
- 严格按照量化表中的数值进行选择
- 燃气管网系统是高危系统，安全要求通常较高
- 切断阀的响应时间通常要求快速(1-2秒内)
- 请依次处理每个安全功能，不要跳过

当所有安全功能都计算完成后，请明确告诉我"所有安全功能计算完成"。
"""
        
        # 构建用户消息
        functions_description = "\n\n".join([
            f"**安全功能 {func['id']}**:\n"
            f"- 描述: {func['description']}\n"
            f"- 组件集: {func.get('element_id_set', 'N/A')}\n"
            f"- 风险集: {func.get('risk_id_set', 'N/A')}"
            for func in safety_functions
        ])
        
        user_message = f"""请为以下安全功能计算要素值：

{functions_description}

请依次为每个安全功能：
1. 搜索相关知识
2. 计算信息安全性要素值
3. 计算可靠性要素值
4. 确定实时性要素值

开始处理第一个安全功能 {safety_functions[0]['id']}。
"""
        
        # 初始化消息
        initial_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # 存储计算结果
        results = {func['id']: {} for func in safety_functions}
        
        # 定义工具调用回调
        def on_tool_call(tool_name, tool_args, tool_result):
            # 保存计算结果
            if tool_name == "calculate_information_security" and tool_result.get('success'):
                for func_id in results.keys():
                    if 'info_security' not in results[func_id]:
                        results[func_id]['info_security'] = tool_result['info_security_value']
                        print(f"  💾 保存 {func_id} 的信息安全性值: {tool_result['info_security_value']}")
                        break
            
            elif tool_name == "calculate_reliability" and tool_result.get('success'):
                for func_id in results.keys():
                    if 'reliability' not in results[func_id]:
                        results[func_id]['reliability'] = tool_result['reliability_value']
                        print(f"  💾 保存 {func_id} 的可靠性值: {tool_result['reliability_value']}")
                        break
        
        # 定义完成检查
        def completion_check(messages, iteration):
            all_complete = all(
                'info_security' in results[func['id']] and 
                'reliability' in results[func['id']]
                for func in safety_functions
            )
            
            if all_complete:
                print("\n✅ 所有安全功能的信息安全性和可靠性已计算完成")
                # 添加请求实时性值的消息
                messages.append({
                    "role": "user",
                    "content": "现在请为每个安全功能确定实时性要素值，并总结所有结果。"
                })
                return False  # 继续执行以获取实时性值
            
            return False
        
        # 迭代调用LLM
        messages, metadata = self.iterate_llm_with_tools(
            initial_messages=initial_messages,
            max_iterations=max_iterations,
            on_tool_call=on_tool_call,
            completion_check=completion_check
        )
        
        # 整理结果
        self.print_section("计算结果汇总")
        
        result_functions = []
        for func in safety_functions:
            func_id = func['id']
            calculated = results.get(func_id, {})
            
            # 构建结果
            result_func = {
                "id": func_id,
                "description": func['description'],
                "element_id_set": func.get('element_id_set', ''),
                "risk_id_set": func.get('risk_id_set', ''),
                "actual": {
                    "info_security": calculated.get('info_security', 0.001),
                    "reliability": calculated.get('reliability', 0.001),
                    "realtime": calculated.get('realtime', 1.0)  # 默认值
                }
            }
            
            result_functions.append(result_func)
            
            print(f"\n【{func_id}】{func['description'][:50]}...")
            print(f"  信息安全性: {result_func['actual']['info_security']}")
            print(f"  可靠性: {result_func['actual']['reliability']}")
            print(f"  实时性: {result_func['actual']['realtime']}")
        
        print("\n" + "="*80)
        
        return result_functions
    
    def process_safety_analysis(
        self,
        hazardous_events: List[str],
        safety_functions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        处理完整的安全分析工作流
        
        Args:
            hazardous_events: 危险事件列表
            safety_functions: 安全功能列表
            
        Returns:
            包含actual和required值的完整结果
        """
        self.print_section("安全功能分析工作流")
        
        # Step 1: 计算要素值
        functions_with_actual = self.calculate_safety_function_values(safety_functions)
        
        # Step 2: 收集用户要求
        self.print_section("收集安全功能要求值")
        
        result = self.toolkit.collect_safety_requirements(
            safety_functions=functions_with_actual,
            interactive=True
        )
        
        if result['success']:
            print(f"\n✅ 成功处理 {result['count']} 个安全功能")
            
            # 显示结果
            self.toolkit.display_safety_functions(result['safety_functions'])
            
            # 保存到文件
            self.save_json(
                data=result['safety_functions'],
                filename="output/stage 2/safety_functions_calculated.json"
            )
            
            return result
        else:
            print(f"\n❌ 处理失败: {result.get('error')}")
            return result


def main():
    """主函数"""
    
    # 从 stage 1 的输出加载安全功能
    from pathlib import Path
    
    stage1_output = Path("output/stage 1/stage1_full_output.json")
    
    if not stage1_output.exists():
        print("❌ 错误: 找不到 stage 1 的输出文件")
        print(f"   请先运行 stage_1_LLM.py 生成输出文件: {stage1_output}")
        return
    
    print("\n" + "="*80)
    print("从 Stage 1 输出加载安全功能")
    print("="*80)
    
    with open(stage1_output, 'r', encoding='utf-8') as f:
        stage1_data = json.load(f)
    
    safety_functions = stage1_data.get('safety_functions', [])
    hazardous_events = stage1_data.get('hazardous_events', [])
    
    if not safety_functions:
        print("❌ 错误: Stage 1 输出中没有安全功能数据")
        return
    
    print(f"\n✅ 成功加载 {len(safety_functions)} 个安全功能")
    print(f"✅ 成功加载 {len(hazardous_events)} 个危险事件")
    
    # 显示加载的安全功能
    for func in safety_functions:
        print(f"\n【{func['id']}】{func['description'][:60]}...")
    
    print("="*80)
    
    try:
        # 创建工作流
        workflow = SafetyFunctionWorkflow()
        
        # 执行工作流
        result = workflow.process_safety_analysis(
            hazardous_events=hazardous_events,
            safety_functions=safety_functions
        )
        
        print("\n" + "="*80)
        print("工作流执行完成!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

