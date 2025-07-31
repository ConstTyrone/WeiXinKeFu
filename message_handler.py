# message_handler.py
from typing import Dict, Any
import logging
import xml.etree.ElementTree as ET
from message_classifier import classifier
from ai_service import qwen_service

logger = logging.getLogger(__name__)

# 用于存储已处理的消息ID，防止重复处理
processed_message_ids = set()

def parse_message(xml_content):
    """解析企业微信消息"""
    root = ET.fromstring(xml_content)
    message = {}
    for child in root:
        message[child.tag] = child.text
    return message

def classify_and_handle_message(message: Dict[str, Any]):
    """分类并处理消息"""
    try:
        user_id = message.get('FromUserName')
        
        # 记录原始消息内容用于调试
        msg_type = message.get('MsgType', 'unknown')
        content = message.get('Content', '')
        logger.info(f"原始消息信息 - 用户: {user_id}, 类型: {msg_type}, 内容: {content[:100]}...")
        print(f"📝 原始消息信息 - 用户: {user_id}, 类型: {msg_type}")
        print(f"   内容预览: {content[:100]}...")
        
        # 分类消息
        message_type = classifier.classify_message(message)
        
        # 记录分类结果
        logger.info(f"用户 {user_id} 发送了 {message_type} 类型的消息")
        print(f"🔍 用户 {user_id} 发送了 {message_type} 类型的消息")
        
        # 根据分类结果处理
        if message_type == 'command':
            logger.info("调用 handle_command")
            print("⌨️ 处理命令消息")
            handle_command(message)
        elif message_type == 'image':
            logger.info("调用 handle_image")
            print("🖼️ 处理图片消息")
            handle_image(message)
        elif message_type == 'file':
            logger.info("调用 handle_file")
            print("📁 处理文件消息")
            handle_file(message)
        elif message_type == 'voice':
            logger.info("调用 handle_voice")
            print("🎤 处理语音消息")
            handle_voice(message)
        elif message_type == 'video':
            logger.info("调用 handle_video")
            print("🎥 处理视频消息")
            handle_video(message)
        elif message_type == 'location':
            logger.info("调用 handle_location")
            print("📍 处理位置消息")
            handle_location(message)
        elif message_type == 'link':
            logger.info("调用 handle_link")
            print("🔗 处理链接消息")
            handle_link(message)
        elif message_type == 'miniprogram':
            logger.info("调用 handle_miniprogram")
            print("📱 处理小程序消息")
            handle_miniprogram(message)
        elif message_type == 'general_text':
            logger.info("调用 handle_general_text")
            print("🤖 开始调用AI处理文本消息")
            handle_general_text(message)
        elif message_type == 'event':
            logger.info("调用 handle_event")
            print("⚡ 处理事件消息")
            handle_event(message)
        else:
            logger.info("调用 handle_unknown")
            print("❓ 处理未知类型消息")
            handle_unknown(message)
            
        print(f"✅ 消息处理完成 - 类型: {message_type}")
            
    except Exception as e:
        logger.error(f"消息处理异常: {e}")
        print(f"❌ 消息处理异常: {e}")


def handle_command(message: Dict[str, Any]):
    """处理命令"""
    user_id = message.get('FromUserName')
    content = message.get('Content')
    
    print(f"[命令] 用户: {user_id}, 命令: {content}")
    
    # 可以实现一些简单的命令响应
    if '帮助' in content or 'help' in content.lower():
        print("用户请求帮助信息")
    elif '状态' in content or 'status' in content.lower():
        print("用户查询状态")

def handle_image(message: Dict[str, Any]):
    """处理图片消息"""
    user_id = message.get('FromUserName')
    media_id = message.get('MediaId')
    
    print(f"[图片] 用户: {user_id}, MediaId: {media_id}")
    print("✅ 图片消息已接收，可以下载并OCR识别")

def handle_file(message: Dict[str, Any]):
    """处理文件消息"""
    user_id = message.get('FromUserName')
    media_id = message.get('MediaId')
    file_name = message.get('Title', 'unknown')
    
    print(f"[文件] 用户: {user_id}, 文件名: {file_name}, MediaId: {media_id}")
    print("✅ 文件消息已接收，可以下载并提取内容")

def handle_voice(message: Dict[str, Any]):
    """处理语音消息"""
    user_id = message.get('FromUserName')
    media_id = message.get('MediaId')
    
    print(f"[语音] 用户: {user_id}, MediaId: {media_id}")
    print("✅ 语音消息已接收，可以下载并转文字")

def handle_general_text(message: Dict[str, Any]):
    """处理普通文本"""
    import json
    user_id = message.get('FromUserName')
    content = message.get('Content')
    
    print(f"[普通文本] 用户: {user_id}")
    print(f"内容: {content}")
    logger.info(f"[普通文本] 用户: {user_id}, 内容: {content}")
    
    # 检查内容是否为空
    if not content or not content.strip():
        print("⚠️ 消息内容为空，跳过AI处理")
        logger.warning("消息内容为空，跳过AI处理")
        return
    
    # 使用通义千问处理消息
    try:
        print("🤖 正在调用通义千问处理消息...")
        logger.info("开始调用通义千问处理消息...")
        print(f"📝 发送给AI的消息内容: {content[:100]}...")
        result = qwen_service.process_message(content)
        
        print(f"✨ AI处理结果:")
        print(f"  📝 消息总结: {result.get('summary', '无')}")
        logger.info(f"AI处理完成，消息总结: {result.get('summary', '无')}")
        
        # 处理新的用户画像格式
        user_profiles = result.get('user_profiles', [])
        if user_profiles:
            print("  👤 提取到的用户画像:")
            for i, profile in enumerate(user_profiles, 1):
                print(f"    {i}. 姓名: {profile.get('name', '未知')}")
                print(f"       性别: {profile.get('gender', '未知')}")
                print(f"       年龄: {profile.get('age', '未知')}")
                print(f"       电话: {profile.get('phone', '未知')}")
                print(f"       所在地: {profile.get('location', '未知')}")
                print(f"       婚育: {profile.get('marital_status', '未知')}")
                print(f"       学历: {profile.get('education', '未知')}")
                print(f"       公司: {profile.get('company', '未知')}")
                print(f"       职位: {profile.get('position', '未知')}")
                print(f"       资产水平: {profile.get('asset_level', '未知')}")
                print(f"       性格: {profile.get('personality', '未知')}")
        else:
            print("  ⚠️ 未提取到用户画像")
            
        # 构造回复消息
        summary = result.get('summary', '无')
        # 清理summary中的多余内容
        if isinstance(summary, str):
            # 移除可能的JSON格式和其他多余内容
            if summary.startswith('{') and summary.endswith('}'):
                try:
                    summary_data = json.loads(summary)
                    summary = summary_data.get('summary', summary)
                except:
                    pass
            # 移除多余的说明文字
            if '\n' in summary:
                summary = summary.split('\n')[0]
        
        reply_content = f"消息总结: {summary}\n"
        if user_profiles:
            reply_content += "提取到的用户画像:\n"
            for i, profile in enumerate(user_profiles, 1):
                name = profile.get('name', '未知')
                position = profile.get('position', '未知')
                company = profile.get('company', '未知')
                
                reply_content += f"{i}. {name}"
                if position != '未知' and position:
                    reply_content += f" ({position})"
                if company != '未知' and company:
                    reply_content += f" @ {company}"
                reply_content += "\n"
                
                # 添加详细信息
                details = []
                detail_mapping = [
                    ('gender', '性别'), ('age', '年龄'), ('phone', '电话'),
                    ('location', '所在地'), ('marital_status', '婚育'),
                    ('education', '学历'), ('asset_level', '资产水平'),
                    ('personality', '性格')
                ]
                
                for key, display_name in detail_mapping:
                    value = profile.get(key, '未知')
                    if value and value != '未知' and value.strip():
                        details.append(f"{display_name}: {value}")
                
                if details:
                    reply_content += "   " + ", ".join(details) + "\n"
        else:
            reply_content += "未提取到用户画像"
        
        print(f"📤 准备发送的回复内容:\n{reply_content}")
        logger.info(f"准备发送的回复内容长度: {len(reply_content)} 字符")
        
        # 发送回复消息
        try:
            from wework_client import wework_client
            # 获取客服账号ID（对于微信客服消息，在ToUserName字段）
            open_kfid = message.get('ToUserName')
            if open_kfid:
                print(f"📤 发送消息到用户: {user_id}, 客服账号: {open_kfid}")
                logger.info(f"发送消息到用户: {user_id}, 客服账号: {open_kfid}")
                result = wework_client.send_text_message(user_id, open_kfid, reply_content)
                print("✅ 回复消息已发送")
                print(f"📨 发送结果: {result}")
                logger.info("✅ 回复消息已发送")
            else:
                print("❌ 无法发送回复消息：缺少客服账号ID")
                logger.error("❌ 无法发送回复消息：缺少客服账号ID")
        except Exception as e:
            logger.error(f"发送回复消息失败: {e}")
            print("❌ 发送回复消息失败")
        
    except Exception as e:
        logger.error(f"AI处理消息时发生错误: {e}")
        print("❌ AI处理失败，请稍后重试")
        
        # 发送错误消息
        try:
            from wework_client import wework_client
            open_kfid = message.get('ToUserName')
            if open_kfid:
                print(f"📤 发送错误消息到用户: {user_id}, 客服账号: {open_kfid}")
                logger.info(f"发送错误消息到用户: {user_id}, 客服账号: {open_kfid}")
                result = wework_client.send_text_message(user_id, open_kfid, "抱歉，消息处理失败，请稍后重试。")
                print("✅ 错误回复已发送")
                print(f"📨 发送结果: {result}")
                logger.info("✅ 错误回复已发送")
        except Exception as send_error:
            logger.error(f"发送错误回复消息失败: {send_error}")
            print("❌ 发送错误回复消息失败")

def handle_event(message: Dict[str, Any]):
    """处理事件消息"""
    user_id = message.get('FromUserName')
    event = message.get('Event')
    event_key = message.get('EventKey')
    
    print(f"[事件消息] 用户: {user_id}, 事件: {event}, 事件Key: {event_key}")
    
    # 打印完整消息内容以便调试
    print("完整事件消息内容:")
    for key, value in message.items():
        print(f"  {key}: {value}")

def handle_unknown(message: Dict[str, Any]):
    """处理未知类型消息"""
    user_id = message.get('FromUserName')
    msg_type = message.get('MsgType')
    
    print(f"[未知类型] 用户: {user_id}, 消息类型: {msg_type}")
    
    # 打印完整消息内容以便调试
    print("完整消息内容:")
    for key, value in message.items():
        print(f"  {key}: {value}")


def handle_wechat_kf_event(message: Dict[str, Any]):
    """处理微信客服事件消息"""
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    corp_id = message.get('ToUserName')
    create_time = message.get('CreateTime')
    event = message.get('Event')
    token = message.get('Token')
    open_kf_id = message.get('OpenKfId')
    
    # 创建事件唯一标识
    event_key = f"{corp_id}_{open_kf_id}_{token}_{create_time}"
    
    # 检查是否已经处理过该事件
    global processed_message_ids
    if event_key in processed_message_ids:
        logger.info(f"事件 {event_key} 已经处理过，跳过重复处理")
        print(f"⚠️ 事件 {event_key} 已经处理过，跳过重复处理")
        return
    
    # 将事件标识添加到已处理集合中
    processed_message_ids.add(event_key)
    # 限制集合大小，避免内存泄漏
    if len(processed_message_ids) > 1000:
        # 移除最早的一半记录
        sorted_ids = sorted(processed_message_ids)
        processed_message_ids = set(sorted_ids[len(sorted_ids)//2:])
    
    logger.info(f"[微信客服事件] 企业ID: {corp_id}, 事件: {event}, 客服账号: {open_kf_id}")
    logger.info(f"Token: {token}, 时间: {create_time}")
    print(f"[微信客服事件] 企业ID: {corp_id}, 事件: {event}, 客服账号: {open_kf_id}")
    print(f"Token: {token}, 时间: {create_time}")
    
    # 直接获取最新消息，不使用游标机制
    try:
        from wework_client import wework_client
        from message_handler import classify_and_handle_message
        logger.info("开始调用sync_kf_messages接口获取最新消息")
        # 获取最近的100条消息（已倒序处理，第一条为最新消息）
        messages = wework_client.sync_kf_messages(token, open_kf_id, limit=100, use_cursor=False)
        logger.info(f"sync_kf_messages调用完成，共获取到 {len(messages)} 条消息")
        print(f"共获取到 {len(messages)} 条消息")
        
        # 检查是否有消息
        if not messages:
            logger.warning("未获取到任何消息")
            print("⚠️ 未获取到任何消息")
            return
        
        # 直接选择最新的消息（倒序后第一条）
        latest_msg = messages[0]
        logger.info(f"处理最新消息: {latest_msg}")
        content_preview = latest_msg.get('text', {}).get('content', '无内容')
        print(f"处理最新消息: {content_preview}")
        
        # 将微信客服消息格式转换为内部格式
        converted_msg = wework_client._convert_kf_message(latest_msg)
        if converted_msg:
            logger.info(f"消息转换成功: {converted_msg}")
            # 添加调试日志
            logger.info(f"转换后的消息类型: {converted_msg.get('MsgType')}")
            logger.info(f"转换后的消息内容: {converted_msg.get('Content', '')[:100]}...")
            print(f"✅ 消息转换成功: {converted_msg.get('Content', '')[:50]}...")
            
            # 分类并处理消息
            print("🔍 开始分类并处理消息...")
            classify_and_handle_message(converted_msg)
            print("✅ 消息分类处理完成")
        else:
            logger.warning("最新消息转换失败")
            print("❌ 消息转换失败")
    except Exception as e:
        logger.error(f"处理微信客服事件失败: {e}", exc_info=True)
        print(f"处理微信客服事件失败: {e}")


def handle_video(message: Dict[str, Any]):
    """处理视频消息"""
    user_id = message.get('FromUserName')
    media_id = message.get('MediaId')
    
    print(f"[视频消息] 用户: {user_id}, MediaId: {media_id}")
    print("✅ 视频消息已接收，可以下载并处理")


def handle_location(message: Dict[str, Any]):
    """处理位置消息"""
    user_id = message.get('FromUserName')
    location_x = message.get('Location_X')
    location_y = message.get('Location_Y')
    label = message.get('Label')
    
    print(f"[位置消息] 用户: {user_id}")
    print(f"位置: {label}, 经纬度: {location_x},{location_y}")


def handle_link(message: Dict[str, Any]):
    """处理链接消息"""
    user_id = message.get('FromUserName')
    title = message.get('Title', '')
    description = message.get('Description', '')
    url = message.get('Url', '')
    
    print(f"[链接消息] 用户: {user_id}")
    print(f"标题: {title}")
    print(f"描述: {description}")
    print(f"链接: {url}")


def handle_miniprogram(message: Dict[str, Any]):
    """处理小程序消息"""
    user_id = message.get('FromUserName')
    title = message.get('Title', '')
    app_id = message.get('AppId', '')
    page_path = message.get('PagePath', '')
    
    print(f"[小程序消息] 用户: {user_id}")
    print(f"标题: {title}")
    print(f"AppId: {app_id}")
    print(f"页面路径: {page_path}")