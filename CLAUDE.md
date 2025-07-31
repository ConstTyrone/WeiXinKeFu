# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

请注意在实现任何有关微信客服时，查看wenxin_doc文件夹中的文档

## Project Overview

This is a FastAPI-based webhook service for integrating with WeWork (企业微信) and WeChat Customer Service (微信客服) platforms. The service handles message callbacks from both platforms, classifies different types of messages, and processes them accordingly. The application supports both Enterprise WeChat's direct message delivery and WeChat Customer Service's event-driven message synchronization mechanism.

## Architecture

The application follows a modular structure:

- `main.py`: FastAPI application with endpoints for WeWork/WeChat callback verification and message handling
- `wework_client.py`: WeWork/WeChat API client for token management, signature verification, message decryption, and message synchronization
- `config/config.py`: Configuration management using environment variables
- `message_classifier.py`: Message classification logic that categorizes incoming messages
- `message_handler.py`: Message processing logic for different message types
- `run.py`: Application startup script

### Key Components

1. **WeWork/WeChat Integration**:

   - Handles signature verification and message decryption for secure communication
   - Supports both Enterprise WeChat (direct message delivery) and WeChat Customer Service (event-driven message sync)
   - Manages access tokens for API calls
2. **Message Classification**:

   - Automatically categorizes messages into types (chat records, contact info, commands, images, files, voice, video, location, links, miniprograms, events)
   - Supports both Enterprise WeChat and WeChat Customer Service message formats
3. **Message Processing**:

   - Different handlers for each message type with appropriate business logic
   - Special handling for WeChat Customer Service events that require calling sync_msg API to retrieve actual message content

## Common Development Tasks

### Environment Setup

1. Create a virtual environment: `python -m venv venv`
2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Set environment variables:
   - WEWORK_CORP_ID
   - WEWORK_AGENT_ID
   - WEWORK_SECRET
   - WEWORK_TOKEN
   - WEWORK_AES_KEY
   - LOCAL_SERVER_PORT (optional, defaults to 3001)
   - QWEN_API_KEY (通义千问API密钥)
   - QWEN_API_ENDPOINT (通义千问API端点，默认为https://dashscope.aliyuncs.com/compatible-mode/v1)
   
   You can create a `.env` file based on `.env.example` for easier configuration.

### Running the Application

You can run the application in two ways:

1. Using uvicorn directly:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 3001 --reload
   ```
2. Using the run script:

   ```bash
   python run.py
   ```

### Testing Webhook

The service exposes multiple endpoints for compatibility:

- GET `/wework/callback` - For WeWork callback verification
- POST `/wework/callback` - For handling WeWork message callbacks
- GET `/wechat/callback` - For WeChat Customer Service callback verification (compatibility route)
- POST `/wechat/callback` - For handling WeChat Customer Service message callbacks (compatibility route)

### Adding New Message Types

To add support for new message types:

1. Update `message_classifier.py` to add classification logic
2. Add a new handler function in `message_handler.py`
3. Register the new handler in the `classify_and_handle_message()` function

### Key Implementation Details

1. **WeChat Customer Service Handling**:

   - When receiving a kf_msg_or_event, the system calls `sync_kf_messages()` to retrieve actual message content
   - Messages are converted from WeChat Customer Service format to internal format for consistent processing
2. **Message Decryption**:

   - Supports multiple decryption formats for compatibility between platforms
   - Includes detailed logging for debugging decryption issues
3. **Signature Verification**:

   - Handles both Enterprise WeChat and WeChat Customer Service signature verification methods
   - Provides detailed logging for debugging signature issues
4. **AI Message Processing**: 
   - Uses Qwen (通义千问) API to process text messages
   - Summarizes message content and extracts identity information
   - Automatically sends processed results back to users via WeChat Customer Service/Enterprise WeChat

## Commands for Development

### Running the Application

```bash
# Run with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 3001 --reload

# Or run with the provided script
python run.py
```

### Installing Dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file with the following variables:
- WEWORK_CORP_ID=your_corp_id
- WEWORK_AGENT_ID=your_agent_id
- WEWORK_SECRET=your_secret
- WEWORK_TOKEN=your_token
- WEWORK_AES_KEY=your_aes_key
- LOCAL_SERVER_PORT=3001
- QWEN_API_KEY=your_qwen_api_key
- QWEN_API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1

## Project Structure

```
├── main.py                 # FastAPI应用主文件，包含回调接口
├── wework_client.py        # 企业微信客户端，处理签名验证、消息解密和API调用
├── config/
│   └── config.py           # 配置管理
├── message_classifier.py   # 消息分类器
├── message_handler.py      # 消息处理器
├── ai_service.py           # AI服务，处理通义千问API调用
├── run.py                  # 应用启动脚本
├── requirements.txt        # 项目依赖
├── weixin_doc/             # 微信客服官方文档
└── CLAUDE.md               # 本文件
```

## Message Processing Flow

### Enterprise WeChat Message Flow
1. WeWork sends GET request for URL verification
2. Service verifies signature and decrypts echostr, returns decrypted result
3. WeWork sends POST requests with messages
4. Service verifies message signature and decrypts content
5. Parses XML message content
6. Classifies message by type
7. Executes appropriate message handling logic

### WeChat Customer Service Message Flow
1. WeChat Customer Service sends GET request for URL verification
2. Service verifies signature and decrypts echostr, returns decrypted result
3. When customer sends message, WeChat Customer Service sends POST event notification
4. Service verifies signature and decrypts event content
5. Parses XML event notification
6. Identifies as WeChat Customer Service event (MsgType=event, Event=kf_msg_or_event)
7. Calls sync_msg API to retrieve actual message content
8. Classifies and processes message by type