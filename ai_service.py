# ai_service_v2.py
import requests
import json
from config.config import config
import logging

logger = logging.getLogger(__name__)

class UserProfileExtractor:
    """用户画像提取器 - 基于文本内容分析用户画像"""
    
    def __init__(self):
        self.api_key = config.qwen_api_key
        self.api_endpoint = config.qwen_api_endpoint
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def extract_user_profile(self, text_content: str) -> dict:
        """
        从文本内容中提取用户画像
        
        Args:
            text_content (str): 从消息中提取的纯文本内容
            
        Returns:
            dict: 包含用户画像信息的字典
        """
        try:
            # 构造用户画像提取的提示词
            prompt = f"""
            请分析以下用户消息，并构建详细的用户画像：
            "{text_content}"
            
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
            
            请严格按照以下JSON格式返回结果，不要包含任何注释或解释：
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
            5. 特别关注聊天记录中的个人信息，如姓名、年龄、工作、居住地等
            6. 从语音转换的文字、文件内容、图片OCR结果中提取有价值的用户信息
            7. 请直接返回JSON，不要有任何额外的说明或注释
            8. 对于学历和公司字段，只需要填写核心信息，不要添加过多解释
            """
            
            # 构造请求数据
            data = {
                "model": "qwen-max",
                "messages": [
                    {"role": "system", "content": "你是一个专业的用户画像分析助手。请严格按照要求的JSON格式返回结果，不要包含任何JSON之外的内容、注释或解释。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3  # 降低温度使输出更稳定
            }
            
            logger.info("正在调用通义千问API分析用户画像")
            logger.info(f"文本内容长度: {len(text_content)} 字符")
            logger.info(f"文本内容预览: {text_content[:200]}...")
            
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
                logger.info(f"AI响应长度: {len(ai_response)} 字符")
                logger.info(f"AI原始响应前500字符: {ai_response[:500]}...")
                
                # 如果响应太长，记录完整内容
                if len(ai_response) > 1000:
                    logger.info(f"AI完整响应: {ai_response}")
                
                # 尝试解析JSON
                try:
                    # 保存原始响应用于调试
                    original_response = ai_response
                    
                    # 处理可能的markdown代码块格式
                    if ai_response.startswith("```json"):
                        ai_response = ai_response[7:]
                    if ai_response.endswith("```"):
                        ai_response = ai_response[:-3]
                    
                    # 清理响应中的额外空白字符
                    ai_response = ai_response.strip()
                    
                    # 尝试找到JSON的开始和结束位置
                    start_pos = ai_response.find('{')
                    end_pos = ai_response.rfind('}')
                    
                    logger.info(f"JSON位置: 开始={start_pos}, 结束={end_pos}")
                    
                    if start_pos != -1 and end_pos != -1 and end_pos > start_pos:
                        json_str = ai_response[start_pos:end_pos+1]
                        logger.info(f"提取的JSON字符串长度: {len(json_str)}")
                        
                        # 验证JSON括号匹配
                        brace_count = json_str.count('{') - json_str.count('}')
                        bracket_count = json_str.count('[') - json_str.count(']')
                        
                        if brace_count != 0 or bracket_count != 0:
                            logger.warning(f"JSON括号不匹配: 大括号差={brace_count}, 方括号差={bracket_count}")
                            # 尝试修复截断的JSON
                            if brace_count > 0:
                                json_str += '}' * brace_count
                            if bracket_count > 0:
                                json_str += ']' * bracket_count
                            logger.info("尝试修复JSON括号...")
                        
                        parsed_result = json.loads(json_str)
                        logger.info("✅ 用户画像分析成功")
                        logger.info(f"提取到 {len(parsed_result.get('user_profiles', []))} 个用户画像")
                        
                        return {
                            "success": True,
                            "data": parsed_result,
                            "error": None
                        }
                    else:
                        raise json.JSONDecodeError("No valid JSON found", ai_response, 0)
                        
                except json.JSONDecodeError:
                    # 如果JSON解析失败，返回原始响应
                    logger.warning("无法解析AI响应为JSON格式")
                    logger.warning(f"原始AI响应: {original_response}")
                    return {
                        "success": False,
                        "data": {
                            "summary": "AI处理完成，但无法解析详细结果",
                            "user_profiles": []
                        },
                        "error": "JSON解析失败"
                    }
            else:
                error_msg = f"通义千问API调用失败，状态码: {response.status_code}"
                logger.error(error_msg)
                logger.error(f"响应内容: {response.text}")
                return {
                    "success": False,
                    "data": {
                        "summary": "AI处理失败",
                        "user_profiles": []
                    },
                    "error": error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "通义千问API调用超时"
            logger.error(error_msg)
            return {
                "success": False,
                "data": {
                    "summary": "AI处理超时",
                    "user_profiles": []
                },
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"处理消息时发生错误: {e}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "data": {
                    "summary": "处理失败",
                    "user_profiles": []
                },
                "error": error_msg
            }

# 全局用户画像提取器实例
profile_extractor = UserProfileExtractor()