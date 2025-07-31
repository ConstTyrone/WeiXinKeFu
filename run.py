#!/usr/bin/env python3
# run.py
import uvicorn
import os

if __name__ == "__main__":
    # 获取端口配置，默认为3002
    port = int(os.getenv("LOCAL_SERVER_PORT", 3001))
    
    # 如果是开发环境且需要热重载，则使用导入字符串方式
    if os.getenv("ENVIRONMENT") == "development":
        uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
    else:
        # 生产环境直接导入应用
        from main import app
        uvicorn.run(app, host="0.0.0.0", port=port)