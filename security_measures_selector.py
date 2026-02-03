"""
安全措施选择工具
用于为安全功能选择合适的功能安全和信息安全措施
"""

import json
from typing import List, Dict, Any, Tuple
from pathlib import Path
from itertools import combinations


class SecurityMeasuresSelector:
    """安全措施选择器"""
    
    def __init__(self):
        """初始化选择器"""
        self.functional_safety_measures = {}
        self.information_security_measures = {}
        self._load_measures()
    
    def _load_measures(self):
        """加载措施数据"""
        # 功能安全措施（来自表12）
        self.functional_safety_measures = {
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
        
        # 信息安全措施（来自表13）
        self.information_security_measures = {
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
    
    def select_measures(
        self,
        current_values: Dict[str, float],
        required_values: Dict[str, float],
        function_description: str = ""
    ) -> Dict[str, Any]:
        """
        为安全功能选择合适的安全措施
        
        Args:
            current_values: 当前要素值 {"reliability": x, "realtime": y, "info_security": z}
            required_values: 目标要素值 {"reliability": x, "realtime": y, "info_security": z}
            function_description: 安全功能描述（可选）
            
        Returns:
            选择结果，包含：
            - success: 是否成功
            - selected_measures: 选中的措施列表
            - final_values: 应用措施后的最终值
            - analysis: 分析说明
        """
        try:
            # 计算需要改进的差值
            delta = {
                "reliability": required_values["reliability"] - current_values["reliability"],
                "realtime": required_values["realtime"] - current_values["realtime"],
                "info_security": required_values["info_security"] - current_values["info_security"]
            }
            
            # 分析需求
            analysis = []
            needs = {}
            
            if delta["reliability"] > 0:
                needs["reliability"] = delta["reliability"]
                analysis.append(f"需要提升可靠性: {delta['reliability']:.6f}")
            
            if delta["realtime"] < 0:
                needs["realtime"] = delta["realtime"]
                analysis.append(f"需要降低实时性: {delta['realtime']:.6f}")
            
            if delta["info_security"] > 0:
                needs["info_security"] = delta["info_security"]
                analysis.append(f"需要提升信息安全性: {delta['info_security']:.6f}")
            
            # 如果所有值都已满足要求
            if not needs:
                return {
                    "success": True,
                    "selected_measures": [],
                    "final_values": current_values.copy(),
                    "analysis": "当前值已满足所有要求，无需添加措施",
                    "details": analysis
                }
            
            # 选择措施
            selected = []
            accumulated_effects = {
                "reliability": 0,
                "realtime": 0,
                "info_security": 0
            }
            
            # 所有可用措施
            all_measures = {
                **self.functional_safety_measures,
                **self.information_security_measures
            }
            
            # 贪心选择算法：优先选择能改善多个维度的措施
            available_measures = list(all_measures.items())
            max_iterations = 20  # 防止无限循环
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                best_measure = None
                best_score = -float('inf')
                
                for measure_name, effects in available_measures:
                    if measure_name in [m["name"] for m in selected]:
                        continue  # 已选择的措施跳过
                    
                    # 计算这个措施的得分
                    score = 0
                    helps = False
                    
                    # 可靠性需求
                    if "reliability" in needs and effects["reliability"] > 0:
                        remaining = needs["reliability"] - accumulated_effects["reliability"]
                        if remaining > 0:
                            score += min(effects["reliability"], remaining) * 1000
                            helps = True
                    
                    # 实时性需求（需要降低，所以effects应该是负的）
                    if "realtime" in needs and effects["realtime"] < 0:
                        remaining = needs["realtime"] - accumulated_effects["realtime"]
                        if remaining < 0:
                            score += min(abs(effects["realtime"]), abs(remaining)) * 100
                            helps = True
                    
                    # 信息安全性需求
                    if "info_security" in needs and effects["info_security"] > 0:
                        remaining = needs["info_security"] - accumulated_effects["info_security"]
                        if remaining > 0:
                            score += min(effects["info_security"], remaining) * 1000000
                            helps = True
                    
                    # 避免选择会使其他维度恶化的措施（除非必要）
                    if "reliability" not in needs and effects["reliability"] < 0:
                        score -= abs(effects["reliability"]) * 500
                    if "realtime" not in needs and effects["realtime"] < 0:
                        score -= abs(effects["realtime"]) * 50
                    if "info_security" not in needs and effects["info_security"] < 0:
                        score -= abs(effects["info_security"]) * 500000
                    
                    if helps and score > best_score:
                        best_score = score
                        best_measure = (measure_name, effects)
                
                # 如果找到了有用的措施，添加它
                if best_measure:
                    measure_name, effects = best_measure
                    selected.append({
                        "name": measure_name,
                        "effects": effects,
                        "type": "功能安全措施" if measure_name in self.functional_safety_measures else "信息安全措施"
                    })
                    
                    # 累积效果
                    for key in accumulated_effects:
                        accumulated_effects[key] += effects[key]
                    
                    # 检查是否所有需求都已满足
                    all_satisfied = True
                    if "reliability" in needs:
                        if accumulated_effects["reliability"] < needs["reliability"]:
                            all_satisfied = False
                    if "realtime" in needs:
                        if accumulated_effects["realtime"] > needs["realtime"]:
                            all_satisfied = False
                    if "info_security" in needs:
                        if accumulated_effects["info_security"] < needs["info_security"]:
                            all_satisfied = False
                    
                    if all_satisfied:
                        break
                else:
                    # 没有找到更多有用的措施
                    break
            
            # 计算最终值
            final_values = {
                "reliability": current_values["reliability"] + accumulated_effects["reliability"],
                "realtime": current_values["realtime"] + accumulated_effects["realtime"],
                "info_security": current_values["info_security"] + accumulated_effects["info_security"]
            }
            
            # 检查是否满足要求
            satisfied = (
                final_values["reliability"] >= required_values["reliability"] and
                final_values["realtime"] >= required_values["realtime"] and
                final_values["info_security"] >= required_values["info_security"]
            )
            
            return {
                "success": True,
                "satisfied": satisfied,
                "selected_measures": selected,
                "final_values": final_values,
                "accumulated_effects": accumulated_effects,
                "analysis": "\n".join(analysis),
                "details": {
                    "current": current_values,
                    "required": required_values,
                    "delta": delta,
                    "measures_count": len(selected)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def select_all_measures_combinations(
        self,
        current_values: Dict[str, float],
        required_values: Dict[str, float],
        function_description: str = "",
        return_minimal_only: bool = True
    ) -> Dict[str, Any]:
        """
        枚举所有能满足条件的安全措施组合
        
        Args:
            current_values: 当前要素值 {"reliability": x, "realtime": y, "info_security": z}
            required_values: 目标要素值 {"reliability": x, "realtime": y, "info_security": z}
            function_description: 安全功能描述（可选）
            return_minimal_only: 是否只返回最小集合（不包含冗余措施的集合）
            
        Returns:
            选择结果，包含：
            - success: 是否成功
            - all_combinations: 所有满足条件的措施组合列表
            - total_count: 满足条件的组合总数
            - analysis: 分析说明
        """
        try:
            # 计算需要改进的差值
            delta = {
                "reliability": required_values["reliability"] - current_values["reliability"],
                "realtime": required_values["realtime"] - current_values["realtime"],
                "info_security": required_values["info_security"] - current_values["info_security"]
            }
            
            # 分析需求
            analysis = []
            needs = {}
            
            if delta["reliability"] > 0:
                needs["reliability"] = delta["reliability"]
                analysis.append(f"需要提升可靠性: {delta['reliability']:.6f}")
            
            if delta["realtime"] < 0:
                needs["realtime"] = delta["realtime"]
                analysis.append(f"需要降低实时性: {delta['realtime']:.6f}")
            
            if delta["info_security"] > 0:
                needs["info_security"] = delta["info_security"]
                analysis.append(f"需要提升信息安全性: {delta['info_security']:.6f}")
            
            # 如果所有值都已满足要求
            if not needs:
                return {
                    "success": True,
                    "all_combinations": [{
                        "measures": [],
                        "final_values": current_values.copy(),
                        "satisfied": True,
                        "accumulated_effects": {
                            "reliability": 0,
                            "realtime": 0,
                            "info_security": 0
                        }
                    }],
                    "total_count": 1,
                    "analysis": "当前值已满足所有要求，无需添加措施",
                    "details": analysis
                }
            
            # 所有可用措施
            all_measures = {
                **self.functional_safety_measures,
                **self.information_security_measures
            }
            
            measures_list = list(all_measures.items())
            n = len(measures_list)
            
            # 存储所有满足条件的组合
            valid_combinations = []
            
            # 枚举所有可能的组合（从空集到全集）
            for r in range(n + 1):
                for combo in combinations(range(n), r):
                    if len(combo) == 0:
                        continue  # 跳过空集（已经检查过当前值是否满足）
                    
                    # 计算这个组合的累积效果
                    accumulated_effects = {
                        "reliability": 0,
                        "realtime": 0,
                        "info_security": 0
                    }
                    
                    selected_measures = []
                    for idx in combo:
                        measure_name, effects = measures_list[idx]
                        selected_measures.append({
                            "name": measure_name,
                            "effects": effects,
                            "type": "功能安全措施" if measure_name in self.functional_safety_measures else "信息安全措施"
                        })
                        
                        for key in accumulated_effects:
                            accumulated_effects[key] += effects[key]
                    
                    # 计算最终值
                    final_values = {
                        "reliability": current_values["reliability"] + accumulated_effects["reliability"],
                        "realtime": current_values["realtime"] + accumulated_effects["realtime"],
                        "info_security": current_values["info_security"] + accumulated_effects["info_security"]
                    }
                    
                    # 检查是否满足要求
                    satisfied = (
                        final_values["reliability"] >= required_values["reliability"] and
                        final_values["realtime"] >= required_values["realtime"] and
                        final_values["info_security"] >= required_values["info_security"]
                    )
                    
                    if satisfied:
                        valid_combinations.append({
                            "measures": selected_measures,
                            "final_values": final_values,
                            "accumulated_effects": accumulated_effects,
                            "satisfied": True,
                            "size": len(selected_measures)
                        })
            
            # 如果只返回最小集合，过滤掉包含其他有效组合的超集
            if return_minimal_only and valid_combinations:
                minimal_combinations = []
                
                for i, combo1 in enumerate(valid_combinations):
                    is_minimal = True
                    combo1_names = set(m["name"] for m in combo1["measures"])
                    
                    # 检查是否存在更小的子集也满足条件
                    for j, combo2 in enumerate(valid_combinations):
                        if i == j:
                            continue
                        combo2_names = set(m["name"] for m in combo2["measures"])
                        
                        # 如果 combo2 是 combo1 的真子集，则 combo1 不是最小的
                        if combo2_names < combo1_names:
                            is_minimal = False
                            break
                    
                    if is_minimal:
                        minimal_combinations.append(combo1)
                
                valid_combinations = minimal_combinations
            
            # 按组合大小排序
            valid_combinations.sort(key=lambda x: (x["size"], [m["name"] for m in x["measures"]]))
            
            return {
                "success": True,
                "all_combinations": valid_combinations,
                "total_count": len(valid_combinations),
                "analysis": "\n".join(analysis),
                "return_minimal_only": return_minimal_only,
                "details": {
                    "current": current_values,
                    "required": required_values,
                    "delta": delta,
                    "needs": needs
                }
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def get_measures_info(self) -> Dict[str, Any]:
        """获取所有措施的信息"""
        return {
            "functional_safety_measures": self.functional_safety_measures,
            "information_security_measures": self.information_security_measures
        }


def main():
    """测试示例"""
    
    selector = SecurityMeasuresSelector()
    
    print("="*80)
    print("安全措施选择器测试 - 枚举所有组合")
    print("="*80)
    
    # 测试案例：F01
    test_case = {
        "id": "F01",
        "description": "保证气站附近发生泄露时，高压切断阀正常关闭",
        "current": {
            "reliability": 0.0001,
            "realtime": 1.0,
            "info_security": 1e-05
        },
        "required": {
            "reliability": 0.001,
            "realtime": 0.25,
            "info_security": 1e-05
        }
    }
    
    print(f"\n测试案例: {test_case['id']}")
    print(f"描述: {test_case['description']}")
    print(f"\n当前值:")
    print(f"  可靠性: {test_case['current']['reliability']}")
    print(f"  实时性: {test_case['current']['realtime']}")
    print(f"  信息安全性: {test_case['current']['info_security']}")
    print(f"\n要求值:")
    print(f"  可靠性: {test_case['required']['reliability']}")
    print(f"  实时性: {test_case['required']['realtime']}")
    print(f"  信息安全性: {test_case['required']['info_security']}")
    
    # 调用枚举所有组合的方法
    result = selector.select_all_measures_combinations(
        current_values=test_case['current'],
        required_values=test_case['required'],
        function_description=test_case['description'],
        return_minimal_only=True
    )
    
    if result['success']:
        print(f"\n分析:")
        print(f"  {result['analysis']}")
        print(f"\n找到 {result['total_count']} 个满足条件的措施组合")
        print(f"（{'仅显示最小集合' if result.get('return_minimal_only') else '包含所有集合'}）")
        
        all_combos = result.get('all_combinations', [])
        
        for i, combo in enumerate(all_combos, 1):
            measures = combo.get('measures', [])
            print(f"\n组合 {i} - {len(measures)} 个措施:")
            
            for measure in measures:
                print(f"  • {measure['name']} ({measure['type']})")
                print(f"    效果: 可靠性{measure['effects']['reliability']:+.6f}, "
                      f"实时性{measure['effects']['realtime']:+.6f}, "
                      f"信息安全性{measure['effects']['info_security']:+.10f}")
            
            fv = combo.get('final_values', {})
            print(f"\n  最终值:")
            print(f"    可靠性: {fv['reliability']:.6f} "
                  f"{'✓' if fv['reliability'] >= test_case['required']['reliability'] else '✗'}")
            print(f"    实时性: {fv['realtime']:.6f} "
                  f"{'✓' if fv['realtime'] >= test_case['required']['realtime'] else '✗'}")
            print(f"    信息安全性: {fv['info_security']:.10f} "
                  f"{'✓' if fv['info_security'] >= test_case['required']['info_security'] else '✗'}")
            print(f"  满足要求: {'✓ 是' if combo.get('satisfied') else '✗ 否'}")
    else:
        print(f"\n✗ 选择失败: {result.get('error')}")
        if 'traceback' in result:
            print(f"\n错误详情:\n{result['traceback']}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

