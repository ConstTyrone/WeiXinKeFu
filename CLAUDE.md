# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

请注意在实现任何有关微信客服时，查看weixin_doc文件夹中的文档

## Project Overview

This is a FastAPI-based webhook service for integrating with WeWork (企业微信) and WeChat Customer Service (微信客服) platforms. The service handles message callbacks from both platforms, classifies different types of messages, and processes them accordingly with AI-powered user profile extraction and multimedia content processing. The application supports both Enterprise WeChat's direct message delivery and WeChat Customer Service's event-driven message synchronization mechanism.

## Architecture

The application follows a clean, unified message processing architecture:

**Core Processing Flow**: 用户消息 → 解密 → 分类 → 转换为纯文本 → AI提取用户画像 → 存储画像数据

### Core Modules:
- `main.py`: FastAPI application with endpoints for WeWork/WeChat callback verification and message handling
- `wework_client.py`: WeWork/WeChat API client for token management, signature verification, message decryption, and message synchronization
- `message_handler.py`: **Unified message processing pipeline** - orchestrates the entire user profile extraction flow
- `message_classifier.py`: Message classification logic that categorizes incoming messages into types
- `message_formatter.py`: **Text Extractor** - Converts all message types (text, voice, files, chat records) to pure text for AI analysis
- `media_processor.py`: **Multimedia Processor** - Handles media download, ETL4LM integration for OCR and PDF processing, voice recognition using Alibaba Cloud ASR
- `ai_service.py`: **User Profile Extractor** - Analyzes text content and extracts detailed user profiles using Qwen API
- `database.py`: **User Profile Database** - SQLite database for storing and managing user profile data (deprecated)
- `database_pg.py`: **PostgreSQL User Profile Database** - Multi-user PostgreSQL database system with quota management
- `db_viewer.py`: **Database Management Tool** - Interactive CLI tool for SQLite database (deprecated)
- `db_viewer_pg.py`: **PostgreSQL Database Management Tool** - Advanced CLI tool for PostgreSQL database management
- `message_sync_optimizer.py`: **Message Sync Optimizer** - Handles pagination and deduplication for WeChat Customer Service message sync
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

3. **Multi-Media Content Processing with ETL4LM and ASR Integration**:
   - **ETL4LM API Integration**: Full integration with ETL4LM service for advanced document processing
     - Image OCR: Automatic text extraction from images with timeout handling (3 minutes)
     - PDF Processing: Advanced PDF parsing with formula recognition and timeout handling (5 minutes)
     - Progress tracking and file size estimation for better user experience
   - **Speech Recognition**: Alibaba Cloud ASR integration for voice messages
     - AMR format support with automatic conversion to PCM using ffmpeg
     - Real-time streaming recognition with WebSocket connection
     - Asynchronous processing with callback handling
   - **Document Processing**: Support for extracting text from common file formats
     - TXT files: Multi-encoding support (UTF-8, GBK, GB2312)
     - Word documents: Ready for python-docx integration
     - PDF files: ETL4LM integration for advanced parsing with OCR and formula support
     - Excel files: Ready for openpyxl integration
   - **Media Download**: Automatic downloading of media files via MediaID for processing
   - **File Type Detection**: Magic number detection for files without metadata

4. **User Profile Database System**:
   - **PostgreSQL Database**: Advanced multi-user storage system for user profiles
     - Separate user profile collections for each WeChat user
     - User quota management (profile limits, daily message limits)
     - Full-text search with Chinese language support
     - Confidence score calculation for profile completeness
     - Message processing logs with performance metrics
     - Tag system for profile categorization
   - **Database Features**:
     - Connection pooling for high concurrency
     - JSONB storage for flexible metadata
     - Automatic timestamp management with triggers
     - Views for statistics and usage analytics
     - Indexed fields for fast querying
   - **Automatic Storage**: Every successful AI analysis is automatically saved
     - User isolation: each user's profiles stored separately
     - Duplicate detection: updates existing profiles by name
     - Full audit trail with raw message and AI response storage
   - **Management Tools**: Advanced CLI tool for database operations
     - Multi-user support with user switching
     - Full-text search across profiles
     - Detailed profile viewing with all metadata
     - User statistics and quota monitoring
     - Batch operations support

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
- **Chat Records**: Deep recursive analysis with multimedia content extraction
  - **Smart Target Detection**: Automatically identifies and analyzes only the target person (not the forwarder)
  - **Multimedia Support**: Full processing of images (OCR), voice (speech-to-text), files (content extraction), locations, and links within chat records
  - **Advanced AI Prompting**: Specialized prompts for chat record analysis focusing on the other party
  - **Real-time Media Processing**: Chat record media files are processed in real-time during analysis
- **Files**: Content extraction from documents for profile information
- **Combined Analysis**: Intelligent analysis across multiple message types

## Commands for Development

### Installing Dependencies
```bash
# Install core dependencies
pip install -r requirements.txt

# For voice recognition support (optional)
pip install alibabacloud-nls-python-sdk

# Create virtual environment (recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
```

### Running the Application
```bash
# Method 1: Using uvicorn directly (recommended for development)
uvicorn main:app --host 0.0.0.0 --port 3001 --reload

# Method 2: Using run script
python run.py
```

### Testing and Validation
```bash
# Check Python syntax for all files
python -m py_compile *.py
python -m py_compile config/*.py

# Validate configuration
python -c "from config.config import config; print('配置验证成功')"

# Test webhook endpoints locally
curl -X GET "http://localhost:3001/"
curl -X POST "http://localhost:3001/test"
```

### Database Management
```bash
# PostgreSQL database management (recommended)
python db_viewer_pg.py

# PostgreSQL operations available:
# - Multi-user profile management
# - Full-text search with Chinese support
# - User statistics and quota monitoring
# - Profile detail viewing with metadata
# - Batch operations

# Legacy SQLite database viewer (deprecated)
python db_viewer.py
```

### Common Development Workflows

1. **Adding New Message Types**:
   - Update `message_classifier.py` to add classification logic
   - Add handler function in `message_handler.py`
   - Add text extraction logic in `message_formatter.py` if needed
   - Update AI prompts in `ai_service.py` if specific handling is required

2. **Testing WeChat Customer Service Integration**:
   - Ensure environment variables are set correctly
   - Run the service: `python run.py`
   - Configure callback URL in WeChat Customer Service admin panel
   - Send test messages through WeChat Customer Service
   - Check console logs for processing status

3. **Debugging Message Processing**:
   - Enable detailed logging in console output
   - Check decryption logs for signature/encryption issues
   - Verify token management for API access
   - Monitor AI response parsing for profile extraction

4. **ETL4LM Integration Testing**:
   - Send images/PDFs through WeChat Customer Service
   - Monitor console for ETL processing status (3min timeout for images, 5min for PDFs)
   - Check timeout handling for large files
   - Verify OCR/text extraction results in AI analysis output

## Environment Configuration

Create a `.env` file with the following variables:

### Required Variables
```bash
# WeWork/WeChat Customer Service Credentials
WEWORK_CORP_ID=your_corp_id              # 企业ID/微信客服企业ID
WEWORK_SECRET=your_secret                # 企业微信应用密钥/微信客服Secret
WEWORK_TOKEN=your_token                  # 回调Token
WEWORK_AES_KEY=your_aes_key             # 加密AES Key

# AI Service
QWEN_API_KEY=your_qwen_api_key          # 通义千问API密钥
```

### Optional Variables
```bash
# Enterprise WeChat Only
WEWORK_AGENT_ID=your_agent_id           # 企业微信应用ID（微信客服不需要）

# Server Configuration
LOCAL_SERVER_PORT=3001                  # 默认: 3001

# AI Service Endpoint
QWEN_API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1

# Voice Recognition (Alibaba Cloud ASR)
ASR_APPKEY=NM5zdrGkIl8xqSzO           # 默认已配置
ASR_TOKEN=your_asr_token               # 需要提供有效Token
ASR_URL=wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1

# Media Processing
FFMPEG_PATH=your_ffmpeg_path           # 可选，默认使用系统PATH
DATABASE_PATH=user_profiles.db         # SQLite数据库文件路径（已弃用）

# PostgreSQL Database (新增)
DATABASE_URL=postgresql://user:password@localhost:5432/user_profiles_db
```

### ETL4LM Configuration (Pre-configured)
```
ETL Base URL: http://110.16.193.170:50103
Predict Endpoint: /v1/etl4llm/predict
```

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
├── database.py             # 用户画像数据库管理器
├── db_viewer.py            # 数据库查看和管理工具
├── message_sync_optimizer.py # 消息同步优化器
├── run.py                  # 应用启动脚本
├── requirements.txt        # 项目依赖
├── .env.example            # 环境变量示例
├── .env.test               # 测试环境配置
├── weixin_doc/             # 微信客服官方文档
├── reference/              # 技术文档参考
│   ├── ETL接口文档.md      # ETL4LM API文档
│   └── 阿里asr文档.md      # 阿里云ASR文档
├── user_profiles.db        # SQLite数据库文件（自动创建）
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

## Platform Differences

**Enterprise WeChat vs WeChat Customer Service:**

- **Enterprise WeChat**: Direct message delivery - complete message content is sent in the callback
- **WeChat Customer Service**: Event-driven message sync - callback only sends event notification, requiring sync_msg API call to retrieve actual message content

## Supported Message Types

**Enterprise WeChat**: text, image, voice, video, file, location, link, miniprogram, event
**WeChat Customer Service**: text, image, voice, video, file, location, link, miniprogram, msgmenu, event (enter_session, msg_send_fail, user_recall_msg)

## Configuration Notes

For WeChat Customer Service, use the WeChat Customer Service enterprise ID for WEWORK_CORP_ID and WeChat Customer Service Secret for WEWORK_SECRET. WEWORK_AGENT_ID can be left empty for WeChat Customer Service.

## Important Implementation Notes

### Message Processing Architecture
The system uses a pipeline approach: **Message → Decrypt → Classify → Extract Text → AI Analysis → Store/Reply**

Key design decisions:
- WeChat Customer Service uses event notifications that require sync_msg API calls to get actual message content
- All message types are converted to plain text before AI analysis for consistency
- Chat record analysis focuses on the "other party" (not the message forwarder)
- Database automatically stores every successful AI analysis with full metadata

### Error Handling Patterns
- Decryption: Multiple fallback methods with detailed logging
- ETL Processing: Timeout handling with user-friendly error messages
- AI Analysis: JSON parsing with automatic bracket repair
- Voice Recognition: Graceful degradation when ASR/ffmpeg unavailable

### Platform-Specific Behavior
- **Enterprise WeChat**: Direct message delivery in callbacks
- **WeChat Customer Service**: Event-driven with separate message sync calls
- Both platforms share the same processing pipeline after initial message retrieval

### Configuration Dependencies
- **Required**: WEWORK_CORP_ID, WEWORK_SECRET, WEWORK_TOKEN, WEWORK_AES_KEY, QWEN_API_KEY
- **Optional**: ASR_TOKEN (for voice), FFMPEG_PATH (for voice conversion)
- **Auto-configured**: ETL4LM endpoint (no API key required)