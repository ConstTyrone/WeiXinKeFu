# main.py
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import xml.etree.ElementTree as ET
import logging
import sys
import json
import time
from ..services.wework_client import wework_client
from ..handlers.message_handler import classify_and_handle_message, parse_message, handle_wechat_kf_event


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

app = FastAPI(title="微信客服用户画像系统", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

# 注册绑定API路由
try:
    from .binding_api import router as binding_router
    app.include_router(binding_router)
    logger.info("绑定API路由注册成功")
except Exception as e:
    logger.warning(f"绑定API路由注册失败: {e}")

# 导入数据库
try:
    from ..database.database_pg import pg_database
    if pg_database.pool:
        db = pg_database
        logger.info("API使用PostgreSQL数据库")
    else:
        raise ImportError("PostgreSQL不可用")
except:
    from ..database.database_sqlite_v2 import database_manager as db
    logger.info("API使用SQLite数据库（备用方案）- 多用户独立存储版本")

# 身份验证
security = HTTPBearer()

# Pydantic模型
class UserLoginRequest(BaseModel):
    wechat_user_id: Optional[str] = None  # 兼容旧版本
    code: Optional[str] = None  # 新增：支持微信登录code

class UserProfile(BaseModel):
    id: int
    profile_name: str
    gender: Optional[str] = None
    age: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    marital_status: Optional[str] = None
    education: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    asset_level: Optional[str] = None
    personality: Optional[str] = None
    ai_summary: Optional[str] = None
    confidence_score: Optional[float] = None
    source_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class UserProfilesResponse(BaseModel):
    total: int
    profiles: List[UserProfile]
    page: int
    page_size: int
    total_pages: int

class UserStatsResponse(BaseModel):
    total_profiles: int
    unique_names: int
    today_profiles: int
    last_profile_at: Optional[str]
    max_profiles: int
    used_profiles: int
    max_daily_messages: int

# 简单的用户验证（生产环境应该使用更安全的JWT或其他认证方式）
def verify_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """验证用户token并返回微信用户ID"""
    try:
        # 这里简化处理，token就是base64编码的微信用户ID
        # 生产环境应该使用JWT或其他安全的认证方式
        import base64
        wechat_user_id = base64.b64decode(credentials.credentials).decode('utf-8')
        
        # 验证用户是否存在
        user_id = db.get_or_create_user(wechat_user_id)
        if user_id:
            return wechat_user_id
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户Token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        logger.error(f"Token验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token验证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/wework/callback")
async def wework_verify(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    """微信客服/企业微信验证回调"""
    import urllib.parse
    logger.info(f"URL验证请求")
    logger.info(f"参数详情 - msg_signature: {msg_signature}, timestamp: {timestamp}, nonce: {nonce}, echostr: {echostr}")
    
    try:
        # URL解码echostr
        echostr_decoded = urllib.parse.unquote(echostr)
        logger.info(f"解码后的echostr: {echostr_decoded}")
        
        # 验证签名 - 微信客服URL验证不包含echostr参数
        # 为了兼容两种平台，我们尝试两种方式
        is_valid = wework_client.verify_signature(msg_signature, timestamp, nonce)
        # 如果标准验证失败，尝试包含echostr的验证（企业微信可能需要）
        if not is_valid:
            is_valid = wework_client.verify_signature(msg_signature, timestamp, nonce, echostr_decoded)
        
        if not is_valid:
            logger.error("签名验证失败")
            raise HTTPException(status_code=400, detail="签名验证失败")
        
        # 解密echostr
        decrypted = wework_client.decrypt_message(echostr_decoded)
        logger.info("URL验证成功")
        
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
        logger.info("收到消息回调")
        
        # 如果请求体为空，记录警告
        if not body:
            logger.warning("收到空的请求体")
            return PlainTextResponse("success")
        
        root = ET.fromstring(body.decode('utf-8'))
        encrypt_msg = root.find('Encrypt').text
        
        # 验证签名
        is_valid = wework_client.verify_signature(msg_signature, timestamp, nonce, encrypt_msg)
        
        if not is_valid:
            logger.error("签名验证失败")
            raise HTTPException(status_code=400, detail="签名验证失败")
        
        # 解密消息
        decrypted_xml = wework_client.decrypt_message(encrypt_msg)
        
        # 解析消息
        message = parse_message(decrypted_xml)
        
        # 检查是否为微信客服事件消息
        msg_type = message.get('MsgType')
        event = message.get('Event')
        
        if msg_type == 'event' and event == 'kf_msg_or_event':
            # 处理微信客服事件消息
            handle_wechat_kf_event(message)
        else:
            # 分类处理普通消息
            classify_and_handle_message(message)
        
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
    return {"status": "success", "message": "测试成功"}

# 添加消息同步状态查看接口
@app.get("/sync/status")
async def get_sync_status():
    """查看消息同步状态"""
    try:
        return {
            "status": "success",
            "message": "消息同步功能已简化，直接获取最新消息",
            "sync_method": "简化版 - 每次仅获取最新1条消息"
        }
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}")
        return {
            "status": "error", 
            "message": str(e)
        }

# 添加微信回调的路由，以兼容不同的回调地址
@app.get("/wechat/callback")
async def wechat_verify(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    """微信客服/企业微信验证回调 - 兼容路由"""
    return await wework_verify(msg_signature, timestamp, nonce, echostr)

@app.post("/wechat/callback")
async def wechat_callback(request: Request, msg_signature: str, timestamp: str, nonce: str):
    """微信消息回调 - 兼容路由"""
    return await wework_callback(request, msg_signature, timestamp, nonce)

# ======================== 前端API接口 ========================

@app.post("/api/login")
async def login(request: UserLoginRequest):
    """用户登录，获取访问token"""
    try:
        import requests
        from ..config.config import config
        
        # 优先使用code进行微信登录
        if request.code:
            logger.info(f"使用微信code登录: {request.code}")
            
            # 检查小程序secret配置
            if not config.wechat_mini_secret:
                logger.warning("微信小程序Secret未配置，尝试使用code作为用户ID（仅限开发环境）")
                # 开发环境：如果没有配置secret，将code作为用户ID使用
                wechat_user_id = f"dev_{request.code[:10]}"
            else:
                # 调用微信API获取openid
                wx_api_url = "https://api.weixin.qq.com/sns/jscode2session"
                params = {
                    "appid": config.wechat_mini_appid,
                    "secret": config.wechat_mini_secret,
                    "js_code": request.code,
                    "grant_type": "authorization_code"
                }
                
                try:
                    response = requests.get(wx_api_url, params=params, timeout=5)
                    wx_data = response.json()
                    
                    if "openid" in wx_data:
                        wechat_user_id = wx_data["openid"]
                        logger.info(f"微信登录成功，获取到openid: {wechat_user_id}")
                        
                        # 可以保存session_key和unionid供后续使用
                        session_key = wx_data.get("session_key")
                        unionid = wx_data.get("unionid")
                    else:
                        # 微信API返回错误
                        error_code = wx_data.get("errcode", -1)
                        error_msg = wx_data.get("errmsg", "未知错误")
                        logger.error(f"微信API错误: {error_msg} (code: {error_code})")
                        
                        # 如果是开发环境的模拟code，使用特殊处理
                        if error_code == 40029 and request.code.startswith("0"):
                            logger.info("检测到开发环境模拟code，使用测试用户ID")
                            wechat_user_id = "dev_user_001"
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"微信登录失败: {error_msg}"
                            )
                except requests.exceptions.RequestException as e:
                    logger.error(f"调用微信API失败: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="调用微信服务失败"
                    )
        
        # 兼容旧版本：直接使用wechat_user_id
        elif request.wechat_user_id:
            wechat_user_id = request.wechat_user_id
            logger.info(f"使用微信用户ID直接登录: {wechat_user_id}")
            
            # 验证用户ID格式（简单验证）
            if not wechat_user_id or len(wechat_user_id) < 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的微信用户ID"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供code或wechat_user_id"
            )
        
        # 创建或获取用户
        user_id = db.get_or_create_user(wechat_user_id)
        
        if user_id:
            # 生成简单token（生产环境应使用JWT）
            import base64
            token = base64.b64encode(wechat_user_id.encode('utf-8')).decode('utf-8')
            
            # 获取用户统计信息
            stats = db.get_user_stats(wechat_user_id)
            
            # 检查绑定状态
            from ..database.binding_db import binding_db
            isBound = False
            external_userid = None
            
            if binding_db:
                binding_info = binding_db.get_user_binding(wechat_user_id)
                if binding_info:
                    isBound = binding_info.get('bind_status') == 1
                    external_userid = binding_info.get('external_userid')
                    # 更新最后登录时间
                    binding_db.update_last_login(wechat_user_id)
            
            return {
                "success": True,
                "token": token,
                "wechat_user_id": wechat_user_id,
                "user_id": user_id,
                "stats": stats,
                "openid": wechat_user_id,  # 为了兼容前端
                "isBound": isBound,
                "external_userid": external_userid
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="用户创建失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

@app.get("/api/profiles", response_model=UserProfilesResponse)
async def get_user_profiles(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    current_user: str = Depends(verify_user_token)
):
    """获取用户的画像列表（分页）"""
    try:
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
            
        offset = (page - 1) * page_size
        
        profiles, total = db.get_user_profiles(
            wechat_user_id=current_user,
            limit=page_size,
            offset=offset,
            search=search
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return UserProfilesResponse(
            total=total,
            profiles=[UserProfile(**profile) for profile in profiles],
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取用户画像列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取画像列表失败"
        )

@app.get("/api/profiles/{profile_id}")
async def get_profile_detail(
    profile_id: int,
    current_user: str = Depends(verify_user_token)
):
    """获取用户画像详情"""
    try:
        profile = db.get_user_profile_detail(current_user, profile_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="画像不存在"
            )
        
        return {
            "success": True,
            "profile": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取画像详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取画像详情失败"
        )

@app.delete("/api/profiles/{profile_id}")
async def delete_profile(
    profile_id: int,
    current_user: str = Depends(verify_user_token)
):
    """删除用户画像"""
    try:
        success = db.delete_user_profile(current_user, profile_id)
        
        if success:
            return {"success": True, "message": "画像删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="画像不存在或删除失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除画像失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除画像失败"
        )

@app.get("/api/stats", response_model=UserStatsResponse)
async def get_user_stats(current_user: str = Depends(verify_user_token)):
    """获取用户统计信息"""
    try:
        stats = db.get_user_stats(current_user)
        return UserStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"获取用户统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )

@app.get("/api/search")
async def search_profiles(
    q: str,
    limit: int = 20,
    current_user: str = Depends(verify_user_token)
):
    """搜索用户画像"""
    try:
        if not q or len(q.strip()) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="搜索关键词不能为空"
            )
        
        profiles, total = db.get_user_profiles(
            wechat_user_id=current_user,
            search=q.strip(),
            limit=limit,
            offset=0
        )
        
        return {
            "success": True,
            "total": total,
            "profiles": profiles,
            "query": q.strip()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索画像失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索失败"
        )

@app.get("/api/recent")
async def get_recent_profiles(
    limit: int = 10,
    current_user: str = Depends(verify_user_token)
):
    """获取最近的用户画像"""
    try:
        if limit < 1 or limit > 50:
            limit = 10
            
        profiles, total = db.get_user_profiles(
            wechat_user_id=current_user,
            limit=limit,
            offset=0
        )
        
        return {
            "success": True,
            "profiles": profiles,
            "total": total
        }
        
    except Exception as e:
        logger.error(f"获取最近画像失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取最近画像失败"
        )

@app.get("/api/user/info")
async def get_user_info(current_user: str = Depends(verify_user_token)):
    """获取当前用户信息"""
    try:
        stats = db.get_user_stats(current_user)
        table_name = db._get_user_table_name(current_user)
        
        return {
            "success": True,
            "wechat_user_id": current_user,
            "table_name": table_name,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

# 实时数据更新相关接口
@app.get("/api/updates/check")
async def check_for_updates(
    last_check: Optional[str] = None,
    current_user: str = Depends(verify_user_token)
):
    """检查是否有新的画像数据"""
    try:
        # 获取最新的画像（最近1分钟内）
        profiles, total = db.get_user_profiles(
            wechat_user_id=current_user,
            limit=5,
            offset=0
        )
        
        # 简单检查是否有更新（生产环境可以用更精确的时间戳对比）
        has_updates = total > 0
        
        return {
            "success": True,
            "has_updates": has_updates,
            "latest_profiles": profiles[:3] if has_updates else [],
            "total_profiles": total,
            "check_time": "2025-08-04T" + str(time.time())
        }
        
    except Exception as e:
        logger.error(f"检查更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查更新失败"
        )