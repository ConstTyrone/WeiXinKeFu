# message_formatter_v2.py
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class MessageTextExtractor:
    """消息文本提取器 - 将各种类型的消息转换为纯文本，用于用户画像提取"""
    
    def __init__(self):
        pass
    
    def extract_text(self, message: Dict[str, Any], message_type: str) -> str:
        """
        从消息中提取纯文本内容，用于用户画像分析
        
        Args:
            message: 消息对象
            message_type: 消息类型
            
        Returns:
            str: 提取的纯文本内容
        """
        extractor_map = {
            'general_text': self._extract_text_content,
            'image': self._extract_image_content,
            'file': self._extract_file_content,
            'voice': self._extract_voice_content,
            'video': self._extract_video_content,
            'location': self._extract_location_content,
            'link': self._extract_link_content,
            'miniprogram': self._extract_miniprogram_content,
            'chat_record': self._extract_chat_record_content,
            'event': self._extract_event_content,
            'command': self._extract_command_content
        }
        
        extractor = extractor_map.get(message_type, self._extract_unknown_content)
        return extractor(message)
    
    def _get_user_context(self, message: Dict[str, Any]) -> str:
        """获取用户上下文信息"""
        user_id = message.get('FromUserName', '未知用户')
        timestamp = message.get('CreateTime', '')
        
        if timestamp:
            try:
                dt = datetime.fromtimestamp(int(timestamp))
                time_str = dt.strftime('%Y年%m月%d日 %H:%M')
            except:
                time_str = '未知时间'
        else:
            time_str = '未知时间'
        
        return f"用户{user_id}在{time_str}"
    
    def _extract_text_content(self, message: Dict[str, Any]) -> str:
        """提取文本消息内容"""
        context = self._get_user_context(message)
        content = message.get('Content', '')
        
        return f"{context}发送了以下文本消息：\n{content}"
    
    def _extract_image_content(self, message: Dict[str, Any]) -> str:
        """提取图片消息信息（暂时返回基本信息，后续可实现OCR）"""
        context = self._get_user_context(message)
        media_id = message.get('MediaId', '')
        
        # TODO: 实现图片OCR文字识别
        return f"{context}发送了一张图片（MediaID: {media_id}）。注：图片内容需要进一步OCR识别才能获取文字信息。"
    
    def _extract_file_content(self, message: Dict[str, Any]) -> str:
        """提取文件内容"""
        context = self._get_user_context(message)
        media_id = message.get('MediaId', '')
        filename = message.get('Title', '未知文件')
        
        # 根据文件扩展名判断文件类型
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if file_ext in ['txt', 'doc', 'docx', 'pdf', 'xls', 'xlsx']:
            # 使用多媒体处理器提取文件内容
            from media_processor import media_processor
            file_content = media_processor.extract_file_content(media_id, filename)
            
            if file_content and file_content != "[Word文档解析功能待实现]" and file_content != "[PDF文档解析功能待实现]" and file_content != "[Excel文档解析功能待实现]":
                return f"{context}发送了文件《{filename}》，文件内容如下：\n{file_content}"
            else:
                return f"{context}发送了文件《{filename}》（{file_ext.upper()}格式），文件内容提取功能待完善。"
        else:
            return f"{context}发送了文件《{filename}》，文件格式为{file_ext}，暂不支持内容提取。"
    
    
    def _extract_voice_content(self, message: Dict[str, Any]) -> str:
        """提取语音消息内容（通过语音识别转文字）"""
        context = self._get_user_context(message)
        media_id = message.get('MediaId', '')
        
        # 使用多媒体处理器进行语音转文字
        from media_processor import media_processor
        voice_text = media_processor.speech_to_text(media_id)
        
        if voice_text and voice_text != "[语音转文字功能待实现]":
            return f"{context}发送了语音消息，语音内容为：\n{voice_text}"
        else:
            return f"{context}发送了语音消息（MediaID: {media_id}），语音转文字功能待完善。"
    
    
    def _extract_video_content(self, message: Dict[str, Any]) -> str:
        """提取视频消息信息"""
        context = self._get_user_context(message)
        media_id = message.get('MediaId', '')
        
        # TODO: 实现视频内容分析（可选功能）
        return f"{context}发送了一个视频（MediaID: {media_id}）。注：视频内容分析功能待实现。"
    
    def _extract_location_content(self, message: Dict[str, Any]) -> str:
        """提取位置信息"""
        context = self._get_user_context(message)
        location_x = message.get('Location_X', '')
        location_y = message.get('Location_Y', '')
        label = message.get('Label', '未知位置')
        
        return f"{context}分享了位置信息：{label}（经度:{location_x}, 纬度:{location_y}）"
    
    def _extract_link_content(self, message: Dict[str, Any]) -> str:
        """提取链接信息"""
        context = self._get_user_context(message)
        title = message.get('Title', '无标题')
        description = message.get('Description', '无描述')
        url = message.get('Url', '')
        
        return f"{context}分享了链接：《{title}》\n描述：{description}\n链接地址：{url}"
    
    def _extract_miniprogram_content(self, message: Dict[str, Any]) -> str:
        """提取小程序信息"""
        context = self._get_user_context(message)
        title = message.get('Title', '无标题')
        app_id = message.get('AppId', '')
        
        return f"{context}分享了小程序：《{title}》（AppID: {app_id}）"
    
    def _extract_chat_record_content(self, message: Dict[str, Any]) -> str:
        """提取聊天记录内容 - 这是最重要的功能"""
        context = self._get_user_context(message)
        merged_msg = message.get('merged_msg', {})
        title = merged_msg.get('title', '无标题')
        items = merged_msg.get('item', [])
        
        text_content = f"{context}转发了聊天记录：《{title}》\n\n聊天记录内容：\n"
        
        for i, item in enumerate(items, 1):
            sender_name = item.get('sender_name', '未知')
            msg_content = item.get('msg_content', '')
            send_time = item.get('send_time', '')
            
            # 格式化时间
            if send_time:
                try:
                    dt = datetime.fromtimestamp(int(send_time))
                    time_formatted = dt.strftime('%H:%M')
                except:
                    time_formatted = '未知时间'
            else:
                time_formatted = '未知时间'
            
            # 解析消息内容
            try:
                content_json = json.loads(msg_content)
                msg_type = content_json.get('msgtype', '')
                
                if msg_type == 'text':
                    actual_content = content_json.get('text', {}).get('content', msg_content)
                elif msg_type == 'image':
                    actual_content = "[发送了图片]"
                elif msg_type == 'voice':
                    actual_content = "[发送了语音]"
                elif msg_type == 'video':
                    actual_content = "[发送了视频]" 
                elif msg_type == 'file':
                    actual_content = "[发送了文件]"
                elif msg_type == 'location':
                    actual_content = "[分享了位置]"
                elif msg_type == 'link':
                    actual_content = "[分享了链接]"
                elif msg_type == 'miniprogram':
                    actual_content = "[分享了小程序]"
                else:
                    actual_content = f"[{msg_type}消息]"
            except:
                actual_content = msg_content
            
            text_content += f"{i}. {sender_name}（{time_formatted}）：{actual_content}\n"
        
        return text_content
    
    def _extract_event_content(self, message: Dict[str, Any]) -> str:
        """提取事件信息"""
        context = self._get_user_context(message)
        event = message.get('Event', '未知事件')
        
        return f"{context}触发了系统事件：{event}"
    
    def _extract_command_content(self, message: Dict[str, Any]) -> str:
        """提取命令内容"""
        context = self._get_user_context(message)
        content = message.get('Content', '')
        
        return f"{context}发送了命令：{content}"
    
    def _extract_unknown_content(self, message: Dict[str, Any]) -> str:
        """提取未知类型消息"""
        context = self._get_user_context(message)
        msg_type = message.get('MsgType', '未知')
        
        return f"{context}发送了未知类型的消息（类型：{msg_type}）"

# 全局文本提取器实例
text_extractor = MessageTextExtractor()