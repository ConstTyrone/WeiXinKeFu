# 企业微信(WeWork)和微信客服回调服务

这是一个基于FastAPI的Webhook服务，用于接收和处理来自企业微信(WeWork)和微信客服平台的消息回调。

## 项目概述

该服务主要功能包括：
- 接收企业微信和微信客服的消息回调
- 验证消息签名确保安全性
- 解密加密消息内容
- 对消息进行分类处理
- 根据消息类型执行相应的业务逻辑
- 支持微信客服特有的事件回调和消息同步机制

## 项目架构

```
├── main.py                 # FastAPI应用主文件，包含回调接口
├── wework_client.py        # 企业微信客户端，处理签名验证、消息解密和API调用
├── config/
│   └── config.py           # 配置管理
├── message_classifier.py   # 消息分类器
├── message_handler.py      # 消息处理器
├── run.py                  # 应用启动脚本
├── requirements.txt        # 项目依赖
├── weixin_doc/             # 微信客服官方文档
└── tests/                  # 测试文件
```

## 核心组件

### 1. FastAPI应用 (main.py)
- 提供两个主要接口：
  - `GET /wework/callback` - 用于企业微信/微信客服回调URL验证
  - `POST /wework/callback` - 用于接收企业微信/微信客服消息回调
- 兼容微信客服平台的路由：
  - `GET /wechat/callback`
  - `POST /wechat/callback`
- 支持微信客服特有的事件回调处理机制

### 2. 企业微信客户端 (wework_client.py)
- `verify_signature()` - 验证消息签名，确保消息来源的合法性
- `decrypt_message()` - 解密企业微信/微信客服发送的加密消息
- `get_access_token()` - 获取企业微信/微信客服API访问令牌
- `sync_kf_messages()` - 同步微信客服消息内容（微信客服特有）

### 3. 消息分类器 (message_classifier.py)
将接收到的消息按类型分类：
- `chat_record` - 聊天记录
- `contact_info` - 联系人信息
- `command` - 命令消息
- `image` - 图片消息
- `file` - 文件消息
- `voice` - 语音消息
- `event` - 事件消息
- `general_text` - 普通文本消息

支持的微信客服消息类型：
- 文本消息 (text)
- 图片消息 (image)
- 语音消息 (voice)
- 视频消息 (video)
- 文件消息 (file)
- 位置消息 (location)
- 链接消息 (link)
- 小程序消息 (miniprogram)
- 菜单消息 (msgmenu)
- 事件消息 (event)
  - 用户进入会话事件 (enter_session)
  - 消息发送失败事件 (msg_send_fail)
  - 用户撤回消息事件 (user_recall_msg)

### 4. 消息处理器 (message_handler.py)
根据消息分类执行相应的处理逻辑：
- 处理聊天记录
- 处理联系人信息
- 处理命令消息
- 处理图片/文件/语音消息
- 处理事件消息
- 处理微信客服特有消息类型（视频、位置、链接、小程序等）
- 处理微信客服事件（用户进入会话、消息发送失败、用户撤回消息等）

## 环境变量配置

在运行服务之前，需要配置以下环境变量：

```bash
WEWORK_CORP_ID=your_corp_id          # 企业ID/微信客服企业ID
WEWORK_AGENT_ID=your_agent_id        # 企业微信应用ID（微信客服可不填）
WEWORK_SECRET=your_secret            # 企业微信应用密钥/微信客服Secret
WEWORK_TOKEN=your_token              # 令牌
WEWORK_AES_KEY=your_aes_key          # AES密钥
LOCAL_SERVER_PORT=3001               # 服务端口（可选，默认3001）
```

注意：对于微信客服，WEWORK_CORP_ID应填写微信客服的企业ID，WEWORK_SECRET应填写微信客服的Secret。

## 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
创建 `.env` 文件并填入上述环境变量。

### 3. 运行服务
```bash
# 方法1：使用uvicorn直接运行
uvicorn main:app --host 0.0.0.0 --port 3001 --reload

# 方法2：使用run.py脚本
python run.py
```

## 测试

项目包含多个测试脚本用于验证功能：

```bash
# 测试回调验证
python tests/test_callback_verification.py

# 测试签名验证
python tests/test_wework_signature.py

# 测试消息回调
python tests/test_message_callback.py
```

### 微信客服测试说明

要测试微信客服功能，需要：

1. 确保已正确配置微信客服的环境变量
2. 启动服务后，在微信客服管理后台配置回调URL
3. 通过微信客服客户端发送测试消息
4. 查看控制台输出确认消息处理是否正常

测试时可以在控制台看到类似以下的输出：
```
[微信客服事件] 企业ID: ww12345678910, 事件: kf_msg_or_event, 客服账号: wkxxxxxxx
Token: ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR, 时间: 1348831860
通过sync_msg接口获取消息成功，共收到1条消息
[文本消息] 用户: wmAJ2GCAAAme1XQRC-NI-q0_ZM9ukoAw
内容: 你好，我想咨询一下产品信息
```

## 调试工具

项目提供了一些实用的调试工具：

```bash
# 调试企业微信回调验证
python utils/debug_wework_callback.py

# 检查端口占用
python utils/check_port.py
```

## 微信客服与企业微信的区别

微信客服和企业微信在消息处理机制上有显著差异：

1. **企业微信**：直接在回调中发送完整的消息内容
2. **微信客服**：采用事件通知机制，回调只通知有新消息，需要主动调用接口获取具体消息内容

## 消息处理流程

### 企业微信消息处理流程
1. 企业微信向配置的回调URL发送GET请求进行URL验证
2. 服务验证签名并解密echostr参数，返回解密结果完成验证
3. 企业微信向回调URL发送POST请求传递消息
4. 服务验证消息签名并解密消息内容
5. 解析XML格式的消息内容
6. 根据消息类型进行分类
7. 执行相应的消息处理逻辑

### 微信客服消息处理流程
1. 微信客服向配置的回调URL发送GET请求进行URL验证
2. 服务验证签名并解密echostr参数，返回解密结果完成验证
3. 当有客户消息时，微信客服向回调URL发送POST请求传递事件通知
4. 服务验证消息签名并解密事件内容
5. 解析XML格式的事件通知
6. 识别为微信客服事件（MsgType=event, Event=kf_msg_or_event）
7. 调用sync_msg接口获取具体消息内容
8. 根据消息类型进行分类和处理

## 具体示例

### 示例1：用户发送文本消息
```
用户发送："你好，我想咨询一下产品信息"

微信客服回调事件：
<xml>
   <ToUserName><![CDATA[ww12345678910]]></ToUserName>
   <CreateTime>1348831860</CreateTime>
   <MsgType><![CDATA[event]]></MsgType>
   <Event><![CDATA[kf_msg_or_event]]></Event>
   <Token><![CDATA[ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR]]></Token>
   <OpenKfId><![CDATA[wkxxxxxxx]]></OpenKfId>
</xml>

通过sync_msg接口获取的具体消息：
{
   "msgtype" : "text",
   "text" : {
        "content" : "你好，我想咨询一下产品信息"
   }
}

处理结果：
[文本消息] 用户: wmAJ2GCAAAme1XQRC-NI-q0_ZM9ukoAw
内容: 你好，我想咨询一下产品信息
```

### 示例2：用户发送图片消息
```
用户发送一张产品图片

微信客服回调事件：
<xml>
   <ToUserName><![CDATA[ww12345678910]]></ToUserName>
   <CreateTime>1348831860</CreateTime>
   <MsgType><![CDATA[event]]></MsgType>
   <Event><![CDATA[kf_msg_or_event]]></Event>
   <Token><![CDATA[ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR]]></Token>
   <OpenKfId><![CDATA[wkxxxxxxx]]></OpenKfId>
</xml>

通过sync_msg接口获取的具体消息：
{
   "msgtype" : "image",
   "image" : {
        "media_id" : "2iSLeVyqzk4eX0IB5kTi9Ljfa2rt9dwfq5WKRQ4Nvvgw"
   }
}

处理结果：
[图片] 用户: wmAJ2GCAAAme1XQRC-NI-q0_ZM9ukoAw, MediaId: 2iSLeVyqzk4eX0IB5kTi9Ljfa2rt9dwfq5WKRQ4Nvvgw
✅ 图片消息已接收，可以下载并OCR识别
```

### 示例3：用户进入会话事件
```
用户点击链接进入客服会话

微信客服回调事件：
<xml>
   <ToUserName><![CDATA[ww12345678910]]></ToUserName>
   <CreateTime>1348831860</CreateTime>
   <MsgType><![CDATA[event]]></MsgType>
   <Event><![CDATA[kf_msg_or_event]]></Event>
   <Token><![CDATA[ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR]]></Token>
   <OpenKfId><![CDATA[wkxxxxxxx]]></OpenKfId>
</xml>

通过sync_msg接口获取的具体消息：
{
   "msgtype" : "event",
   "event" : {
        "event_type": "enter_session",
        "open_kfid": "wkAJ2GCAAASSm4_FhToWMFea0xAFfd3Q",
        "external_userid": "wmAJ2GCAAAme1XQRC-NI-q0_ZM9ukoAw",
        "scene": "123",
        "scene_param": "abc",
        "welcome_code": "aaaaaa"
   }
}

处理结果：
[微信客服事件] 企业ID: ww12345678910, 事件: kf_msg_or_event, 客服账号: wkxxxxxxx
Token: ENCApHxnGDNAVNY4AaSJKj4Tb5mwsEMzxhFmHVGcra996NR, 时间: 1348831860
[事件消息] 用户: wmAJ2GCAAAme1XQRC-NI-q0_ZM9ukoAw, 事件: enter_session, 事件Key: None
完整事件消息内容:
  msgtype: event
  event: {'event_type': 'enter_session', 'open_kfid': 'wkAJ2GCAAASSm4_FhToWMFea0xAFfd3Q', 'external_userid': 'wmAJ2GCAAAme1XQRC-NI-q0_ZM9ukoAw', 'scene': '123', 'scene_param': 'abc', 'welcome_code': 'aaaaaa'}
```

## 扩展开发

要添加新的消息处理逻辑：
1. 在 `message_classifier.py` 中添加新的分类规则
2. 在 `message_handler.py` 中实现新的处理函数
3. 在 `classify_and_handle_message()` 函数中添加新的处理分支