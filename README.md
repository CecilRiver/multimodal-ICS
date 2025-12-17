# 多模态工业控制系统（ICS）安全分析工具

基于大语言模型（LLM）的工业控制系统安全风险分析与防护措施选择系统。

## 📋 项目简介

本项目通过多模态AI技术（GPT-4o）对工业控制系统进行全流程安全分析：

1. **风险识别** - 分析系统拓扑、识别危险事件和安全功能
2. **要素计算** - 计算安全功能的信息安全性、可靠性和实时性指标
3. **措施优选** - 枚举并优选满足要求的安全防护措施组合

## 🏗️ 系统架构

```
多模态输入 → Stage 1: 风险分析 → Stage 2: 要素计算 → Stage 3: 措施优选 → 最优方案
```

## 🚀 快速开始

### 1. 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量（.env）
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选
```

### 2. 运行工作流

```bash
# 按顺序执行三个阶段
python stage_1_LLM.py  # 多模态风险分析
python stage_2_LLM.py  # 要素值计算
python stage_3_LLM.py  # 措施选择与优化（需要交互输入权重）
```

### 3. 查看结果

```
output/
├── stage 1/
│   ├── stage1_full_output.json      # 完整输出
│   └── safety_functions.json        # 安全功能列表
├── stage 2/
│   └── safety_functions_calculated.json  # 包含要素值
└── stage 3/
    ├── security_measures_selected.json   # 各功能措施组合
    ├── global_measures_combinations.json # 全局组合
    └── optimal_measures_solution.json    # 最优方案
```

## 📦 核心模块

### 主流程模块

| 文件 | 功能 | 说明 |
|------|------|------|
| `stage_1_LLM.py` | 多模态风险分析 | 使用GPT-4o处理图片、表格、文本，识别危险事件和安全功能 |
| `stage_2_LLM.py` | 要素值计算 | 通过LLM调用工具计算信息安全性、可靠性、实时性 |
| `stage_3_LLM.py` | 措施选择优化 | 三阶段工作流：枚举组合→全局搜索→权重优选 |

### 工具模块

| 文件 | 功能 |
|------|------|
| `multimodal_openai_client.py` | OpenAI多模态API客户端 |
| `prompt_manager.py` | 提示词模板管理 |
| `stage1_output_parser.py` | Stage 1输出解析 |
| `ics_tools.py` | ICS要素计算工具集 |
| `security_measures_selector.py` | 安全措施选择器 |
| `llm_workflow_base.py` | LLM工作流基类 |

## 🔬 三阶段工作流详解

### Stage 1: 多模态风险分析

**输入**：
- 图片：系统拓扑图、结构图、控制模型图
- 表格：组件列表、风险列表、风险路径
- 文本：系统说明文档

**输出**：
```json
{
  "hazardous_events": ["E-1: 描述", "E-2: 描述"],
  "safety_functions": [
    {
      "id": "F01",
      "description": "安全功能描述",
      "element_id_set": "01 ∪ 02 ∪ 03",
      "risk_id_set": "R42 ∪ R43"
    }
  ]
}
```

### Stage 2: 要素值计算

**功能**：使用LLM自动调用工具计算每个安全功能的三个要素值

**要素**：
1. **信息安全性** = f(机密性, 完整性, 可用性)
2. **可靠性** = f(危险失效概率, 人因错误, 合规性)
3. **实时性** = 响应时间量化值

**工具调用**：
- `web_search`: 搜索相关标准
- `calculate_information_security`: 计算信息安全性
- `calculate_reliability`: 计算可靠性
- `collect_safety_requirements`: 收集用户要求值

**输出**：每个安全功能包含 `actual` 和 `required` 两组值

### Stage 3: 措施选择与优化

**三个子阶段**：

1. **枚举组合** - 为每个安全功能枚举所有满足条件的措施组合
2. **全局搜索** - 找到能同时满足所有安全功能的措施集合
3. **权重优选** - 基于用户输入的权重，计算并选择最优方案

**可用措施**（11种）：
- 功能安全：设备冗余、内存签名、看门狗、监视、参考传感器、信息冗余
- 信息安全：防火墙、加密技术、安全更新、系统备份、身份认证

**优化目标**：
```
g_total = Σ (w_i × g_i)
g_i = w_rel × reliability + w_rt × realtime + w_is × info_security
```

## 📂 输入数据结构

```
input_data/
├── pictures/              # 系统图片（jpg格式）
├── tables/
│   ├── stage 1/          # 组件、风险、路径表格（Markdown）
│   ├── stage 2/          # 要素量化表（Markdown）
│   └── stage 3/          # 措施列表和要素值表（Markdown）
└── manual/               # 系统说明文档（txt）
```

## 🎯 使用场景

### 分析不同风险路径

修改 `stage_1_LLM.py` 中的路径参数：

```python
user_prompt = pm.get_prompt("ics_risk_analysis", PATH_ID="A1")  # 或 "A15" 等
```

### 自定义要素权重

在 `stage_3_LLM.py` 的 `OptimalMeasuresSelector` 类中修改：

```python
self.element_weights = {
    'reliability': 3 * (10 ** 2),      # 300
    'realtime': 2 * (10 ** 0),         # 2
    'info_security': 1 * (10 ** 3)     # 1000
}
```

### 交互式/自动模式

Stage 2 在 `collect_safety_requirements` 中设置 `interactive` 参数：
- `True`: 手动输入要求值
- `False`: 使用默认值

## ⚙️ 配置文件

### .env

```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选
```

### prompts.yaml

提示词模板，支持变量替换（如 `{PATH_ID}`）

## 📊 输出说明

### Stage 1
- `stage1_full_output.json`: 包含原始输出、解析结果、token统计
- `safety_functions.json`: 纯净的安全功能列表

### Stage 2
- `safety_functions_calculated.json`: 包含actual和required值

### Stage 3
- `security_measures_selected.json`: 各功能的措施组合
- `global_measures_combinations.json`: 全局措施组合（满足所有功能）
- `optimal_measures_solution.json`: 最优方案（含配置、排名、详细计算）

## 🔧 开发扩展

### 添加新工具

在 `ics_tools.py` 中添加方法并注册到工具定义：

```python
def new_tool(self, param: str) -> Dict[str, Any]:
    """工具功能说明"""
    return {"success": True, "result": ...}

@staticmethod
def get_tool_definitions() -> List[Dict]:
    # 添加工具定义
```

### 使用基类重构

继承 `llm_workflow_base.py` 中的基类获得通用功能：

```python
from llm_workflow_base import LLMWorkflowBase, DataLoaderMixin

class MyWorkflow(LLMWorkflowBase, DataLoaderMixin):
    # 自动获得环境设置、LLM交互、文件保存等功能
```

## 📝 注意事项

1. **API费用** - GPT-4o处理多模态数据成本较高
2. **响应时间** - Stage 1首次调用可能需要30-60秒
3. **组合数量** - Stage 3检查2^11=2048种组合，耗时较长
4. **权重输入** - Stage 3需要手动输入每个安全功能的权重
5. **文件结构** - 确保输入数据按指定结构组织

## 🌟 特性

- ✅ 多模态输入（图片、表格、文本）
- ✅ LLM自动调用工具
- ✅ 组合枚举与最小集过滤
- ✅ 加权多目标优化
- ✅ 结构化JSON输出
- ✅ 模块化设计，易于扩展

## 📄 License

MIT License

---

**提示**：首次运行建议使用小规模数据测试，确认流程正常后再处理完整数据。
