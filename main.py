# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import xml.etree.ElementTree as ET
import logging
import sys
from wework_client import wework_client
from message_handler import classify_and_handle_message, parse_message, handle_wechat_kf_event

# 添加请求日志中间件
async def log_requests(request: Request, call_next):
    logger.info(f"收到请求: {request.method} {request.url}")
    logger.info(f"请求头: {dict(request.headers)}")
    
    # 如果是POST请求，记录请求体
    if request.method == "POST":
        body = await request.body()
        logger.info(f"请求体长度: {len(body)} 字节")
        if len(body) < 1000:  # 只记录较短的请求体
            logger.info(f"请求体内容: {body.decode()}")
        else:
            logger.info(f"请求体内容(前100字符): {body[:100].decode()}")
    
    response = await call_next(request)
    logger.info(f"响应状态码: {response.status_code}")
    return response

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

app = FastAPI()

# 注册中间件
app.middleware("http")(log_requests)

logger = logging.getLogger(__name__)

@app.get("/wework/callback")
async def wework_verify(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    """微信客服/企业微信验证回调"""
    logger.info(f"收到验证请求: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}, echostr={echostr}")
    
    try:
        # 验证签名 - 微信客服URL验证不包含echostr参数
        # 为了兼容两种平台，我们尝试两种方式
        is_valid = wework_client.verify_signature(msg_signature, timestamp, nonce)
        logger.info(f"不包含echostr的签名验证结果: {is_valid}")
        
        # 如果标准验证失败，尝试包含echostr的验证（企业微信可能需要）
        if not is_valid:
            is_valid = wework_client.verify_signature(msg_signature, timestamp, nonce, echostr)
            logger.info(f"包含echostr的签名验证结果: {is_valid}")
        
        if not is_valid:
            logger.error("签名验证失败")
            raise HTTPException(status_code=400, detail="签名验证失败")
        
        # 解密echostr
        logger.info("开始解密echostr")
        decrypted = wework_client.decrypt_message(echostr)
        logger.info(f"解密成功，返回明文: {decrypted}")
        
        # 微信客服/企业微信回调验证需要返回解密后的明文
        return PlainTextResponse(decrypted)
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"处理请求时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")

@app.post("/wework/callback")
async def wework_callback(request: Request, msg_signature: str, timestamp: str, nonce: str):
    """微信客服/企业微信消息回调"""
    try:
        # 获取请求体
        body = await request.body()
        logger.info(f"收到消息回调请求，请求体长度: {len(body)} 字节")
        logger.info(f"参数: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}")
        
        # 如果请求体为空，记录警告
        if not body:
            logger.warning("收到空的请求体")
            return PlainTextResponse("success")
        
        root = ET.fromstring(body.decode('utf-8'))
        encrypt_msg = root.find('Encrypt').text
        logger.info(f"提取到的加密消息长度: {len(encrypt_msg) if encrypt_msg else 0} 字符")
        
        # 验证签名
        logger.info(f"开始验证消息签名: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}")
        is_valid = wework_client.verify_signature(msg_signature, timestamp, nonce, encrypt_msg)
        logger.info(f"签名验证结果: {is_valid}")
        
        if not is_valid:
            logger.error("签名验证失败")
            raise HTTPException(status_code=400, detail="签名验证失败")
        
        # 解密消息
        logger.info("开始解密消息")
        decrypted_xml = wework_client.decrypt_message(encrypt_msg)
        logger.info(f"消息解密成功，解密后XML长度: {len(decrypted_xml)} 字符")
        logger.info(f"解密后XML预览: {decrypted_xml[:200]}...")
        
        # 解析消息
        logger.info("开始解析消息")
        message = parse_message(decrypted_xml)
        logger.info(f"消息解析完成: {message}")
        
        # 检查是否为微信客服事件消息
        msg_type = message.get('MsgType')
        event = message.get('Event')
        logger.info(f"消息类型: {msg_type}, 事件: {event}")
        
        if msg_type == 'event' and event == 'kf_msg_or_event':
            # 处理微信客服事件消息
            logger.info("处理微信客服事件消息")
            handle_wechat_kf_event(message)
        else:
            # 分类处理普通消息
            logger.info("分类处理普通消息")
            classify_and_handle_message(message)
        
        logger.info("消息处理完成，返回success")
        return PlainTextResponse("success")
        
    except ET.ParseError as e:
        logger.error(f"XML解析失败: {e}")
        logger.error(f"请求体内容: {await request.body()}")
        return PlainTextResponse("fail")
    except Exception as e:
        logger.error(f"消息处理失败: {e}", exc_info=True)
        return PlainTextResponse("fail")

# 添加根路径测试接口
@app.get("/")
async def root():
    return {"message": "服务器正常运行"}

# 添加一个简单的测试接口
@app.post("/test")
async def test_endpoint(request: Request):
    """测试接口"""
    logger.info("收到测试请求")
    body = await request.body()
    logger.info(f"测试请求体: {body.decode()}")
    return {"status": "success", "message": "测试成功"}

# 添加微信回调的路由，以兼容不同的回调地址
@app.get("/wechat/callback")
async def wechat_verify(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    """微信客服/企业微信验证回调 - 兼容路由"""
    logger.info(f"收到微信验证请求: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}, echostr={echostr}")
    return await wework_verify(msg_signature, timestamp, nonce, echostr)

@app.post("/wechat/callback")
async def wechat_callback(request: Request, msg_signature: str, timestamp: str, nonce: str):
    """微信消息回调 - 兼容路由"""
    logger.info(f"收到微信消息回调请求")
    return await wework_callback(request, msg_signature, timestamp, nonce)