"""
Stage 1 输出解析器
从大模型的文本输出中提取安全功能列表
"""

import re
import json
from typing import List, Dict, Any


class Stage1OutputParser:
    """Stage 1 输出解析器"""
    
    @staticmethod
    def parse_safety_functions(text: str) -> List[Dict[str, Any]]:
        """
        从文本中解析安全功能列表
        
        Args:
            text: 大模型输出的文本
            
        Returns:
            安全功能列表
        """
        safety_functions = []
        
        # 分行处理
        lines = text.split('\n')
        
        # 标记是否在安全功能表格区域
        in_safety_functions_section = False
        header_found = False
        
        for i, line in enumerate(lines):
            # 检测安全功能表格的开始
            if '安全功能定义' in line or 'Safety Functions' in line or '安全功能' in line:
                in_safety_functions_section = True
                continue
            
            # 如果在安全功能区域，尝试解析表格行
            if in_safety_functions_section:
                # 跳过表头（| id | element id set | ...）
                if '| id' in line.lower() and ('element' in line.lower() or 'risk' in line.lower()):
                    header_found = True
                    continue
                
                # 跳过表头分隔符（| ---- | ---- | ---- | ---- |）
                if '----' in line and header_found:
                    continue
                
                # 尝试匹配数据行
                # 格式：| F01  | 01 ∪ 02 ∪ ... | R42 ∪ R43 ∪ ... | 描述文本 |
                # 使用更宽松的匹配
                if line.strip().startswith('|') and 'F' in line:
                    parts = [p.strip() for p in line.split('|')]
                    # 过滤掉空字符串
                    parts = [p for p in parts if p]
                    
                    # 应该有4个部分：id, element_id_set, risk_id_set, description
                    if len(parts) >= 4:
                        func_id = parts[0].strip().upper()
                        # 验证是否是有效的功能ID（F开头+数字）
                        if re.match(r'^F\d+$', func_id):
                            element_id_set = parts[1].strip()
                            risk_id_set = parts[2].strip()
                            description = parts[3].strip()
                            
                            safety_function = {
                                "id": func_id,
                                "description": description,
                                "element_id_set": element_id_set,
                                "risk_id_set": risk_id_set
                            }
                            
                            safety_functions.append(safety_function)
                
                # 如果遇到新的章节标题，退出表格区域
                elif line.strip().startswith('#') and len(safety_functions) > 0:
                    break
        
        return safety_functions
    
    @staticmethod
    def parse_hazardous_events(text: str) -> List[str]:
        """
        从文本中解析危险事件列表
        
        Args:
            text: 大模型输出的文本
            
        Returns:
            危险事件列表
        """
        hazardous_events = []
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # 匹配危险事件标题，格式：- **危险事件 E-X**：
            # 或：- **E-X**：
            match = re.search(r'-\s*\*\*(?:危险事件\s+)?(E-\d+)\*\*[：:]', line)
            
            if match:
                event_id = match.group(1)
                description = ""
                
                # 尝试在同一行获取描述
                description_match = re.search(r'\*\*[：:]\s*(.+)', line)
                if description_match:
                    description = description_match.group(1).strip()
                
                # 如果同一行没有描述，检查下一行
                if not description and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not next_line.startswith('-') and not next_line.startswith('#'):
                        description = next_line
                
                # 移除结尾的分号
                description = description.rstrip('；;')
                
                if description:
                    hazardous_events.append(f"{event_id}: {description}")
        
        return hazardous_events
    
    @staticmethod
    def parse_full_output(text: str) -> Dict[str, Any]:
        """
        解析完整输出
        
        Args:
            text: 大模型输出的文本
            
        Returns:
            包含危险事件和安全功能的字典
        """
        return {
            "hazardous_events": Stage1OutputParser.parse_hazardous_events(text),
            "safety_functions": Stage1OutputParser.parse_safety_functions(text)
        }


def test_parser():
    """测试解析器"""
    
    # 测试文本
    test_text = """
## 一、危险事件分析

- **危险事件 E-1**：
  当气站附近发生泄露（通过旋拧阀 A1 模拟），高压切断阀未正常关闭；

- **危险事件 E-2**：
  当高压切断阀与中压切断阀间发生泄露（通过旋拧阀 A2 模拟），高压切断阀与中压切断阀之一未正常关闭；

## 二、安全功能定义（Safety Functions）

| id   | element id set | risk id set | 安全功能描述 |
| ---- | -------------- | ----------- | ------------ |
| F01  | 01 ∪ 02 ∪ 03 ∪ 05 ∪ 06 ∪ 09 ∪ 10 | R42 ∪ R43 ∪ R46 ∪ C41 ∪ R51 | 保证气站附近发生泄露时，高压切断阀正常关闭；且泄露修复后，高压切断阀正常打开 |
| F02  | 01 ∪ 02 ∪ 03 ∪ 05 ∪ 06 ∪ 07 ∪ 09 ∪ 10 ∪ 11 ∪ 12 | R42 ∪ R43 ∪ R46 ∪ C41 ∪ R51 | 保证高压切断阀与中压切断阀间发生泄露时，高压切断阀与中压切断阀均正常关闭 |
"""
    
    parser = Stage1OutputParser()
    result = parser.parse_full_output(test_text)
    
    print("解析结果：")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_parser()

