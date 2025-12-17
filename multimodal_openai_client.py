"""
OpenAI多模态大模型调用脚本
支持处理图片、Markdown表格和文本文件
"""

import os
import base64
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv


class MultimodalDataProcessor:
    """多模态数据处理器"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化OpenAI客户端
        
        Args:
            api_key: OpenAI API密钥，如果不提供则从环境变量OPENAI_API_KEY读取
            base_url: API基础URL，可选（用于自定义端点，如果不提供则从环境变量OPENAI_BASE_URL读取）
        """
        # 首先加载.env文件中的环境变量
        load_dotenv()
        
        # 从参数或环境变量获取配置
        final_api_key = api_key or os.environ.get("OPENAI_API_KEY")
        final_base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=final_api_key,
            base_url=final_base_url
        )
    
    def encode_image(self, image_path: str) -> str:
        """
        将图片编码为base64字符串
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            base64编码的图片字符串
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def read_text_file(self, file_path: str) -> str:
        """
        读取文本文件内容
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            文件内容字符串
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_images_from_directory(self, directory: str) -> List[Dict]:
        """
        从目录加载所有图片
        
        Args:
            directory: 图片目录路径
            
        Returns:
            图片信息列表，包含文件名和base64编码
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        images = []
        
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"警告: 目录 {directory} 不存在")
            return images
        
        for file_path in dir_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                try:
                    base64_image = self.encode_image(str(file_path))
                    images.append({
                        'filename': file_path.name,
                        'data': base64_image
                    })
                    print(f"已加载图片: {file_path.name}")
                except Exception as e:
                    print(f"加载图片 {file_path.name} 失败: {e}")
        
        return images
    
    def load_markdown_tables_from_directory(self, directory: str) -> List[Dict]:
        """
        从目录加载所有Markdown表格文件
        
        Args:
            directory: Markdown文件目录路径
            
        Returns:
            表格信息列表，包含文件名和内容
        """
        tables = []
        
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"警告: 目录 {directory} 不存在")
            return tables
        
        for file_path in dir_path.rglob('*.md'):
            if file_path.is_file():
                try:
                    content = self.read_text_file(str(file_path))
                    tables.append({
                        'filename': file_path.name,
                        'content': content
                    })
                    print(f"已加载表格: {file_path.name}")
                except Exception as e:
                    print(f"加载表格 {file_path.name} 失败: {e}")
        
        return tables
    
    def load_text_files_from_directory(self, directory: str) -> List[Dict]:
        """
        从目录加载所有文本文件
        
        Args:
            directory: 文本文件目录路径
            
        Returns:
            文本信息列表，包含文件名和内容
        """
        texts = []
        
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"警告: 目录 {directory} 不存在")
            return texts
        
        for file_path in dir_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.txt':
                try:
                    content = self.read_text_file(str(file_path))
                    texts.append({
                        'filename': file_path.name,
                        'content': content
                    })
                    print(f"已加载文本: {file_path.name}")
                except Exception as e:
                    print(f"加载文本 {file_path.name} 失败: {e}")
        
        return texts
    
    def build_messages(self, 
                      images: List[Dict], 
                      tables: List[Dict], 
                      texts: List[Dict],
                      user_prompt: str = None) -> List[Dict]:
        """
        构建发送给OpenAI的消息内容
        
        Args:
            images: 图片列表
            tables: 表格列表
            texts: 文本列表
            user_prompt: 用户提示词
            
        Returns:
            消息列表
        """
        content = []
        
        # 添加用户提示词
        if user_prompt:
            content.append({
                "type": "text",
                "text": user_prompt
            })
        
        # 添加文本内容
        if texts:
            text_content = "\n\n=== 文本文件内容 ===\n\n"
            for text in texts:
                text_content += f"【{text['filename']}】\n{text['content']}\n\n"
            content.append({
                "type": "text",
                "text": text_content
            })
        
        # 添加表格内容
        if tables:
            table_content = "\n\n=== 表格内容 ===\n\n"
            for table in tables:
                table_content += f"【{table['filename']}】\n{table['content']}\n\n"
            content.append({
                "type": "text",
                "text": table_content
            })
        
        # 添加图片
        for image in images:
            content.append({
                "type": "text",
                "text": f"\n\n【图片: {image['filename']}】"
            })
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image['data']}"
                }
            })
        
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]
        
        return messages
    
    def call_openai_api(self, 
                       messages: List[Dict],
                       model: str = "gpt-4o",
                       max_tokens: int = 4096,
                       temperature: float = 0.7) -> Dict:
        """
        调用OpenAI API
        
        Args:
            messages: 消息列表
            model: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            API响应结果
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return {
                'success': True,
                'response': response,
                'content': response.choices[0].message.content,
                'usage': response.usage
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_multimodal_data(self,
                               pictures_dir: str = "input_data/pictures",
                               tables_dir: str = "input_data/tables/stage 1",
                               manual_dir: str = "input_data/manual",
                               user_prompt: str = None,
                               model: str = "gpt-4o",
                               max_tokens: int = 4096,
                               temperature: float = 0.7) -> Dict:
        """
        处理多模态数据并调用OpenAI API
        
        Args:
            pictures_dir: 图片目录
            tables_dir: 表格目录
            manual_dir: 文本目录
            user_prompt: 用户提示词
            model: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            API调用结果
        """
        print("=== 开始加载数据 ===")
        
        # 加载所有数据
        images = self.load_images_from_directory(pictures_dir)
        tables = self.load_markdown_tables_from_directory(tables_dir)
        texts = self.load_text_files_from_directory(manual_dir)
        
        print(f"\n数据加载完成:")
        print(f"- 图片: {len(images)} 个")
        print(f"- 表格: {len(tables)} 个")
        print(f"- 文本: {len(texts)} 个")
        
        # 构建消息
        print("\n=== 构建消息 ===")
        messages = self.build_messages(images, tables, texts, user_prompt)
        
        # 调用API
        print("\n=== 调用OpenAI API ===")
        result = self.call_openai_api(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return result


def main():
    """主函数示例"""
    
    # 初始化处理器
    # 可以从环境变量读取API密钥，或者直接传入
    processor = MultimodalDataProcessor(
        # api_key="your-api-key-here",  # 可选：直接设置API密钥
        # base_url="https://api.openai.com/v1"  # 可选：自定义API端点
    )
    
    # 自定义提示词
    user_prompt = """
    请分析以下燃气管网测试系统的相关资料，包括：
    1. 系统的物理结构、拓扑图和控制结构
    2. 系统组件列表
    3. 系统的安全风险和安全隐患
    4. 系统的风险路径
    5. 系统的详细使用说明
    
    请基于这些资料，给出对该燃气管网测试系统的全面分析，包括系统架构、安全风险评估和建议。
    """
    
    # 处理数据并调用API
    result = processor.process_multimodal_data(
        pictures_dir="input_data/pictures",
        tables_dir="input_data/tables/stage 1",
        manual_dir="input_data/manual",
        user_prompt=user_prompt,
        model="gpt-4o",  # 或使用 "gpt-4o-mini"、"gpt-4-turbo" 等
        max_tokens=4096,
        temperature=0.7
    )
    
    # 处理结果
    if result['success']:
        print("\n" + "="*50)
        print("API调用成功!")
        print("="*50)
        print(f"\n模型响应:\n{result['content']}")
        print(f"\n\nToken使用情况:")
        print(f"- 提示tokens: {result['usage'].prompt_tokens}")
        print(f"- 完成tokens: {result['usage'].completion_tokens}")
        print(f"- 总计tokens: {result['usage'].total_tokens}")
    else:
        print("\n" + "="*50)
        print("API调用失败!")
        print("="*50)
        print(f"错误信息: {result['error']}")


if __name__ == "__main__":
    main()

