# ai_service_new.py
import requests
import json
from config.config import config
import logging

logger = logging.getLogger(__name__)

class QwenService:
    def __init__(self):
        self.api_key = config.qwen_api_key
        self.api_endpoint = config.qwen_api_endpoint
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def process_message(self, markdown_content: str) -> dict:
        """
        处理Markdown格式的消息内容
        
        Args:
            markdown_content (str): Markdown格式的消息内容
            
        Returns:
            dict: 包含success状态、回复内容和分析结果的字典
        """
        try:
            # 构造智能的提示词
            prompt = f"""
作为一个智能客服助手，请分析以下用户消息并提供合适的回复：

{markdown_content}

请按照以下要求分析和回复：

1. **消息分析**：
   - 理解用户的意图和需求
   - 识别消息类型和关键信息
   - 分析用户可能的情感状态

2. **回复生成**：
   - 提供友好、专业的回复
   - 回复要简洁明了，不超过200字
   - 根据消息类型给出相应的处理建议或回复

3. **特殊消息处理**：
   - 对于图片/文件/语音等媒体消息：确认收到并简要说明后续处理
   - 对于聊天记录：总结对话要点并给出合适回应
   - 对于位置信息：确认收到位置并给出相关建议
   - 对于链接/小程序：确认收到分享内容

请直接回复用户，不需要JSON格式，语气要自然友好。
            """
            
            # 构造请求数据
            data = {
                "model": "qwen-max",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            logger.info("正在调用通义千问API处理消息")
            logger.info(f"Markdown内容长度: {len(markdown_content)} 字符")
            
            # 发送请求到通义千问API
            response = requests.post(
                f"{self.api_endpoint}/chat/completions",
                headers=self.headers,
                data=json.dumps(data),
                timeout=30
            )
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                logger.info("成功获取通义千问API响应")
                
                # 解析响应内容
                ai_response = result['choices'][0]['message']['content']
                logger.info(f"AI回复预览: {ai_response[:100]}...")
                
                return {
                    "success": True,
                    "reply": ai_response.strip(),
                    "error": None
                }
            else:
                error_msg = f"通义千问API调用失败，状态码: {response.status_code}"
                logger.error(error_msg)
                logger.error(f"响应内容: {response.text}")
                return {
                    "success": False,
                    "reply": "抱歉，AI服务暂时不可用，请稍后重试。",
                    "error": error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "通义千问API调用超时"
            logger.error(error_msg)
            return {
                "success": False,
                "reply": "处理超时，请稍后重试。",
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"处理消息时发生错误: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "reply": "处理失败，请稍后重试。",
                "error": error_msg
            }

# 全局AI服务实例
ai_service = QwenService()