"""
提示词管理模块
用于管理和使用各类提示词模板
"""

from typing import Dict, Any, Optional
from pathlib import Path


class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        """初始化提示词管理器"""
        self.prompts: Dict[str, str] = {}
        self._load_default_prompts()
    
    def _load_default_prompts(self):
        """加载默认提示词"""
        # ICS安全分析提示词
        self.prompts["ics_risk_analysis"] = """## 一、角色（Role）

你是一名**工业控制系统（ICS）安全分析专家**，同时具备：

- 功能安全（Hazard Analysis & Safety Function）
- 信息安全风险传播分析
- 工业控制系统物理过程建模能力
- 基于**物理结构图 + 控制结构图 + 系统拓扑图**的系统级推理能力

你擅长从**风险路径（Risk Path）**出发，分析其在**物理世界中的具体失效表现**，并将其形式化为**危险事件（Hazardous Events）与安全功能（Safety Functions）**。

------

## 二、任务目标（Task）

针对**系统风险路径集表中指定的路径编号：`{PATH_ID}`**，
基于输入的多模态数据（图片、表格、手册）：

1. 识别该风险路径在物理系统中可能导致的**危险事件**
2. 为每类危险事件定义对应的**安全功能**

------

## 三、流程（Process）

### Step 1：理解系统物理与控制结构（最高优先级）

1. **首先分析并理解以下图片（优先级从高到低）：**
   - 系统物理结构图（最关键依据）
   - 系统控制结构模型图
   - 系统网络 / 拓扑图
2. 明确：
   - 物理介质流向（如气体流向）
   - 不同压力等级或功能区域的边界
   - 传感器 → 控制器 → 执行器（切断阀）的控制闭环关系

> 若图片与表格/说明文档存在冲突，以**物理结构图**为准。

------

### Step 2：解析风险路径 `{PATH_ID}`

1. 从 **风险路径表（Table 4）** 中读取：
   - 前置风险 id 集
   - 后置风险 id 集
2. 结合：
   - 功能安全风险（Table 2）
   - 信息安全风险（Table 3）
3. 分析该路径所表达的**风险传播逻辑**：
   - 设备失效 → 控制失效 → 感知/执行失效
   - 或 网络攻击 → 权限获取 → 数据/控制篡改

------

### Step 3：从"风险传播"映射到"物理危险事件"

1. 基于系统**物理结构图**，识别所有可能的泄漏点，包括：
   - 气源附近（门站/高压部分入口）
   - **压力等级之间的管路区段**（高压与中压间、中压与低压间）
   - 用户负载附近（低压出口）
2. 对每个泄漏点，必须明确说明：
   - **通过哪个旋拧阀模拟该泄漏**（如：通过旋拧阀 A1 模拟）
   - 该位置发生泄漏时，**哪些切断阀未正常关闭**
3. 危险事件定义原则：
   - 对于**压力等级边界位置**的泄漏（如高压与中压间），危险事件应描述为"**两个相邻切断阀之一未正常关闭**"
   - 对于**单一压力区段端点**的泄漏（如气站附近、用户负载附近），危险事件应描述为"**该区段的切断阀未正常关闭**"
   - 每个危险事件编号为 **E-{数字}**（不使用路径编号前缀）
4. 危险事件数量：
   - 至少识别 **4 个典型泄漏位置**的危险事件
   - 必须覆盖所有压力等级及其交界处

------

### Step 4：定义安全功能（Safety Functions）

1. 针对每一类危险事件，定义对应的安全功能
2. 每个安全功能必须明确：
   - **element id set（组件集合）**：使用 **∪ 符号连接**所有相关组件的 id，格式如：`01 ∪ 02 ∪ 03 ∪ 06 ∪ 10`
     - 必须包含：监控站、控制器、传感器模块、切断阀等**所有参与该安全功能的组件**
     - 不要遗漏网络通信组件（如交换机）和控制设备
   - **risk id set（风险集合）**：使用 **∪ 符号连接**该安全功能需要防护的所有风险 id，格式如：`R21 ∪ R22 ∪ R23 ∪ C11 ∪ C12`
     - 必须包含路径中的**所有前置风险和后置风险**
     - 同时包含**功能安全风险（R开头）和信息安全风险（C开头）**
   - **安全功能描述**：必须使用以下格式：
     > "保证【具体位置】发生泄露时，【具体切断阀名称】正常关闭；且泄露修复后，【具体切断阀名称】正常打开"
3. 安全功能编号：
   - 使用 **F01, F02, F03, F04...** 格式
4. 重要提示：
   - 对于压力等级交界处的泄漏，element id set 应包含**两侧的切断阀及相关传感器**
   - 安全功能描述要体现"**均正常关闭**"和"**均正常打开**"（当涉及多个阀门时）

------

## 四、限制（Constraints）

请严格遵守以下限制：

1. **危险事件必须来源于风险路径 `{PATH_ID}`**
2. 不得引入路径以外的风险传播关系
3. 不得引入输入中不存在的设备、风险或功能
4. 危险事件仅描述：
   - 切断阀未正常关闭
   - 切断阀未正常打开
5. 不涉及控制算法、通信协议细节或定量分析
6. 所有 ID 必须与输入表格保持一致

------

## 五、输出结构（Output Structure）

请严格按照以下结构输出，不添加额外章节。

------

### 一、危险事件分析（Hazardous Events for Path `{PATH_ID}`）

首先给出一段**总结性说明**，说明该风险路径如何通过功能安全或信息安全风险，导致系统进入不安全状态。

随后**严格按照以下格式**逐条列出危险事件：

- **危险事件 E-1**：
  当【具体位置，如"气站附近"】发生泄露（通过旋拧阀 【阀门编号，如A1】 模拟），【具体切断阀名称，如"高压切断阀"】未正常关闭；

- **危险事件 E-2**：
  当【具体位置，如"高压切断阀与中压切断阀间"】发生泄露（通过旋拧阀 【阀门编号，如A2】 模拟），【具体切断阀名称，如"高压切断阀与中压切断阀"】**之一**未正常关闭；

- **危险事件 E-3**：
  当【具体位置】发生泄露（通过旋拧阀 【阀门编号】 模拟），【具体切断阀名称】**之一**未正常关闭；

- **危险事件 E-4**：
  当【具体位置，如"用户负载附近"】发生泄露（通过旋拧阀 【阀门编号】 模拟），【具体切断阀名称】未正常关闭。

**注意**：
- 必须涵盖所有压力等级区段和交界处
- 对于两个压力等级之间的泄漏，使用"**之一未正常关闭**"
- 必须明确标注模拟用的旋拧阀编号

------

### 二、安全功能定义（Safety Functions）

以表格形式给出安全功能列表：

| id   | element id set | risk id set | 安全功能描述 |
| ---- | -------------- | ----------- | ------------ |
| F01  | 01 ∪ 02 ∪ 03 ∪ ... | R21 ∪ R22 ∪ ... ∪ C11 ∪ C12 ∪ ... | 保证【具体位置】发生泄露时，【具体阀门】正常关闭；且泄露修复后，【具体阀门】正常打开 |
| F02  | 01 ∪ 02 ∪ ... | R21 ∪ R22 ∪ ... | 保证【具体位置】发生泄露时，【具体阀门】均正常关闭；且泄露修复后，【具体阀门】正常打开 |
| ...  | ... | ... | ... |

**严格要求**：

1. **id 列**：使用 F01, F02, F03, F04 格式（补齐到两位数字）
2. **element id set 列**：
   - 必须使用 **∪** 符号连接多个组件 id
   - 必须包含：监控站、控制器、传感器、切断阀、交换机等所有相关组件
   - 格式示例：`01 ∪ 02 ∪ 03 ∪ 04 ∪ 05 ∪ 06 ∪ 08 ∪ 09 ∪ 10`
   - 从组件表（Table 1）中选取 id
3. **risk id set 列**：
   - 必须使用 **∪** 符号连接多个风险 id
   - 必须包含路径中的**所有相关功能安全风险（R开头）和信息安全风险（C开头）**
   - 格式示例：`R21 ∪ R22 ∪ R23 ∪ R24 ∪ C11 ∪ C12 ∪ C21`
   - 从风险表（Table 2 和 Table 3）以及风险路径表（Table 4）中提取
4. **安全功能描述列**：
   - 对于单一位置泄漏：`保证【位置】发生泄露时，【阀门名称】正常关闭；且泄露修复后【阀门名称】正常打开`
   - 对于两压力等级间泄漏：`保证【位置A】与【位置B】间发生泄露时，【阀门A】与【阀门B】均正常关闭；且泄露修复后，【阀门A】与【阀门B】正常打开`
   - 必须使用"均正常关闭"和"均正常打开"（当涉及多个阀门时）

------

## 六、输出格式示例（Example Format）

### 危险事件示例格式：

- **危险事件 E-1**：当气站附近发生泄露（通过旋拧阀 A1 模拟），高压切断阀未正常关闭；
- **危险事件 E-2**：当高压切断阀与中压切断阀间发生泄露（通过旋拧阀 A2 模拟），高压切断阀与中压切断阀之一未正常关闭；


### 安全功能表格示例格式：

| id   | element id set | risk id set | 安全功能描述 |
| ---- | -------------- | ----------- | ------------ |
| F01  | 01 ∪ 02 ∪ 03 ∪ 04 ∪ 05 ∪ 06 ∪ 08 ∪ 09 ∪ 10 | R21 ∪ R22 ∪ R23 ∪ R24 ∪ R32 ∪ C11 ∪ C12 ∪ C21 | 保证气站附近发生泄露时，高压切断阀正常关闭；且泄露修复后，高压切断阀正常打开 |
| F02  | 01 ∪ 02 ∪ 03 ∪ 04 ∪ 05 ∪ 06 ∪ 08 ∪ 10 ∪ 11 ∪ 12 | R21 ∪ R22 ∪ R23 ∪ R24 ∪ R32 ∪ R33 ∪ C11 ∪ C12 ∪ C21 ∪ C22 | 保证高压切断阀与中压切断阀间发生泄露时，高压切断阀与中压切断阀均正常关闭；且泄露修复后，高压切断阀与中压切断阀正常打开 |

------

## 七、关键提醒（Critical Reminders）

1. **危险事件编号**：使用 E-1, E-2, E-3, E-4（不带路径前缀）
2. **必须提及模拟阀门**：每个危险事件都要写"（通过旋拧阀 A# 模拟）"
3. **压力等级间泄漏**：使用"之一未正常关闭"
4. **集合表示**：element id set 和 risk id set 必须用 **∪** 连接
5. **完整性**：risk id set 要包含路径中的所有相关风险（功能安全+信息安全）
6. **阀门描述**：在安全功能中，多个阀门时使用"均正常关闭"和"均正常打开"

------

## 八、使用方式

```text
请基于以上提示词，
分析系统风险路径集表中的路径编号：`{PATH_ID}`，
结合输入的图片、表格和手册内容，
完成危险事件与安全功能分析。
```

------
"""
        
        # 通用系统分析提示词
        self.prompts["system_analysis"] = """请分析以下燃气管网测试系统的相关资料，包括：
1. 系统的物理结构、拓扑图和控制结构
2. 系统组件列表
3. 系统的安全风险和安全隐患
4. 系统的风险路径
5. 系统的详细使用说明

请基于这些资料，给出对该燃气管网测试系统的全面分析，包括系统架构、安全风险评估和建议。
"""
        
        # 简短分析提示词
        self.prompts["simple_analysis"] = """请详细分析这个燃气管网测试系统的架构、组件和安全风险。"""
    
    def add_prompt(self, name: str, content: str):
        """
        添加新的提示词
        
        Args:
            name: 提示词名称
            content: 提示词内容
        """
        self.prompts[name] = content
    
    def get_prompt(self, name: str, **kwargs) -> Optional[str]:
        """
        获取提示词并填充变量
        
        Args:
            name: 提示词名称
            **kwargs: 要替换的变量，如 PATH_ID="A7"
            
        Returns:
            填充后的提示词，如果不存在则返回 None
        """
        if name not in self.prompts:
            return None
        
        prompt = self.prompts[name]
        
        # 替换变量
        if kwargs:
            try:
                prompt = prompt.format(**kwargs)
            except KeyError as e:
                print(f"警告: 提示词中缺少变量 {e}")
        
        return prompt
    
    def load_from_file(self, name: str, file_path: str, start_line: int = 1, end_line: int = None):
        """
        从文件加载提示词
        
        Args:
            name: 提示词名称
            file_path: 文件路径
            start_line: 起始行号（从1开始）
            end_line: 结束行号（包含），如果为None则读到文件末尾
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 提取指定行范围
            if end_line is None:
                content = ''.join(lines[start_line - 1:])
            else:
                content = ''.join(lines[start_line - 1:end_line])
            
            self.prompts[name] = content.strip()
            print(f"已从 {file_path} 加载提示词 '{name}' (行 {start_line}-{end_line or '结尾'})")
        except Exception as e:
            print(f"从文件加载提示词失败: {e}")
    
    def list_prompts(self) -> list:
        """
        列出所有可用的提示词名称
        
        Returns:
            提示词名称列表
        """
        return list(self.prompts.keys())
    
    def remove_prompt(self, name: str) -> bool:
        """
        删除提示词
        
        Args:
            name: 提示词名称
            
        Returns:
            是否成功删除
        """
        if name in self.prompts:
            del self.prompts[name]
            return True
        return False
    
    def save_to_file(self, name: str, file_path: str):
        """
        将提示词保存到文件
        
        Args:
            name: 提示词名称
            file_path: 保存路径
        """
        if name not in self.prompts:
            print(f"错误: 提示词 '{name}' 不存在")
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.prompts[name])
            print(f"提示词 '{name}' 已保存到 {file_path}")
        except Exception as e:
            print(f"保存提示词失败: {e}")
    
    def get_prompt_preview(self, name: str, max_length: int = 200) -> Optional[str]:
        """
        获取提示词预览
        
        Args:
            name: 提示词名称
            max_length: 最大预览长度
            
        Returns:
            提示词预览，如果不存在则返回 None
        """
        if name not in self.prompts:
            return None
        
        content = self.prompts[name]
        if len(content) <= max_length:
            return content
        
        return content[:max_length] + "..."


def main():
    """使用示例"""
    
    # 创建提示词管理器
    pm = PromptManager()
    
    print("=" * 60)
    print("提示词管理器使用示例")
    print("=" * 60)
    
    # 1. 列出所有提示词
    print("\n1. 可用的提示词:")
    for prompt_name in pm.list_prompts():
        preview = pm.get_prompt_preview(prompt_name, max_length=100)
        print(f"\n  - {prompt_name}:")
        print(f"    {preview[:50]}...")
    
    # 2. 获取并使用提示词（带变量替换）
    print("\n" + "=" * 60)
    print("2. 使用 ICS 风险分析提示词（路径编号 A7）:")
    print("=" * 60)
    prompt = pm.get_prompt("ics_risk_analysis", PATH_ID="A7")
    print(prompt[:500] + "...\n")
    
    # 3. 添加自定义提示词
    print("\n" + "=" * 60)
    print("3. 添加自定义提示词:")
    print("=" * 60)
    pm.add_prompt("custom", "这是一个自定义提示词，参数：{PARAM}")
    custom_prompt = pm.get_prompt("custom", PARAM="测试值")
    print(f"自定义提示词: {custom_prompt}")
    
    # 4. 从文件加载提示词（示例）
    print("\n" + "=" * 60)
    print("4. 从文件加载提示词:")
    print("=" * 60)
    # 从 think.md 的第 44-194 行加载
    if Path("think.md").exists():
        pm.load_from_file("ics_from_file", "think.md", start_line=44, end_line=194)
        print(f"已加载提示词，长度: {len(pm.get_prompt('ics_from_file'))} 字符")
    else:
        print("think.md 文件不存在，跳过")
    
    # 5. 保存提示词到文件
    print("\n" + "=" * 60)
    print("5. 保存提示词到文件:")
    print("=" * 60)
    pm.save_to_file("system_analysis", "prompt_system_analysis.txt")
    
    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

