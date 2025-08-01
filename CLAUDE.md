# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

请注意在实现任何有关微信客服时，查看weixin_doc文件夹中的文档

## Project Overview

This is a FastAPI-based webhook service for integrating with WeWork (企业微信) and WeChat Customer Service (微信客服) platforms. The service handles message callbacks from both platforms, classifies different types of messages, and processes them accordingly. The application supports both Enterprise WeChat's direct message delivery and WeChat Customer Service's event-driven message synchronization mechanism.

## Architecture

The application follows a clean, unified message processing architecture:

**Core Processing Flow**: 用户消息 → 解密 → 分类 → 转换为纯文本 → AI提取用户画像 → 存储画像数据

### Core Modules:
- `main.py`: FastAPI application with endpoints for WeWork/WeChat callback verification and message handling
- `wework_client.py`: WeWork/WeChat API client for token management, signature verification, message decryption, and message synchronization
- `message_handler.py`: **Unified message processing pipeline** - orchestrates the entire user profile extraction flow
- `message_classifier.py`: Message classification logic that categorizes incoming messages into types
- `message_formatter.py`: **Text Extractor** - Converts all message types (text, voice, files, chat records) to pure text for AI analysis
- `media_processor.py`: **NEW** - Handles speech-to-text, file content extraction (word/pdf/excel/txt), and media download
- `ai_service.py`: **User Profile Extractor** - Analyzes text content and extracts detailed user profiles using Qwen API
- `config/config.py`: Configuration management using environment variables
- `run.py`: Application startup script

### Key Components

1. **WeWork/WeChat Integration**:

   - Handles signature verification and message decryption for secure communication
   - Supports both Enterprise WeChat (direct message delivery) and WeChat Customer Service (event-driven message sync)
   - Manages access tokens for API calls
2. **User Profile Extraction Pipeline**:

   - **Classification**: Automatically categorizes messages into standardized types (text, image, file, voice, video, location, link, miniprogram, chat_record, event, command)
   - **Text Extraction**: Converts all message types to pure text format for AI analysis
     - Text messages: Direct content extraction
     - Voice messages: Speech-to-text conversion
     - Files: Content extraction from Word/PDF/Excel/TXT documents
     - Chat records: Structured conversation parsing with participant analysis
     - Images: OCR text recognition (framework ready)
   - **AI Analysis**: Feeds extracted text to Qwen (通义千问) API for user profile extraction
   - **Profile Generation**: Extracts detailed user information including name, age, location, occupation, personality, etc.
   - Special handling for WeChat Customer Service events that require calling sync_msg API to retrieve actual message content

3. **Multi-Media Content Processing**:

   - **Speech Recognition**: Framework for converting voice messages to text (ready for API integration)
   - **Document Processing**: Support for extracting text from common file formats
     - TXT files: Multi-encoding support (UTF-8, GBK, GB2312)
     - Word documents: Ready for python-docx integration
     - PDF files: Ready for PyPDF2/pdfplumber integration  
     - Excel files: Ready for openpyxl integration
   - **Media Download**: Automatic downloading of media files via MediaID for processing
   - **OCR Integration**: Framework ready for image text recognition

## User Profile Extraction

The system extracts the following user profile information:

1. **姓名（主键）** - Primary identifier, required field
2. **性别** - Male/Female/Unknown
3. **年龄** - Specific age or age range
4. **电话** - Phone number or other contact information
5. **所在地（常驻地）** - City or region of residence
6. **婚育** - Marital and parental status (已婚已育/已婚未育/未婚/离异/未知)
7. **学历（学校）** - Education level and institutions
8. **公司（行业）** - Current company and industry
9. **职位** - Current position or job title
10. **资产水平** - Asset level (High/Medium/Low/Unknown)
11. **性格** - Personality traits and characteristics

### Supported Input Types for Profile Extraction:
- **Text Messages**: Direct analysis of user conversations
- **Voice Messages**: Speech-to-text → profile extraction  
- **Chat Records**: Multi-participant conversation analysis
- **Files**: Content extraction from documents for profile information
- **Combined Analysis**: Intelligent analysis across multiple message types

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

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
# Method 1: Using uvicorn directly (recommended for development)
uvicorn main:app --host 0.0.0.0 --port 3001 --reload

# Method 2: Using run script
python run.py
```

### Testing
```bash
# Test callback verification
python tests/test_callback_verification.py

# Test signature verification  
python tests/test_wework_signature.py

# Test message callback
python tests/test_message_callback.py
```

### Debug Tools
```bash
# Debug WeWork callback verification
python utils/debug_wework_callback.py

# Check port usage
python utils/check_port.py
```

### Environment Variables
Create a `.env` file with the following variables:
- WEWORK_CORP_ID=your_corp_id (企业ID/微信客服企业ID)
- WEWORK_AGENT_ID=your_agent_id (企业微信应用ID，微信客服可不填)
- WEWORK_SECRET=your_secret (企业微信应用密钥/微信客服Secret)
- WEWORK_TOKEN=your_token
- WEWORK_AES_KEY=your_aes_key
- LOCAL_SERVER_PORT=3001 (optional, defaults to 3001)
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
7. Calls sync_msg API with limit=1 to retrieve the latest message only
8. Converts message format and classifies message by type
9. Extracts text content and sends to AI for user profile analysis
10. Formats AI analysis results and sends back to user via WeChat API

## Recent Bug Fixes (2025-08-01)

### Critical Message Sync Issues Fixed:
1. **Fixed oldest vs newest message problem**: Previously was reading oldest 20 messages instead of newest
2. **Simplified sync logic**: Removed complex pagination optimization that was causing errors
3. **Single message processing**: Now only processes the latest message each time (limit=1)
4. **Added user reply mechanism**: AI analysis results are now sent back to users automatically
5. **Improved message ordering**: When limit=1, uses max() by send_time to ensure we get the actual newest message

### Key Changes Made:
- **message_handler.py**: 
  - Simplified `handle_wechat_kf_event()` to use direct sync with limit=1
  - Added `process_message_and_get_result()` function that returns formatted text for user replies
  - Added automatic message sending back to users with AI analysis results
- **wework_client.py**: 
  - Fixed `sync_kf_messages()` to properly handle limit=1 case
  - When limit=1, uses max() by send_time to get the actual newest message
  - Removed problematic message list reversal logic
- **main.py**: 
  - Removed dependency on broken message_sync_optimizer
  - Simplified sync status endpoint

## Platform Differences

**Enterprise WeChat vs WeChat Customer Service:**

- **Enterprise WeChat**: Direct message delivery - complete message content is sent in the callback
- **WeChat Customer Service**: Event-driven message sync - callback only sends event notification, requiring sync_msg API call to retrieve actual message content

## Supported Message Types

**Enterprise WeChat**: text, image, voice, video, file, location, link, miniprogram, event
**WeChat Customer Service**: text, image, voice, video, file, location, link, miniprogram, msgmenu, event (enter_session, msg_send_fail, user_recall_msg)

## Configuration Notes

For WeChat Customer Service, use the WeChat Customer Service enterprise ID for WEWORK_CORP_ID and WeChat Customer Service Secret for WEWORK_SECRET. WEWORK_AGENT_ID can be left empty for WeChat Customer Service.