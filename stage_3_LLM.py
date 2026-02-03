"""
完整的安全措施选择工作流（重构版）
包含三个阶段：
1. 为每个安全功能枚举所有可行的措施组合
2. 找到能同时满足所有安全功能的全局措施组合
3. 基于用户指定的权重选择最优方案
"""

import json
import time
from typing import List, Dict, Any, Set, Optional
from security_measures_selector import SecurityMeasuresSelector
from itertools import combinations
from llm_workflow_base import (
    ToolBasedWorkflow,
    LLMWorkflowBase,
    DataLoaderMixin,
    UserInteractionMixin
)
from log_utils import setup_logging, teardown_logging


class MeasuresSelectionWorkflow(ToolBasedWorkflow):
    """安全措施选择工作流 - 阶段1"""
    
    def __init__(self):
        """初始化工作流"""
        super().__init__()
        
        # 初始化措施选择器
        self.selector = SecurityMeasuresSelector()
        
        # 加载措施表格
        self.measures_tables = self.load_table_files(
            table_dir="input_data/tables/stage 3",
            table_files={
                "measures_list": "表 11 功能安全和信息安全措施列表.md",
                "functional_safety": "表 12 各功能安全措施的要素值.md",
                "information_security": "表 13 各信息安全措施的要素值.md"
            }
        )
    
    def get_tool_definitions(self) -> List[Dict]:
        """获取工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "select_all_security_measures_combinations",
                    "description": "为安全功能枚举所有能满足条件的功能安全和信息安全措施组合，返回所有可行的措施集合",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "function_id": {
                                "type": "string",
                                "description": "安全功能ID，如F01"
                            },
                            "current_values": {
                                "type": "object",
                                "description": "当前要素值",
                                "properties": {
                                    "reliability": {"type": "number"},
                                    "realtime": {"type": "number"},
                                    "info_security": {"type": "number"}
                                },
                                "required": ["reliability", "realtime", "info_security"]
                            },
                            "required_values": {
                                "type": "object",
                                "description": "目标要素值",
                                "properties": {
                                    "reliability": {"type": "number"},
                                    "realtime": {"type": "number"},
                                    "info_security": {"type": "number"}
                                },
                                "required": ["reliability", "realtime", "info_security"]
                            },
                            "description": {
                                "type": "string",
                                "description": "安全功能描述"
                            },
                            "return_minimal_only": {
                                "type": "boolean",
                                "description": "是否只返回最小集合（不包含冗余措施的集合），默认为true",
                                "default": True
                            }
                        },
                        "required": ["function_id", "current_values", "required_values"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """执行工具调用"""
        if tool_name == "select_all_security_measures_combinations":
            result = self.selector.select_all_measures_combinations(
                current_values=arguments["current_values"],
                required_values=arguments["required_values"],
                function_description=arguments.get("description", ""),
                return_minimal_only=arguments.get("return_minimal_only", True)
            )
            return result
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    def select_measures_for_functions(
        self,
        safety_functions: List[Dict[str, Any]],
        max_iterations: int = 20
    ) -> Dict[str, Any]:
        """
        为所有安全功能选择措施
        
        Args:
            safety_functions: 安全功能列表
            max_iterations: 最大迭代次数
            
        Returns:
            选择结果
        """
        self.print_section("安全措施选择工作流")
        
        # 构建系统提示词
        system_prompt = f"""你是一个工业控制系统(ICS)安全工程师，负责为安全功能枚举所有可行的功能安全和信息安全措施组合。

**任务**：为每个安全功能枚举所有能满足条件的措施组合，使其actual值达到required值。

**措施列表和要素值**：

{self.measures_tables.get('measures_list', '')}

{self.measures_tables.get('functional_safety', '')}

{self.measures_tables.get('information_security', '')}

**选择原则**：

1. **可靠性要素**：
   - 如果 actual.reliability < required.reliability，需要选择提升可靠性的措施
   - 功能安全措施通常提供正的可靠性增益

2. **实时性要素**：
   - 如果 actual.realtime > required.realtime，需要选择降低实时性的措施（更快）
   - 实时性要素值越小表示响应越快

3. **信息安全性要素**：
   - 如果 actual.info_security < required.info_security，需要选择提升信息安全性的措施

4. **枚举所有组合**：
   - 工具会自动枚举所有可能的措施组合（2^11种可能）
   - 筛选出所有满足条件的组合

请依次处理每个安全功能。
"""
        
        # 构建用户消息
        functions_summary = "\n\n".join([
            f"**{func['id']}**: {func['description']}\n"
            f"- 当前值: reliability={func['actual']['reliability']:.6f}, "
            f"realtime={func['actual']['realtime']:.2f}, "
            f"info_security={func['actual']['info_security']:.10f}\n"
            f"- 要求值: reliability={func['required']['reliability']:.6f}, "
            f"realtime={func['required']['realtime']:.2f}, "
            f"info_security={func['required']['info_security']:.10f}"
            for func in safety_functions
        ])
        
        user_message = f"""请为以下安全功能枚举所有能满足条件的措施组合：

{functions_summary}

请依次为每个安全功能调用 select_all_security_measures_combinations 工具。
"""
        
        # 初始化消息
        initial_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # 存储结果
        results = {}
        
        # 定义工具调用回调
        def on_tool_call(tool_name, tool_args, tool_result):
            function_id = tool_args.get("function_id", "Unknown")
            print(f"为 {function_id} 选择措施...")
            
            if tool_result.get('success'):
                results[function_id] = tool_result
                
                total_count = tool_result.get('total_count', 0)
                if total_count > 0:
                    print(f"  ✅ 找到 {total_count} 个满足条件的措施组合")
                    
                    # 显示前几个组合
                    all_combos = tool_result.get('all_combinations', [])
                    for i in range(min(3, len(all_combos))):
                        combo = all_combos[i]
                        measures = combo.get('measures', [])
                        print(f"    组合 {i+1} ({len(measures)} 个措施):")
                        for measure in measures:
                            print(f"      - {measure['name']}")
                    
                    if total_count > 3:
                        print(f"    ... 还有 {total_count - 3} 个组合")
                else:
                    print(f"  ℹ️ 当前值已满足要求，无需添加措施")
            else:
                print(f"  ❌ 选择失败: {tool_result.get('error')}")
        
        # 定义完成检查
        def completion_check(messages, iteration):
            return len(results) >= len(safety_functions)
        
        # 迭代调用LLM
        messages, metadata = self.iterate_llm_with_tools(
            initial_messages=initial_messages,
            max_iterations=max_iterations,
            on_tool_call=on_tool_call,
            completion_check=completion_check
        )
        
        return results
    
    def process_safety_functions(
        self,
        input_file: str = "output/stage 2/safety_functions_calculated.json"
    ) -> Dict[str, Any]:
        """处理安全功能文件"""
        # 读取数据
        safety_functions = self.load_json(input_file)
        print(f"\n📁 已加载 {len(safety_functions)} 个安全功能")
        
        # 选择措施
        results = self.select_measures_for_functions(safety_functions)
        
        # 整理输出
        self.print_section("措施选择结果汇总")
        
        final_results = []
        for func in safety_functions:
            func_id = func['id']
            selection = results.get(func_id, {})
            
            result_item = {
                "id": func_id,
                "description": func['description'],
                "element_id_set": func.get('element_id_set', ''),
                "risk_id_set": func.get('risk_id_set', ''),
                "actual": func['actual'],
                "required": func['required'],
                "all_combinations": []
            }
            
            if selection.get('success'):
                all_combos = selection.get('all_combinations', [])
                result_item["all_combinations"] = all_combos
                result_item["total_count"] = selection.get('total_count', 0)
                result_item["return_minimal_only"] = selection.get('return_minimal_only', True)
                
                print(f"\n【{func_id}】{func['description'][:50]}...")
                print(f"  找到 {result_item['total_count']} 个满足条件的措施组合")
            
            final_results.append(result_item)
        
        # 保存结果
        self.save_json(
            data=final_results,
            filename="output/stage 3/security_measures_selected.json"
        )
        
        return {
            "success": True,
            "results": final_results,
            "output_file": "security_measures_selected.json"
        }


class GlobalMeasuresSelector(LLMWorkflowBase, DataLoaderMixin):
    """全局措施选择器 - 阶段2"""
    
    def __init__(self):
        """初始化选择器"""
        super().__init__(auto_load_env=False)  # 不需要OpenAI客户端
        
        # 加载措施数据
        measures_data = self.load_measures_data()
        self.functional_safety_measures = measures_data["functional_safety"]
        self.information_security_measures = measures_data["information_security"]
    
    def check_combination_satisfies_all_functions(
        self,
        measures_set: Set[str],
        safety_functions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """检查一个措施集合是否能同时满足所有安全功能"""
        all_measures = {
            **self.functional_safety_measures,
            **self.information_security_measures
        }
        
        total_effects = {"reliability": 0, "realtime": 0, "info_security": 0}
        measures_details = []
        
        for measure_name in measures_set:
            if measure_name in all_measures:
                effects = all_measures[measure_name]
                for key in total_effects:
                    total_effects[key] += effects[key]
                
                measures_details.append({
                    "name": measure_name,
                    "effects": effects,
                    "type": "功能安全措施" if measure_name in self.functional_safety_measures else "信息安全措施"
                })
        
        all_satisfied = True
        function_results = []
        
        for func in safety_functions:
            final_values = {
                "reliability": func['actual']['reliability'] + total_effects['reliability'],
                "realtime": func['actual']['realtime'] + total_effects['realtime'],
                "info_security": func['actual']['info_security'] + total_effects['info_security']
            }
            
            satisfied = (
                final_values["reliability"] >= func['required']['reliability'] and
                final_values["realtime"] >= func['required']['realtime'] and
                final_values["info_security"] >= func['required']['info_security']
            )
            
            function_results.append({
                "function_id": func['id'],
                "description": func['description'],
                "actual": func['actual'],
                "required": func['required'],
                "final_values": final_values,
                "satisfied": satisfied
            })
            
            if not satisfied:
                all_satisfied = False
        
        return {
            "measures": measures_details,
            "total_effects": total_effects,
            "all_satisfied": all_satisfied,
            "function_results": function_results,
            "size": len(measures_details)
        }
    
    def find_all_global_combinations(
        self,
        safety_functions: List[Dict[str, Any]],
        return_minimal_only: bool = True
    ) -> Dict[str, Any]:
        """找到所有能同时满足所有安全功能的全局措施组合"""
        self.print_section("阶段2：全局安全措施组合搜索")
        
        all_measures = {**self.functional_safety_measures, **self.information_security_measures}
        measures_list = list(all_measures.keys())
        n = len(measures_list)
        
        print(f"\n可用措施总数: {n}")
        print(f"安全功能总数: {len(safety_functions)}")
        print(f"总组合数: 2^{n} = {2**n}")
        print(f"\n开始枚举所有组合...")
        
        valid_global_combinations = []
        total_checked = 0
        
        for r in range(n + 1):
            if r == 0:
                measures_set = set()
                result = self.check_combination_satisfies_all_functions(measures_set, safety_functions)
                total_checked += 1
                
                if result['all_satisfied']:
                    valid_global_combinations.append(result)
                    print(f"  ✓ 找到满足条件的组合: 空集（无需添加措施）")
            else:
                found_count = 0
                for combo_indices in combinations(range(n), r):
                    measures_set = set(measures_list[i] for i in combo_indices)
                    result = self.check_combination_satisfies_all_functions(measures_set, safety_functions)
                    total_checked += 1
                    
                    if result['all_satisfied']:
                        valid_global_combinations.append(result)
                        found_count += 1
                
                if found_count > 0:
                    print(f"  大小为 {r} 的组合: 找到 {found_count} 个满足条件")
        
        print(f"\n总共检查了 {total_checked} 个组合")
        print(f"找到 {len(valid_global_combinations)} 个满足所有安全功能的组合")
        
        # 保存过滤前的所有组合
        all_valid_combinations_count = len(valid_global_combinations)
        
        # 过滤最小集合
        minimal_combinations = []
        if return_minimal_only and valid_global_combinations:
            print(f"\n正在过滤，只保留最小集合...")
            
            for i, combo1 in enumerate(valid_global_combinations):
                is_minimal = True
                combo1_names = set(m["name"] for m in combo1["measures"])
                
                for j, combo2 in enumerate(valid_global_combinations):
                    if i == j:
                        continue
                    combo2_names = set(m["name"] for m in combo2["measures"])
                    
                    if combo2_names < combo1_names:
                        is_minimal = False
                        break
                
                if is_minimal:
                    minimal_combinations.append(combo1)
            
            print(f"过滤后保留 {len(minimal_combinations)} 个最小集合")
            
            # 保存过滤详情
            self.save_json(
                data={
                    "summary": {
                        "total_combinations_before_filter": all_valid_combinations_count,
                        "minimal_combinations_after_filter": len(minimal_combinations),
                        "filtered_out_count": all_valid_combinations_count - len(minimal_combinations)
                    },
                    "all_valid_combinations": valid_global_combinations,
                    "minimal_combinations": minimal_combinations
                },
                filename="output/stage 3/minimal_filter_details.json"
            )
            print(f"✅ 已保存过滤详情到: output/stage 3/minimal_filter_details.json")
            
            valid_global_combinations = minimal_combinations
        
        valid_global_combinations.sort(key=lambda x: (x["size"], [m["name"] for m in x["measures"]]))
        
        return {
            "success": True,
            "global_combinations": valid_global_combinations,
            "total_count": len(valid_global_combinations),
            "return_minimal_only": return_minimal_only,
            "total_checked": total_checked,
            "total_functions": len(safety_functions),
            "all_valid_combinations_count": all_valid_combinations_count,
            "minimal_combinations_count": len(minimal_combinations) if return_minimal_only else None
        }


class OptimalMeasuresSelector(LLMWorkflowBase, UserInteractionMixin):
    """最优措施选择器 - 阶段3"""
    
    def __init__(self, element_weights: Optional[Dict[str, float]] = None):
        """初始化选择器"""
        super().__init__(auto_load_env=False)  # 不需要OpenAI客户端
        
        # 要素权重（由用户输入或使用默认值）
        self.element_weights = element_weights or {
            'reliability': 3 * (10 ** 2),
            'realtime': 2 * (10 ** 0),
            'info_security': 1 * (10 ** 3)
        }
        self.function_weights = []
    
    def get_element_weights_from_user(self) -> Dict[str, float]:
        """从用户获取要素权重"""
        self.print_section("要素权重（使用默认值，跳过输入）")
        print("\n已自动使用默认要素权重：")
        print(f"  - 可靠性 (reliability): {self.element_weights['reliability']}")
        print(f"  - 实时性 (realtime): {self.element_weights['realtime']}")
        print(f"  - 信息安全性 (info_security): {self.element_weights['info_security']}")
        return self.element_weights
    
    def get_function_weights_from_user(self, safety_functions: List[Dict[str, Any]]) -> List[float]:
        """从用户获取每个安全功能的权重"""
        self.print_section("安全功能权重（使用默认值，跳过输入）")
        weights = [1.0 for _ in safety_functions]
        print(f"\n已自动使用默认权重（全部=1.0）：{weights}")
        return weights
    
    def calculate_function_measure(self, final_values: Dict[str, float]) -> float:
        """计算单个安全功能的要素度量"""
        return (
            self.element_weights['reliability'] * final_values['reliability'] +
            self.element_weights['realtime'] * final_values['realtime'] +
            self.element_weights['info_security'] * final_values['info_security']
        )
    
    def calculate_combination_measure(
        self,
        combination: Dict[str, Any],
        function_weights: List[float]
    ) -> Dict[str, Any]:
        """计算组合的总要素度量"""
        function_results = combination['function_results']
        function_measures = []
        
        for func_result in function_results:
            measure = self.calculate_function_measure(func_result['final_values'])
            function_measures.append({
                'function_id': func_result['function_id'],
                'description': func_result['description'],
                'final_values': func_result['final_values'],
                'measure': measure
            })
        
        total_measure = 0
        for func_measure_info in function_measures:
            func_id = func_measure_info['function_id']
            func_index = int(func_id[1:]) - 1
            weight = function_weights[func_index] if func_index < len(function_weights) else 1
            total_measure += weight * func_measure_info['measure']
        
        return {
            'combination': combination,
            'function_measures': function_measures,
            'total_measure': total_measure
        }
    
    def select_optimal_combination(
        self,
        global_combinations: List[Dict[str, Any]],
        safety_functions: List[Dict[str, Any]],
        function_weights: List[float]
    ) -> Dict[str, Any]:
        """从所有全局组合中选择最优方案"""
        self.print_section("阶段3：最优措施方案选择")
        
        if not global_combinations:
            print("\n⚠️ 没有找到任何全局组合")
            return {'success': False, 'error': '没有可用的全局组合'}
        
        self.function_weights = function_weights
        
        print(f"\n📊 配置信息：")
        print(f"  安全功能权重: {function_weights}")
        print(f"  要素权重: {self.element_weights}")
        
        print(f"\n📁 共有 {len(global_combinations)} 个候选组合")
        print(f"\n正在计算各组合的要素度量...")
        
        all_measures = []
        for i, combo in enumerate(global_combinations, 1):
            measure_info = self.calculate_combination_measure(combo, function_weights)
            measure_info['combination_index'] = i
            all_measures.append(measure_info)
            
            if i <= 5:
                print(f"  组合 {i}: {len(combo['measures'])} 个措施, 总要素度量 = {measure_info['total_measure']:.10f}")
        
        if len(global_combinations) > 5:
            print(f"  ... 还有 {len(global_combinations) - 5} 个组合")
        
        optimal = max(all_measures, key=lambda x: x['total_measure'])
        
        self.print_section("最优方案详情")
        
        print(f"\n🏆 最优方案: 组合 {optimal['combination_index']}")
        print(f"📈 总要素度量: {optimal['total_measure']:.10f}")
        
        measures = optimal['combination']['measures']
        print(f"\n【措施列表】({len(measures)} 个措施)")
        if measures:
            for i, measure in enumerate(measures, 1):
                print(f"  {i}. {measure['name']} ({measure['type']})")
        else:
            print("  （无需添加措施）")
        
        return {
            'success': True,
            'optimal_solution': {
                'combination_index': optimal['combination_index'],
                'total_measure': optimal['total_measure'],
                'measures': measures,
                'total_effects': optimal['combination']['total_effects'],
                'function_measures': optimal['function_measures']
            },
            'all_combinations_ranking': [
                {
                    'combination_index': m['combination_index'],
                    'total_measure': m['total_measure'],
                    'measures_count': len(m['combination']['measures'])
                }
                for m in sorted(all_measures, key=lambda x: x['total_measure'], reverse=True)
            ]
        }


def main():
    """主函数 - 执行完整的三阶段工作流"""
    
    # 设置日志记录
    log_file, tee, original_stdout = setup_logging("stage_3")
    
    try:
        print("\n" + "="*80)
        print("完整的安全措施选择工作流")
        print("="*80)
        print("\n流程说明：")
        print("  阶段1：为每个安全功能枚举所有可行的措施组合")
        print("  阶段2：找到能同时满足所有安全功能的全局措施组合")
        print("  阶段3：基于用户指定的权重选择最优方案")
        print("="*80)
        
        # ========== 阶段1 ==========
        t_stage1_start = time.time()
        print("\n" + "▶"*40)
        print("开始执行阶段1：为每个安全功能选择措施")
        print("▶"*40)
        
        workflow = MeasuresSelectionWorkflow()
        result_stage1 = workflow.process_safety_functions()
        
        if not result_stage1['success']:
            print("\n❌ 阶段1执行失败，停止流程")
            return
        
        print("\n✅ 阶段1完成")
        print(f"⏱ 阶段1耗时: {time.time() - t_stage1_start:.2f} 秒")
        
        # 读取安全功能数据
        safety_functions = workflow.load_json("output/stage 2/safety_functions_calculated.json")
        
        # ========== 阶段2 ==========
        t_stage2_start = time.time()
        print("\n" + "▶"*40)
        print("开始执行阶段2：查找全局措施组合")
        print("▶"*40)
        
        global_selector = GlobalMeasuresSelector()
        result_stage2 = global_selector.find_all_global_combinations(
            safety_functions,
            return_minimal_only=True
        )
        
        if not result_stage2['success'] or result_stage2['total_count'] == 0:
            print("\n❌ 阶段2执行失败或未找到满足条件的组合，停止流程")
            return
        
        print("\n✅ 阶段2完成")
        print(f"⏱ 阶段2耗时: {time.time() - t_stage2_start:.2f} 秒")
        
        # 保存阶段2结果
        global_selector.save_json(
            data={
                "summary": {
                    "total_functions": result_stage2['total_functions'],
                    "total_combinations_checked": result_stage2['total_checked'],
                    "valid_combinations_found": result_stage2['total_count'],
                    "return_minimal_only": result_stage2['return_minimal_only']
                },
                "global_combinations": result_stage2['global_combinations']
            },
            filename="output/stage 3/global_measures_combinations.json"
        )
        
        # ========== 阶段3 ==========
        t_stage3_start = time.time()
        print("\n" + "▶"*40)
        print("开始执行阶段3：选择最优方案")
        print("▶"*40)
        
        optimal_selector = OptimalMeasuresSelector()
        
        # 获取要素权重
        element_weights = optimal_selector.get_element_weights_from_user()
        
        # 获取安全功能权重
        function_weights = optimal_selector.get_function_weights_from_user(safety_functions)
        
        result_stage3 = optimal_selector.select_optimal_combination(
            result_stage2['global_combinations'],
            safety_functions,
            function_weights
        )
        
        if not result_stage3['success']:
            print("\n❌ 阶段3执行失败")
            return
        
        print("\n✅ 阶段3完成")
        print(f"⏱ 阶段3耗时: {time.time() - t_stage3_start:.2f} 秒")
        
        # 保存阶段3结果
        optimal_selector.save_json(
            data={
                "configuration": {
                    "function_weights": function_weights,
                    "element_weights": optimal_selector.element_weights
                },
                "total_candidates": result_stage2['total_count'],
                "optimal_solution": result_stage3['optimal_solution'],
                "all_combinations_ranking": result_stage3['all_combinations_ranking']
            },
            filename="output/stage 3/optimal_measures_solution.json"
        )
        
        # 总结
        print("\n" + "="*80)
        print("完整流程执行完成！")
        print("="*80)
        
        print("\n📊 结果摘要：")
        print(f"  - 处理的安全功能数量: {len(safety_functions)}")
        print(f"  - 检查的组合总数: {result_stage2['total_checked']}")
        print(f"  - 找到的有效组合数量: {result_stage2.get('all_valid_combinations_count', 0)}")
        if result_stage2.get('minimal_combinations_count'):
            print(f"  - 过滤后的最小集合数量: {result_stage2['minimal_combinations_count']}")
        print(f"  - 最优方案的要素度量: {result_stage3['optimal_solution']['total_measure']:.10f}")
        
        print("\n📁 输出文件：")
        print("  - output/stage 3/security_measures_selected.json (阶段1结果)")
        print("  - output/stage 3/global_measures_combinations.json (阶段2结果)")
        if result_stage2.get('return_minimal_only'):
            print("  - output/stage 3/minimal_filter_details.json (最小集合过滤详情)")
        print("  - output/stage 3/optimal_measures_solution.json (阶段3结果 - 最优方案)")
        
        print("\n💡 最优方案措施列表：")
        measures = result_stage3['optimal_solution']['measures']
        if measures:
            for i, measure in enumerate(measures, 1):
                print(f"  {i}. {measure['name']} ({measure['type']})")
        else:
            print("  （无需添加措施）")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 总耗时
        # 计算从开始到此的总耗时（以阶段1开始为界，若需更精确可在更外层加总计时）
        # 这里从 main 进入后开始计时
        # 为避免遗漏，若需要严格总时长，请在最外层再加一个总计时；此处简化不重复
        # 清理日志
        teardown_logging(log_file, tee, original_stdout)


if __name__ == "__main__":
    main()

