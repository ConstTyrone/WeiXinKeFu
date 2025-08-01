# ai_service.py
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
    
    def process_message(self, message_content):
        """
        使用通义千问处理消息内容，总结消息并提取身份信息
        
        Args:
            message_content (str): 用户发送的消息内容
            
        Returns:
            dict: 包含消息总结和身份信息的字典
        """
        try:
            # 构造提示词
            prompt = f"""
            请分析以下用户消息，并构建详细的用户画像：
            "{message_content}"
            
            请从消息中提取以下用户画像信息：
            
            1. 姓名（主键）- 必填
            2. 性别 - 男/女/未知
            3. 年龄 - 具体年龄或年龄段
            4. 电话 - 手机号或其他联系方式
            5. 所在地（常驻地）- 城市或地区
            6. 婚育 - 已婚已育/已婚未育/未婚/离异/未知
            7. 学历（学校）- 最高学历及毕业院校
            8. 公司（行业）- 当前就职公司及所属行业
            9. 职位 - 当前职位或职务
            10. 资产水平 - 高/中/低/未知
            11. 性格 - 描述用户的性格特征
            
            请以JSON格式返回结果，格式如下：
            {{
                "summary": "消息的主要内容总结（不超过50个字）",
                "user_profiles": [
                    {{
                        "name": "姓名",
                        "gender": "性别",
                        "age": "年龄",
                        "phone": "电话",
                        "location": "所在地",
                        "marital_status": "婚育情况",
                        "education": "学历（学校）",
                        "company": "公司（行业）",
                        "position": "职位",
                        "asset_level": "资产水平",
                        "personality": "性格描述"
                    }}
                ]
            }}
            
            注意事项：
            1. 如果某些信息无法从消息中提取，请填写"未知"
            2. 只提取消息中明确提到的信息，不要推测
            3. 如果消息中提到了多个人物，请为每个人物创建一个用户画像
            4. summary字段请用简短语言总结消息的主要内容
            """
            
            # 构造请求数据
            data = {
                "model": "qwen-max",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            # 发送请求到通义千问API
            logger.info("正在调用通义千问API处理消息")
            logger.info(f"发送给AI的消息内容预览: {message_content[:100]}...")
            response = requests.post(
                f"{self.api_endpoint}/chat/completions",
                headers=self.headers,
                data=json.dumps(data),
                timeout=30  # 设置30秒超时
            )
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                logger.info("成功获取通义千问API响应")
                
                # 解析响应内容
                ai_response = result['choices'][0]['message']['content']
                logger.info(f"AI原始响应: {ai_response[:200]}...")
                
                # 尝试解析JSON
                try:
                    # 保存原始响应用于调试
                    original_response = ai_response
                    
                    # 处理可能的markdown代码块格式
                    if ai_response.startswith("```json"):
                        ai_response = ai_response[7:]
                    if ai_response.endswith("```"):
                        ai_response = ai_response[:-3]
                    
                    # 尝试找到JSON的开始和结束位置
                    start_pos = ai_response.find('{')
                    end_pos = ai_response.rfind('}')
                    
                    if start_pos != -1 and end_pos != -1 and end_pos > start_pos:
                        json_str = ai_response[start_pos:end_pos+1]
                        parsed_result = json.loads(json_str)
                        logger.info("✅ AI响应解析成功")
                        return parsed_result
                    else:
                        raise json.JSONDecodeError("No valid JSON found", ai_response, 0)
                        
                except json.JSONDecodeError:
                    # 如果JSON解析失败，返回原始响应
                    logger.warning("无法解析AI响应为JSON格式")
                    logger.warning(f"原始AI响应: {original_response}")
                    return {
                        "summary": "AI处理完成，但无法解析详细结果",
                        "user_profiles": []
                    }
            else:
                logger.error(f"通义千问API调用失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return {
                    "summary": "AI处理失败",
                    "user_profiles": []
                }
                
        except requests.exceptions.Timeout:
            logger.error("通义千问API调用超时")
            return {
                "summary": "AI处理超时",
                "user_profiles": []
            }
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")
            return {
                "summary": "处理过程中发生错误",
                "user_profiles": []
            }

# 全局实例
qwen_service = QwenService()