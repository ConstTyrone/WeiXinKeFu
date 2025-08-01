# message_formatter.py
import json
from typing import Dict, Any
from datetime import datetime

class MessageFormatter:
    """消息格式化器 - 将各种类型的消息转换为Markdown格式"""
    
    def __init__(self):
        pass
    
    def format_message(self, message: Dict[str, Any], message_type: str) -> str:
        """
        将消息转换为Markdown格式
        
        Args:
            message: 消息对象
            message_type: 消息类型
            
        Returns:
            str: Markdown格式的消息内容
        """
        formatter_map = {
            'general_text': self._format_text,
            'image': self._format_image,
            'file': self._format_file,
            'voice': self._format_voice,
            'video': self._format_video,
            'location': self._format_location,
            'link': self._format_link,
            'miniprogram': self._format_miniprogram,
            'chat_record': self._format_chat_record,
            'event': self._format_event,
            'command': self._format_command
        }
        
        formatter = formatter_map.get(message_type, self._format_unknown)
        return formatter(message)
    
    def _get_user_info(self, message: Dict[str, Any]) -> tuple:
        """提取用户信息"""
        user_id = message.get('FromUserName', '未知用户')
        timestamp = message.get('CreateTime', '')
        if timestamp:
            try:
                dt = datetime.fromtimestamp(int(timestamp))
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = str(timestamp)
        else:
            time_str = '未知时间'
        return user_id, time_str
    
    def _format_text(self, message: Dict[str, Any]) -> str:
        """格式化文本消息"""
        user_id, time_str = self._get_user_info(message)
        content = message.get('Content', '')
        
        return f"""# 📝 文本消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 文本消息

## 消息内容
{content}
"""
    
    def _format_image(self, message: Dict[str, Any]) -> str:
        """格式化图片消息"""
        user_id, time_str = self._get_user_info(message)
        media_id = message.get('MediaId', '')
        
        return f"""# 🖼️ 图片消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 图片消息
**媒体ID**: {media_id}

## 描述
用户发送了一张图片，可以通过媒体ID下载查看具体内容。
"""
    
    def _format_file(self, message: Dict[str, Any]) -> str:
        """格式化文件消息"""
        user_id, time_str = self._get_user_info(message)
        media_id = message.get('MediaId', '')
        title = message.get('Title', '未知文件')
        
        return f"""# 📁 文件消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 文件消息
**文件名**: {title}
**媒体ID**: {media_id}

## 描述
用户发送了一个文件，可以通过媒体ID下载查看具体内容。
"""
    
    def _format_voice(self, message: Dict[str, Any]) -> str:
        """格式化语音消息"""
        user_id, time_str = self._get_user_info(message)
        media_id = message.get('MediaId', '')
        
        return f"""# 🎤 语音消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 语音消息
**媒体ID**: {media_id}

## 描述
用户发送了一条语音消息，可以通过媒体ID下载并进行语音识别处理。
"""
    
    def _format_video(self, message: Dict[str, Any]) -> str:
        """格式化视频消息"""
        user_id, time_str = self._get_user_info(message)
        media_id = message.get('MediaId', '')
        
        return f"""# 🎥 视频消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 视频消息
**媒体ID**: {media_id}

## 描述
用户发送了一个视频，可以通过媒体ID下载查看具体内容。
"""
    
    def _format_location(self, message: Dict[str, Any]) -> str:
        """格式化位置消息"""
        user_id, time_str = self._get_user_info(message)
        location_x = message.get('Location_X', '')
        location_y = message.get('Location_Y', '')
        label = message.get('Label', '未知位置')
        
        return f"""# 📍 位置消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 位置消息

## 位置信息
**位置名称**: {label}
**经度**: {location_x}
**纬度**: {location_y}

## 描述
用户分享了一个地理位置信息。
"""
    
    def _format_link(self, message: Dict[str, Any]) -> str:
        """格式化链接消息"""
        user_id, time_str = self._get_user_info(message)
        title = message.get('Title', '无标题')
        description = message.get('Description', '无描述')
        url = message.get('Url', '')
        
        return f"""# 🔗 链接消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 链接消息

## 链接信息
**标题**: {title}
**描述**: {description}
**链接**: {url}

## 描述
用户分享了一个网页链接。
"""
    
    def _format_miniprogram(self, message: Dict[str, Any]) -> str:
        """格式化小程序消息"""
        user_id, time_str = self._get_user_info(message)
        title = message.get('Title', '无标题')
        app_id = message.get('AppId', '')
        page_path = message.get('PagePath', '')
        
        return f"""# 📱 小程序消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 小程序消息

## 小程序信息
**标题**: {title}
**AppID**: {app_id}
**页面路径**: {page_path}

## 描述
用户分享了一个小程序。
"""
    
    def _format_chat_record(self, message: Dict[str, Any]) -> str:
        """格式化聊天记录消息"""
        user_id, time_str = self._get_user_info(message)
        merged_msg = message.get('merged_msg', {})
        title = merged_msg.get('title', '无标题')
        items = merged_msg.get('item', [])
        
        markdown = f"""# 💬 聊天记录消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 聊天记录
**记录标题**: {title}
**消息条数**: {len(items)}条

## 聊天记录内容
"""
        
        for i, item in enumerate(items, 1):
            sender_name = item.get('sender_name', '未知')
            msg_content = item.get('msg_content', '')
            send_time = item.get('send_time', '')
            
            # 尝试解析消息内容JSON
            try:
                content_json = json.loads(msg_content)
                if content_json.get('msgtype') == 'text':
                    actual_content = content_json.get('text', {}).get('content', msg_content)
                else:
                    actual_content = f"[{content_json.get('msgtype', '未知类型')}消息]"
            except:
                actual_content = msg_content
            
            # 格式化时间
            if send_time:
                try:
                    dt = datetime.fromtimestamp(int(send_time))
                    time_formatted = dt.strftime('%H:%M:%S')
                except:
                    time_formatted = str(send_time)
            else:
                time_formatted = '未知时间'
            
            markdown += f"""
### {i}. {sender_name} ({time_formatted})
{actual_content}
"""
        
        markdown += "\n## 描述\n用户转发了一段聊天记录，包含多人对话内容。"
        return markdown
    
    def _format_event(self, message: Dict[str, Any]) -> str:
        """格式化事件消息"""
        user_id, time_str = self._get_user_info(message)
        event = message.get('Event', '未知事件')
        event_content = message.get('EventContent', {})
        
        return f"""# ⚡ 事件消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 事件消息
**事件类型**: {event}

## 事件详情
{json.dumps(event_content, ensure_ascii=False, indent=2)}

## 描述
系统事件通知。
"""
    
    def _format_command(self, message: Dict[str, Any]) -> str:
        """格式化命令消息"""
        user_id, time_str = self._get_user_info(message)
        content = message.get('Content', '')
        
        return f"""# ⌨️ 命令消息

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: 命令消息

## 命令内容
{content}

## 描述
用户发送了一个系统命令。
"""
    
    def _format_unknown(self, message: Dict[str, Any]) -> str:
        """格式化未知类型消息"""
        user_id, time_str = self._get_user_info(message)
        msg_type = message.get('MsgType', '未知')
        
        return f"""# ❓ 未知消息类型

**用户ID**: {user_id}
**时间**: {time_str}
**消息类型**: {msg_type}

## 原始消息内容
{json.dumps(message, ensure_ascii=False, indent=2)}

## 描述
收到了一个未知类型的消息。
"""

# 全局格式化器实例
formatter = MessageFormatter()