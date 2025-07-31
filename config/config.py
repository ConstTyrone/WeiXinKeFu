# config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv
import logging

# Load environment variables from .env.test file for testing
load_dotenv(".env.test")
load_dotenv()

# 添加调试信息
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Loaded environment variables:")
logger.info(f"  WEWORK_CORP_ID: {os.getenv('WEWORK_CORP_ID')}")
logger.info(f"  WEWORK_AGENT_ID: {os.getenv('WEWORK_AGENT_ID')}")
logger.info(f"  WEWORK_TOKEN: {os.getenv('WEWORK_TOKEN')}")
logger.info(f"  WEWORK_AES_KEY: {os.getenv('WEWORK_AES_KEY')[:10]}...")  # 只显示前10个字符

@dataclass
class WeWorkConfig:
    corp_id: str = os.getenv('WEWORK_CORP_ID')
    agent_id: str = os.getenv('WEWORK_AGENT_ID')
    secret: str = os.getenv('WEWORK_SECRET')
    token: str = os.getenv('WEWORK_TOKEN')
    encoding_aes_key: str = os.getenv('WEWORK_AES_KEY')
    local_server_port: int = int(os.getenv('LOCAL_SERVER_PORT', 3001))
    # 通义千问API配置
    qwen_api_key: str = os.getenv('QWEN_API_KEY')
    qwen_api_endpoint: str = os.getenv('QWEN_API_ENDPOINT', 'https://dashscope.aliyuncs.com/compatible-mode/v1')

config = WeWorkConfig()

# 添加配置调试信息
logger.info(f"WeWorkConfig initialized:")
logger.info(f"  corp_id: {config.corp_id}")
logger.info(f"  agent_id: {config.agent_id}")
logger.info(f"  token: {config.token}")
logger.info(f"  encoding_aes_key: {config.encoding_aes_key[:10]}...")  # 只显示前10个字符