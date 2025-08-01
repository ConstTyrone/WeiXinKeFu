# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

请注意在实现任何有关微信客服时，查看weixin_doc文件夹中的文档

## Project Overview

This is a FastAPI-based webhook service for integrating with WeWork (企业微信) and WeChat Customer Service (微信客服) platforms. The service handles message callbacks from both platforms, classifies different types of messages, and processes them accordingly with AI-powered user profile extraction. The application supports both Enterprise WeChat's direct message delivery and WeChat Customer Service's event-driven message synchronization mechanism.

## Architecture

The application follows a clean, unified message processing architecture:

**Core Processing Flow**: 用户消息 → 解密 → 分类 → 转换为纯文本 → AI提取用户画像 → 存储画像数据

### Core Modules:
- `main.py`: FastAPI application with endpoints for WeWork/WeChat callback verification and message handling
- `wework_client.py`: WeWork/WeChat API client for token management, signature verification, message decryption, and message synchronization
- `message_handler.py`: **Unified message processing pipeline** - orchestrates the entire user profile extraction flow
- `message_classifier.py`: Message classification logic that categorizes incoming messages into types
- `message_formatter.py`: **Text Extractor** - Converts all message types (text, voice, files, chat records) to pure text for AI analysis
- `media_processor.py`: **Multimedia Processor** - Handles media download, ETL4LM integration for OCR and PDF processing
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

3. **Multi-Media Content Processing with ETL4LM Integration**:

   - **ETL4LM API Integration**: Full integration with ETL4LM service for advanced document processing
     - Image OCR: Automatic text extraction from images with timeout handling (3 minutes)
     - PDF Processing: Advanced PDF parsing with formula recognition and timeout handling (5 minutes)
     - Progress tracking and file size estimation for better user experience
   - **Speech Recognition**: Framework for converting voice messages to text (ready for API integration)
   - **Document Processing**: Support for extracting text from common file formats
     - TXT files: Multi-encoding support (UTF-8, GBK, GB2312)
     - Word documents: Ready for python-docx integration
     - PDF files: ETL4LM integration for advanced parsing with OCR and formula support
     - Excel files: Ready for openpyxl integration
   - **Media Download**: Automatic downloading of media files via MediaID for processing
   - **File Type Detection**: Magic number detection for files without metadata

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
# Test ETL integration
python test_etl.py

# Test timeout handling
python test_timeout_handling.py

# Check Python syntax
python -m py_compile *.py
```

### Development Workflow
1. **Adding New Message Types**: Update `message_classifier.py` → Add handler in `message_handler.py` → Add text extraction in `message_formatter.py`
2. **Testing ETL Features**: Send images/PDFs through WeChat → Check logs for processing status → Verify AI analysis results
3. **Debugging**: Enable detailed logging by checking console output during message processing

### Environment Variables
Create a `.env` file with the following variables:
- WEWORK_CORP_ID=your_corp_id (企业ID/微信客服企业ID)
- WEWORK_AGENT_ID=your_agent_id (企业微信应用ID，微信客服可不填)
- WEWORK_SECRET=your_secret (企业微信应用密钥/微信客服Secret)
- WEWORK_TOKEN=your_token
- WEWORK_AES_KEY=your_aes_key
- LOCAL_SERVER_PORT=3001 (optional, defaults to 3001)
- QWEN_API_KEY=your_qwen_api_key (通义千问API密钥)
- QWEN_API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1

### ETL4LM Configuration
The ETL4LM service is pre-configured:
- ETL Base URL: http://110.16.193.170:50103
- Predict Endpoint: /v1/etl4llm/predict
- No additional API keys required for ETL service

## Project Structure

```
├── main.py                 # FastAPI应用主文件，包含回调接口
├── wework_client.py        # 企业微信客户端，处理签名验证、消息解密和API调用
├── config/
│   └── config.py           # 配置管理
├── message_classifier.py   # 消息分类器
├── message_handler.py      # 消息处理器
├── message_formatter.py    # 消息文本提取器
├── media_processor.py      # 多媒体处理器（包含ETL集成）
├── ai_service.py           # AI服务，处理通义千问API调用
├── run.py                  # 应用启动脚本
├── requirements.txt        # 项目依赖
├── weixin_doc/             # 微信客服官方文档
├── reference/              # 技术文档参考
│   └── ETL接口文档.md      # ETL4LM API文档
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

## Recent Updates and Improvements

### ETL4LM Integration (2025-08-01)
1. **Image OCR Processing**: Integrated ETL4LM API for automatic text extraction from images
   - Supports multiple image formats (jpg, png, bmp, tiff, webp)
   - 3-minute timeout with progress tracking
   - Automatic text extraction for user profile analysis

2. **PDF Document Processing**: Advanced PDF parsing with ETL4LM
   - Text layer extraction and OCR when needed
   - Formula recognition support
   - 5-minute timeout for complex documents
   - File size estimation and progress feedback

3. **Enhanced Timeout Handling**:
   - Increased PDF processing timeout from 120s to 300s
   - Added user-friendly error messages with suggestions
   - Progress tracking with time estimation
   - Detailed error categorization (timeout, connection, general)

4. **File Type Detection**: 
   - Magic number detection for files without metadata
   - Handles WeChat Customer Service file messages without filenames
   - Automatic file type identification for proper processing

### Critical Message Sync Issues Fixed (2025-08-01):
1. **Fixed oldest vs newest message problem**: Previously was reading oldest messages instead of newest
2. **Simplified sync logic**: Removed complex pagination optimization that was causing errors
3. **Improved cursor management**: Properly tracks message position for each customer service account
4. **Added user reply mechanism**: AI analysis results are now sent back to users automatically

## Platform Differences

**Enterprise WeChat vs WeChat Customer Service:**

- **Enterprise WeChat**: Direct message delivery - complete message content is sent in the callback
- **WeChat Customer Service**: Event-driven message sync - callback only sends event notification, requiring sync_msg API call to retrieve actual message content

## Supported Message Types

**Enterprise WeChat**: text, image, voice, video, file, location, link, miniprogram, event
**WeChat Customer Service**: text, image, voice, video, file, location, link, miniprogram, msgmenu, event (enter_session, msg_send_fail, user_recall_msg)

## Configuration Notes

For WeChat Customer Service, use the WeChat Customer Service enterprise ID for WEWORK_CORP_ID and WeChat Customer Service Secret for WEWORK_SECRET. WEWORK_AGENT_ID can be left empty for WeChat Customer Service.