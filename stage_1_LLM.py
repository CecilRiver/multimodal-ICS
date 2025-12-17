"""
Stage 1: 多模态风险分析
分析ICS系统的风险路径，识别危险事件和安全功能
"""

import json
from pathlib import Path
from multimodal_openai_client import MultimodalDataProcessor
from prompt_manager import PromptManager
from stage1_output_parser import Stage1OutputParser

# 初始化提示词管理器
pm = PromptManager()

# 获取 ICS 风险分析提示词，并指定路径编号
# 可以修改 PATH_ID 参数来分析不同的风险路径，如 "A7", "A8", "A9" 等
user_prompt = pm.get_prompt("ics_risk_analysis", PATH_ID="A1")

# 方式1: 使用环境变量中的API密钥
processor = MultimodalDataProcessor()

# 方式2: 直接传入API密钥（如果不想使用环境变量）
# processor = MultimodalDataProcessor(api_key="sk-your-api-key-here")

# 调用OpenAI多模态API
result = processor.process_multimodal_data(
    pictures_dir="input_data/pictures",
    tables_dir="input_data/tables/stage 1",
    manual_dir="input_data/manual",
    user_prompt=user_prompt,
    model="gpt-4o",  # 可选: gpt-4o-mini, gpt-4-turbo
    max_tokens=4096,
    temperature=0.7
)

# 处理结果
if result['success']:
    print("\n" + "="*80)
    print("模型分析结果:")
    print("="*80)
    print(result['content'])
    print("\n" + "="*80)
    print(f"Token使用情况: 总计 {result['usage'].total_tokens} tokens")
    print("="*80)
    
    # 解析输出
    print("\n" + "="*80)
    print("解析安全功能列表")
    print("="*80)
    
    parser = Stage1OutputParser()
    parsed_data = parser.parse_full_output(result['content'])
    
    safety_functions = parsed_data['safety_functions']
    hazardous_events = parsed_data['hazardous_events']
    
    print(f"\n✅ 解析到 {len(hazardous_events)} 个危险事件")
    print(f"✅ 解析到 {len(safety_functions)} 个安全功能")
    
    # 显示解析结果
    if safety_functions:
        print("\n安全功能列表：")
        for func in safety_functions:
            print(f"\n【{func['id']}】{func['description'][:50]}...")
            print(f"  组件集: {func['element_id_set'][:50]}...")
            print(f"  风险集: {func['risk_id_set'][:50]}...")
    
    # 保存到文件
    output_dir = Path("output/stage 1")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存完整输出
    output_file = output_dir / "stage1_full_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "raw_output": result['content'],
            "hazardous_events": hazardous_events,
            "safety_functions": safety_functions,
            "token_usage": {
                "total_tokens": result['usage'].total_tokens,
                "prompt_tokens": result['usage'].prompt_tokens,
                "completion_tokens": result['usage'].completion_tokens
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 完整结果已保存到: {output_file}")
    
    # 保存安全功能列表（供 stage 2 使用）
    safety_functions_file = output_dir / "safety_functions.json"
    with open(safety_functions_file, 'w', encoding='utf-8') as f:
        json.dump(safety_functions, f, ensure_ascii=False, indent=2)
    
    print(f"💾 安全功能列表已保存到: {safety_functions_file}")
    print("\n" + "="*80)
    
else:
    print(f"错误: {result['error']}")






