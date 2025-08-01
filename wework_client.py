# wework_client.py
import hashlib
import base64
import time
import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from config.config import config

class WeWorkClient:
    def __init__(self, config):
        self.config = config
        self._access_token = None
        self._token_expires_at = 0
        # 用于存储不同客服账号的消息游标
        self._kf_cursors = {}
    
    def get_access_token(self):
        """获取access_token"""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
        params = {
            'corpid': self.config.corp_id,
            'corpsecret': self.config.secret
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('errcode') == 0:
            self._access_token = data['access_token']
            self._token_expires_at = time.time() + data.get('expires_in', 7200) - 300
            return self._access_token
        
        raise Exception(f"获取token失败: {data.get('errmsg')}")
    
    def verify_signature(self, signature, timestamp, nonce, encrypt_msg=None):
        """验证签名"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 微信客服/企业微信签名验证需要将token、timestamp、nonce按字典序排序
        params = [self.config.token, timestamp, nonce]
        
        # 对于消息回调，可能需要包含encrypt参数
        if encrypt_msg:
            params.append(encrypt_msg)
        
        params.sort()
        sorted_params = ''.join(params)
        sha1_hash = hashlib.sha1(sorted_params.encode()).hexdigest()
        
        # 签名验证失败时记录错误
        if sha1_hash != signature:
            logger.error(f"签名验证失败 - 期望: {signature}, 实际: {sha1_hash}")
            logger.error(f"参数详情 - token: {self.config.token}, timestamp: {timestamp}, nonce: {nonce}, encrypt_msg: {encrypt_msg}")
            logger.error(f"排序后的参数: {sorted_params}")
        
        return sha1_hash == signature
    
    def decrypt_message(self, encrypt_msg):
        """解密消息"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Base64解码
            msg_bytes = base64.b64decode(encrypt_msg)
            
            # 解码AES密钥
            key = base64.b64decode(self.config.encoding_aes_key + '=')
            
            # 提取IV（前16字节）
            iv = msg_bytes[:16]
            
            # 提取加密数据（16字节之后的部分）
            encrypted_data = msg_bytes[16:]
            
            # 创建AES解密器
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # 解密数据
            decrypted = cipher.decrypt(encrypted_data)
            
            # 尝试去除PKCS#7填充
            try:
                decrypted = unpad(decrypted, AES.block_size)
            except ValueError as pad_error:
                logger.warning(f"去除填充失败: {pad_error}")
                # 如果去除填充失败，尝试直接使用解密后的数据
            
            # 提取消息内容
            # 根据微信平台文档：前16字节为随机字符串，接着4字节为消息长度，后面是消息内容
            # 但实际测试发现格式可能有所不同，需要灵活处理
            
            if len(decrypted) < 20:
                raise Exception("解密后的数据长度不足")
            
            # 尝试标准格式解析
            content_length = int.from_bytes(decrypted[16:20], byteorder='big')
            
            # 检查长度是否合理
            if content_length > 0 and content_length < len(decrypted) - 20:
                content = decrypted[20:20+content_length].decode('utf-8')
                return content
            
            # 如果标准格式失败，尝试另一种可能的格式
            # 直接使用前4字节作为长度（微信客服可能使用这种格式）
            alternative_length = int.from_bytes(decrypted[:4], byteorder='big')
            
            if alternative_length > 0 and alternative_length < len(decrypted) - 4:
                content = decrypted[4:4+alternative_length].decode('utf-8')
                return content
            
            # 如果以上都失败，尝试直接返回剩余数据（特殊情况处理）
            remaining_data = decrypted[20:]  # 跳过前16字节随机字符串和4字节长度字段
            try:
                content = remaining_data.decode('utf-8')
                return content
            except UnicodeDecodeError:
                # 如果还是无法解码，返回十六进制表示
                content_hex = remaining_data.hex()
                return content_hex
            
        except Exception as e:
            logger.error(f"解密过程出错: {e}", exc_info=True)
            raise Exception(f"消息解密失败: {e}")

    def sync_kf_messages(self, token=None, open_kf_id=None, limit=100, get_latest_only=False):
        """
        同步微信客服消息
        
        Args:
            token: 回调事件返回的token
            open_kf_id: 客服账号ID
            limit: 每次拉取的消息数量
            get_latest_only: 是否只获取最新消息（会使用cursor增量拉取）
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 获取access_token
            access_token = self.get_access_token()
            if not access_token:
                raise Exception("无法获取access_token")
            
            # 构造请求URL
            url = f"https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg?access_token={access_token}"
            
            cursor_key = open_kf_id or "default"
            
            # 如果只获取最新消息，使用最优策略
            if get_latest_only:
                # 策略1: 使用游标增量拉取（如果有记录的游标）
                if cursor_key in self._kf_cursors and self._kf_cursors[cursor_key]:
                    # 使用记录的游标进行增量拉取
                    payload = {
                        "token": token,
                        "limit": limit,
                        "cursor": self._kf_cursors[cursor_key]
                    }
                    if open_kf_id:
                        payload["open_kfid"] = open_kf_id
                    
                    logger.info(f"使用游标增量拉取最新消息: {self._kf_cursors[cursor_key]}")
                    logger.info(f"调用sync_msg接口: {url}")
                    logger.info(f"请求参数: {payload}")
                    
                    # 发送POST请求
                    response = requests.post(url, json=payload)
                    result = response.json()
                    
                    # 检查是否有错误
                    if result.get("errcode") != 0:
                        raise Exception(f"sync_msg接口调用失败: {result.get('errmsg')}")
                    
                    # 更新游标
                    if "next_cursor" in result:
                        old_cursor = self._kf_cursors.get(cursor_key, "None")
                        new_cursor = result["next_cursor"]
                        self._kf_cursors[cursor_key] = new_cursor
                        logger.info(f"更新游标: {old_cursor} -> {new_cursor}")
                    
                    # 处理消息列表
                    msg_list = result.get("msg_list", [])
                    logger.info(f"通过sync_msg接口获取消息成功，共收到{len(msg_list)}条消息")
                    
                    if not msg_list:
                        logger.info("没有新消息")
                        return []
                    
                    # 对于增量拉取，API返回的就是从上次cursor之后的新消息
                    # 按时间排序，取最新的一条
                    msg_list.sort(key=lambda x: x.get('send_time', 0), reverse=True)
                    latest_message = msg_list[0]
                    logger.info(f"增量拉取到最新消息: {latest_message.get('msgid', '')} (时间: {latest_message.get('send_time', 0)})")
                    return [latest_message]
                else:
                    # 策略2: 如果没有记录的游标，使用limit=1直接拉取最新消息
                    logger.info("首次拉取或无游标记录，使用limit=1直接拉取最新消息")
                    payload = {
                        "token": token,
                        "limit": 1  # 强制使用limit=1获取最新消息
                    }
                    if open_kf_id:
                        payload["open_kfid"] = open_kf_id
                    
                    logger.info(f"调用sync_msg接口: {url}")
                    logger.info(f"请求参数: {payload}")
                    
                    # 发送POST请求
                    response = requests.post(url, json=payload)
                    result = response.json()
                    
                    # 检查是否有错误
                    if result.get("errcode") != 0:
                        raise Exception(f"sync_msg接口调用失败: {result.get('errmsg')}")
                    
                    # 更新游标
                    if "next_cursor" in result:
                        old_cursor = self._kf_cursors.get(cursor_key, "None")
                        new_cursor = result["next_cursor"]
                        self._kf_cursors[cursor_key] = new_cursor
                        logger.info(f"更新游标: {old_cursor} -> {new_cursor}")
                    
                    # 处理消息列表
                    msg_list = result.get("msg_list", [])
                    logger.info(f"通过sync_msg接口获取消息成功，共收到{len(msg_list)}条消息")
                    
                    if not msg_list:
                        logger.info("没有新消息")
                        return []
                    
                    # 按时间排序，取最新的一条
                    msg_list.sort(key=lambda x: x.get('send_time', 0), reverse=True)
                    latest_message = msg_list[0] if msg_list else None
                    if latest_message:
                        logger.info(f"直接拉取到最新消息: {latest_message.get('msgid', '')} (时间: {latest_message.get('send_time', 0)})")
                        return [latest_message]
                    else:
                        logger.info("未获取到消息")
                        return []
            else:
                # 普通拉取模式
                payload = {
                    "token": token,
                    "limit": limit
                }
                if open_kf_id:
                    payload["open_kfid"] = open_kf_id
                
                # 如果有游标记录，也使用游标
                if cursor_key in self._kf_cursors and self._kf_cursors[cursor_key]:
                    payload["cursor"] = self._kf_cursors[cursor_key]
                    logger.info(f"使用游标进行普通拉取: {self._kf_cursors[cursor_key]}")
                
                logger.info(f"调用sync_msg接口: {url}")
                logger.info(f"请求参数: {payload}")
                
                # 发送POST请求
                response = requests.post(url, json=payload)
                result = response.json()
                
                # 检查是否有错误
                if result.get("errcode") != 0:
                    raise Exception(f"sync_msg接口调用失败: {result.get('errmsg')}")
                
                # 更新游标
                if "next_cursor" in result:
                    old_cursor = self._kf_cursors.get(cursor_key, "None")
                    new_cursor = result["next_cursor"]
                    self._kf_cursors[cursor_key] = new_cursor
                    logger.info(f"更新游标: {old_cursor} -> {new_cursor}")
                
                # 处理消息列表
                msg_list = result.get("msg_list", [])
                logger.info(f"通过sync_msg接口获取消息成功，共收到{len(msg_list)}条消息")
                
                if not msg_list:
                    logger.info("没有新消息")
                    return []
                
                # 普通拉取，按时间倒序排列，最新的在前面
                msg_list.sort(key=lambda x: x.get('send_time', 0), reverse=True)
                logger.info("消息列表已按时间倒序排列，最新的在前面")
                return msg_list
            
        except Exception as e:
            logger.error(f"sync_kf_messages处理失败: {e}", exc_info=True)
            raise Exception(f"同步微信客服消息失败: {e}")

    def _convert_kf_message(self, kf_msg):
        """将微信客服消息格式转换为内部消息格式"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 创建基础消息结构
            converted_msg = {
                "MsgType": kf_msg.get("msgtype", "unknown"),
                "FromUserName": kf_msg.get("external_userid", ""),
                "ToUserName": kf_msg.get("open_kfid", ""),
                "CreateTime": kf_msg.get("send_time", ""),
            }
            
            # 根据消息类型添加具体内容
            msg_type = kf_msg.get("msgtype")
            if msg_type == "text":
                converted_msg["Content"] = kf_msg.get("text", {}).get("content", "")
            elif msg_type == "image":
                converted_msg["MediaId"] = kf_msg.get("image", {}).get("media_id", "")
            elif msg_type == "voice":
                converted_msg["MediaId"] = kf_msg.get("voice", {}).get("media_id", "")
            elif msg_type == "video":
                converted_msg["MediaId"] = kf_msg.get("video", {}).get("media_id", "")
            elif msg_type == "file":
                converted_msg["MediaId"] = kf_msg.get("file", {}).get("media_id", "")
                converted_msg["Title"] = kf_msg.get("file", {}).get("filename", "")
            elif msg_type == "location":
                converted_msg["Location_X"] = kf_msg.get("location", {}).get("latitude", "")
                converted_msg["Location_Y"] = kf_msg.get("location", {}).get("longitude", "")
                converted_msg["Label"] = kf_msg.get("location", {}).get("name", "")
            elif msg_type == "merged_msg":
                # 处理聊天记录消息
                merged_msg_content = kf_msg.get("merged_msg", {})
                converted_msg["merged_msg"] = merged_msg_content
            elif msg_type == "event":
                event_content = kf_msg.get("event", {})
                converted_msg["Event"] = event_content.get("event_type", "")
                converted_msg["OpenKfId"] = event_content.get("open_kfid", "")
                converted_msg["ExternalUserId"] = event_content.get("external_userid", "")
                # 将事件内容添加到消息中
                converted_msg["EventContent"] = event_content
            
            return converted_msg
            
        except Exception as e:
            logger.error(f"消息转换失败: {e}", exc_info=True)
            return None
    
    def send_text_message(self, external_userid, open_kfid, content):
        """发送文本消息到微信客服用户"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 获取access_token
            access_token = self.get_access_token()
            if not access_token:
                raise Exception("无法获取access_token")
            
            # 构造请求URL
            url = f"https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg?access_token={access_token}"
            
            # 构造请求参数
            payload = {
                "touser": external_userid,
                "open_kfid": open_kfid,
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
                        
            logger.info(f"发送文本消息: {url}")
            logger.info(f"请求参数: {payload}")
            
            # 发送POST请求
            response = requests.post(url, json=payload)
            result = response.json()
            
            logger.info(f"发送消息接口返回: {result}")
            
            # 检查是否有错误
            if result.get("errcode") != 0:
                raise Exception(f"发送消息接口调用失败: {result.get('errmsg')}")
            
            return result
            
        except Exception as e:
            logger.error(f"发送文本消息失败: {e}", exc_info=True)
            raise Exception(f"发送文本消息失败: {e}")
    
   
            

wework_client = WeWorkClient(config)