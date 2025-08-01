# message_handler_new.py
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any
from message_classifier import classifier
from message_formatter import formatter
from ai_service import ai_service

logger = logging.getLogger(__name__)

# AI服务已在ai_service模块中初始化

def parse_message(xml_data: str) -> Dict[str, Any]:
    """解析XML消息数据"""
    try:
        root = ET.fromstring(xml_data)
        message = {}
        
        for child in root:
            if child.text:
                message[child.tag] = child.text.strip()
        
        return message
    except Exception as e:
        logger.error(f"消息解析失败: {e}")
        return {}

def process_message(message: Dict[str, Any]) -> None:
    """
    统一的消息处理流程
    
    流程: 消息 → 分类 → 转Markdown → AI处理 → 回复用户
    """
    try:
        user_id = message.get('FromUserName')
        if not user_id:
            logger.warning("消息中缺少用户ID，跳过处理")
            return
        
        print(f"📨 收到消息 - 用户: {user_id}")
        
        # 步骤1: 分类消息类型
        message_type = classifier.classify_message(message)
        print(f"🔍 消息分类: {message_type}")
        
        # 步骤2: 转换为Markdown格式
        markdown_content = formatter.format_message(message, message_type)
        print(f"📝 已转换为Markdown格式")
        logger.info(f"Markdown内容预览: {markdown_content[:200]}...")
        
        # 步骤3: 发送给AI处理
        print(f"🤖 正在调用AI处理...")
        ai_response = ai_service.process_message(markdown_content)
        
        if ai_response.get('success', False):
            reply_content = ai_response.get('reply', '处理完成，但没有回复内容')
            print(f"✅ AI处理成功")
            logger.info(f"AI回复内容: {reply_content}")
        else:
            reply_content = "抱歉，消息处理失败，请稍后重试。"
            print(f"❌ AI处理失败: {ai_response.get('error', '未知错误')}")
            logger.error(f"AI处理失败: {ai_response}")
        
        # 步骤4: 发送回复给用户
        send_reply_to_user(message, reply_content)
        
        print(f"✅ 消息处理完成 - 类型: {message_type}")
        
    except Exception as e:
        logger.error(f"消息处理过程中发生错误: {e}", exc_info=True)
        print(f"❌ 消息处理失败: {e}")
        
        # 发送错误回复
        try:
            send_reply_to_user(message, "抱歉，消息处理失败，请稍后重试。")
        except Exception as send_error:
            logger.error(f"发送错误回复失败: {send_error}")

def send_reply_to_user(message: Dict[str, Any], reply_content: str) -> None:
    """发送回复消息给用户"""
    try:
        from wework_client import wework_client
        
        user_id = message.get('FromUserName')
        open_kfid = message.get('ToUserName')
        
        if not user_id or not open_kfid:
            logger.error("缺少必要的用户信息，无法发送回复")
            return
        
        print(f"📤 发送回复给用户: {user_id}")
        result = wework_client.send_text_message(user_id, open_kfid, reply_content)
        
        if result and result.get('errcode') == 0:
            print("✅ 回复发送成功")
            logger.info("回复消息发送成功")
        else:
            print(f"❌ 回复发送失败: {result}")
            logger.error(f"回复消息发送失败: {result}")
            
    except Exception as e:
        logger.error(f"发送回复消息时发生错误: {e}", exc_info=True)
        print(f"❌ 发送回复失败: {e}")

def classify_and_handle_message(message: Dict[str, Any]) -> None:
    """
    处理普通消息的入口函数
    """
    process_message(message)

def handle_wechat_kf_event(message: Dict[str, Any]) -> None:
    """
    处理微信客服事件消息
    """
    try:
        # 防重复处理机制
        corp_id = message.get('ToUserName', '')
        open_kfid = message.get('OpenKfId', '')
        token = message.get('Token', '')
        create_time = message.get('CreateTime', '')
        
        event_id = f"{corp_id}_{open_kfid}_{token}_{create_time}"
        
        # 简单的内存去重（生产环境建议使用Redis）
        if not hasattr(handle_wechat_kf_event, '_processed_events'):
            handle_wechat_kf_event._processed_events = set()
        
        if event_id in handle_wechat_kf_event._processed_events:
            print(f"⚠️ 事件 {event_id} 已经处理过，跳过重复处理")
            logger.info(f"事件 {event_id} 已经处理过，跳过重复处理")
            return
        
        handle_wechat_kf_event._processed_events.add(event_id)
        
        print(f"[微信客服事件] 企业ID: {corp_id}, 事件: kf_msg_or_event, 客服账号: {open_kfid}")
        print(f"Token: {token}, 时间: {create_time}")
        
        # 调用sync_kf_messages获取最新消息
        from wework_client import wework_client
        messages = wework_client.sync_kf_messages(token, open_kfid)
        
        if messages:
            print(f"共获取到 {len(messages)} 条消息")
            logger.info(f"sync_kf_messages调用完成，共获取到 {len(messages)} 条消息")
            
            # 处理最新的消息
            latest_msg = messages[0]  # 第一条是最新的
            
            # 转换消息格式
            converted_msg = wework_client._convert_kf_message(latest_msg)
            
            if converted_msg:
                # 使用统一的消息处理流程
                process_message(converted_msg)
            else:
                logger.error("消息转换失败")
                print("❌ 消息转换失败")
        else:
            print("未获取到消息")
            logger.info("sync_kf_messages调用完成，但未获取到消息")
            
    except Exception as e:
        logger.error(f"处理微信客服事件时发生错误: {e}", exc_info=True)
        print(f"❌ 处理微信客服事件失败: {e}")