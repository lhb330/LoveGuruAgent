# LoveGuruAgent

基于 FastAPI + LangGraph + pgvector 的恋爱咨询 AI 后端项目。

项目提供：
- 聊天接口（支持流式 SSE 输出）
- 聊天历史持久化
- 基于 Markdown 知识库的 RAG 检索
- OpenAI / 通义千问双模型适配
- 启动时自动导入知识库向量
- 智能工具调用（地图搜索等）
- **长期记忆管理**（自动提取用户关键信息并跨会话使用）

## 技术栈

- Web 框架：FastAPI
- ORM：SQLAlchemy
- 数据库：PostgreSQL + pgvector
- 大模型接入：OpenAI、DashScope(Qwen)
- 编排层：LangGraph
- 配置管理：pydantic-settings

## 快速启动

```bash
pip install -r requirements.txt
copy .env.example .env
python main.py
```

启动后访问：
- Swagger 文档：[http://127.0.0.1:9000/docs](http://127.0.0.1:9000/docs)
- 健康检查：[http://127.0.0.1:9000/api/v1/health/](http://127.0.0.1:9000/api/v1/health/)

## 配置说明

主要配置位于 [`.env`](D:/lhb_work/py_charm_work/LoveGuruAgent/.env:1)。

重点字段：
- `DATABASE_URL`：PostgreSQL 连接串
- `LLM_PROVIDER`：`openai` 或 `qwen`
- `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL`
- `DASHSCOPE_API_KEY` / `QWEN_MODEL` / `QWEN_EMBEDDING_MODEL`
- `VECTOR_DIMENSION`：向量维度，需要与 embedding 模型输出维度一致
- `KNOWLEDGE_DOCS_DIR`：知识库 Markdown 目录，默认是 `docs`
- `BAIDU_MAP_AK`：百度地图 API 密钥（用于地点搜索功能）
- `ENABLE_LONG_MEMORY`：是否启用长期记忆功能，默认 `true`
- `LONG_MEMORY_MAX_ENTRIES`：单个用户最大记忆数量，默认 `100`

如果使用千问，必须把 `DASHSCOPE_API_KEY` 改成真实值，否则启动时知识库向量导入会失败。

## 项目架构

项目采用典型分层结构：

```text
controller -> services -> dao -> entity
                |
             harness
                |
           llm / rag / vector
```

职责划分：
- `controller`：对外暴露 HTTP 接口，只做参数接收和响应返回
- `services`：业务逻辑层，负责聊天、RAG、向量导入、模型调用
- `dao`：数据库访问层，负责 ORM 查询与持久化
- `entity`：数据库表映射
- `harness`：LangGraph、Prompt 拼装、调用链编排、工具集成
- `tools`：外部工具模块（百度地图搜索等）
- `common`：通用返回体、异常、常量、工具函数
- `config`：配置、数据库连接、日志初始化

## 目录说明

### 根目录

- [`main.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/main.py:1)
  应用入口，创建 FastAPI 实例，注册路由、异常处理，并在生命周期中执行向量库初始化。

- [`.env.example`](D:/lhb_work/py_charm_work/LoveGuruAgent/.env.example:1)
  环境变量模板。

- [`requirements.txt`](D:/lhb_work/py_charm_work/LoveGuruAgent/requirements.txt:1)
  Python 依赖列表。

### `common/`

- [`common/ApiResult.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/common/ApiResult.py:1)
  统一接口返回包装，格式为 `code / msg / data`。

- [`common/exceptions.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/common/exceptions.py:1)
  统一异常定义和全局异常处理。

- [`common/ErrorCode.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/common/ErrorCode.py:1)
  错误码定义。

- [`common/constants.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/common/constants.py:1)
  通用常量，如消息类型、系统提示词。

- [`common/utils.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/common/utils.py:1)
  通用工具函数，例如读取文本文件。

### `config/`

- [`config/settings.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/config/settings.py:1)
  读取 `.env` 配置。

- [`config/database.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/config/database.py:1)
  SQLAlchemy `engine`、`SessionLocal`、`Base`、pgvector 列定义。

- [`config/logger.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/config/logger.py:1)
  日志初始化。

### `controller/`

- [`controller/health_controller.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/controller/health_controller.py:1)
  健康检查接口。

- [`controller/chat_controller.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/controller/chat_controller.py:1)
  聊天、历史记录、清空会话接口。

- [`controller/vector_controller.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/controller/vector_controller.py:1)
  手动重建知识库向量接口。

### `entity/`

- [`entity/chat_message.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/entity/chat_message.py:1)
  聊天消息表映射，对应 `t_ai_chat_message`。

- [`entity/knowledge_embedding.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/entity/knowledge_embedding.py:1)
  知识库向量表映射，对应 `t_knowledge_embedding`。

- [`entity/user_memory.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/entity/user_memory.py:1)
  用户长期记忆表映射，对应 `t_user_memory`。

### `dao/`

- [`dao/chat_message_dao.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/dao/chat_message_dao.py:1)
  聊天消息的增删查。

- [`dao/knowledge_embedding_dao.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/dao/knowledge_embedding_dao.py:1)
  向量数据的保存、清空、相似度检索。

- [`dao/user_memory_dao.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/dao/user_memory_dao.py:1)
  用户长期记忆的增删改查、按重要度检索、记忆淘汰。

### `services/`

#### `services/chat/`

- [`services/chat/chat_service.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/chat/chat_service.py:1)
  聊天主流程：保存用户消息、调用图编排、保存 AI 回复、返回引用文档。**对话结束后异步提取长期记忆**。
  
  **核心功能**：
  - 同步/流式聊天接口（支持 SSE 打字机效果）
  - LangGraph 图调用（带重试机制，最多3次）
  - 异步记忆提取（后台线程，不影响响应速度）
  - 人工审批恢复（敏感词拦截场景）
  - 断点续传（checkpointer 状态恢复）

- [`services/chat/rag_service.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/chat/rag_service.py:1)
  RAG 检索服务：把问题转 embedding，再到 pgvector 中做相似度查询。

#### `services/llm/`

- [`services/llm/factory.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/llm/factory.py:1)
  根据 `LLM_PROVIDER` 选择使用 OpenAI 或 Qwen。

- [`services/llm/openai_service.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/llm/openai_service.py:1)
  OpenAI 聊天与 embedding 调用封装。

- [`services/llm/qwen_service.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/llm/qwen_service.py:1)
  DashScope/Qwen 聊天与 embedding 调用封装，并补充了错误响应校验。

#### `services/vector/`

- [`services/vector/pgvector_service.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/vector/pgvector_service.py:1)
  知识库向量导入、数据库扩展初始化、启动时向量构建。

#### `services/memory/`

- [`services/memory/memory_service.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/memory/memory_service.py:1)
  长期记忆管理：记忆提取、检索、存储、淘汰。
  
  **核心功能**：
  - **记忆提取**：使用 LLM 从对话中提取用户关键信息（偏好、关系状态、重要事件等）
  - **隐含信息推断**：从用户问题中推断隐含状态（如"第一次约会"→推测用户单身）
  - **记忆检索**：对话开始时加载用户长期记忆，注入 Prompt 提供个性化回复
  - **记忆淘汰**：按重要度评分自动清理低价值记忆，保持记忆库精简

### `harness/`

- [`harness/graph_builder.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/graph_builder.py:1)
  LangGraph 图定义。包含 Agent 节点、Tool Node、工具结果处理节点，支持 LLM 自主决策是否调用工具。

- [`harness/chain_builder.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/chain_builder.py:1)
  把"检索 -> Prompt 拼装 -> 模型生成"串成一条链。包含智能地址提取和地点类型识别逻辑。

- [`harness/prompt_manager.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/prompt_manager.py:1)
  把知识库引用内容、工具搜索结果和用户问题拼成最终 Prompt。

### `docs/`

知识库目录。这里放 Markdown 文档，启动时或调用重建接口时会被导入向量库。

### `logs/`

运行日志目录。

### `tools/`

外部工具模块目录：
- `baidu_map_tool.py`：百度地图搜索工具，支持地点搜索（餐厅、酒店、银行等20+种POI类型）

## 当前接口

### 健康检查

- `GET /api/v1/health/`

### 聊天接口（同步）

- `POST /api/v1/chat/send`
- `GET /api/v1/chat/history/{conversation_id}`
- `GET /api/v1/chat/history/all`（获取所有消息）
- `GET /api/v1/chat/history/grouped`（按会话分组）
- `DELETE /api/v1/chat/{conversation_id}`

### 聊天接口（流式 SSE）

- `POST /api/v1/chat/send-stream`

**请求示例**：
```json
{
  "conversation_id": "conv-20260427-42",
  "message": "第一次约会需要注意什么？",
  "user_id": "test_user_001"
}
```

**SSE 响应格式**：
```
data: {"content": "第一次", "done": false}

data: {"content": "约会时", "done": false}

data: {"content": "", "done": true, "references": []}
```

### 人工审批与断点续传

- `POST /api/v1/chat/approve`（人工审批敏感词拦截）
- `POST /api/v1/chat/resume/{conversation_id}`（断点续传恢复）

### 向量接口

- `POST /api/v1/vector/rebuild`

## 接口请求流程

### 1. 聊天请求流程

接口：`POST /api/v1/chat/send`

请求示例：

```json
{
  "conversation_id": "test-001",
  "message": "终于谈恋爱了，超开心，想知道怎么更好地相处。"
}
```

执行流程：

1. 请求进入 [`controller/chat_controller.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/controller/chat_controller.py:12)
2. Controller 调用 [`ChatService.chat`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/chat/chat_service.py:16)
3. `ChatService` 先把用户消息写入 `t_ai_chat_message`
4. `ChatService` 调用 LangGraph：[`build_chat_graph()`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/graph_builder.py:16)
5. 图中的 `agent` 节点判断是否需要调用工具
   - **需要工具**：执行 `tools` 节点 → `tools_result` 节点处理结果 → 生成回复
   - **不需要工具**：执行 `generate_reply` 节点（RAG流程）→ 生成回复
6. `ChatChainBuilder` 调用 [`RAGService.retrieve`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/chat/rag_service.py:10) 检索知识库
7. 检索结果和工具结果交给 [`PromptManager`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/prompt_manager.py:1) 组装 Prompt
8. 通过 [`services/llm/factory.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/llm/factory.py:6) 选择具体模型服务
9. 调用模型生成回复
10. AI 回复写入 `t_ai_chat_message`
11. 返回 `conversation_id`、`reply`、`references`

返回示例：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "conversation_id": "test-001",
    "reply": "这里是模型回复",
    "references": [
      {
        "doc_name": "恋爱常见问题和回答 - 单身篇.md",
        "content": "文档内容",
        "metadata": {
          "source": "docs/xxx.md"
        }
      }
    ]
  }
}
```

### 2. 查询聊天历史流程

接口：`GET /api/v1/chat/history/{conversation_id}`

执行流程：

1. 请求进入 [`controller/chat_controller.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/controller/chat_controller.py:18)
2. 调用 [`ChatService.history`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/chat/chat_service.py:43)
3. 通过 [`ChatMessageDAO.list_messages`](D:/lhb_work/py_charm_work/LoveGuruAgent/dao/chat_message_dao.py:28) 查询消息表
4. 返回当前会话的完整历史

### 3. 重建知识库向量流程

接口：`POST /api/v1/vector/rebuild`

执行流程：

1. 请求进入 [`controller/vector_controller.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/controller/vector_controller.py:9)
2. 调用 [`PGVectorService.rebuild_from_docs`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/vector/pgvector_service.py:25)
3. 扫描 `docs/*.md`
4. 逐篇读取文档内容
5. 调用 embedding 模型生成向量
6. 清空旧向量数据并写入新数据

## 大模型调用链路

### 聊天生成链路

```text
POST /api/v1/chat/send
  -> ChatController.send_message
  -> ChatService.chat
  -> LangGraph(agent)
  -> [条件路由]
     ├─ 需要工具 -> ToolNode -> tools_result -> ChatChainBuilder.run
     └─ 不需要工具 -> ChatChainBuilder.run
  -> RAGService.retrieve
  -> PromptManager.build_chat_prompt / build_chat_prompt_with_tools
  -> LLM Factory(get_llm_service)
  -> OpenAIService.invoke / QwenService.invoke
  -> 返回模型回复
```

### RAG 检索链路

```text
用户问题
  -> RAGService.retrieve
  -> LLM Factory(get_llm_service)
  -> OpenAIService.embed_text / QwenService.embed_text
  -> KnowledgeEmbeddingDAO.similarity_search
  -> pgvector cosine_distance 检索
  -> 返回 top_k 文档
```

### 知识库导入链路

```text
应用启动 / POST /api/v1/vector/rebuild
  -> VectorBootstrapService.initialize / PGVectorService.rebuild_from_docs
  -> 扫描 docs/*.md
  -> 读取 Markdown 内容
  -> 调用 embedding 模型
  -> 写入 t_knowledge_embedding
```

## 启动时发生了什么

应用启动时会执行 [`main.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/main.py:11) 中的 `lifespan`：

1. 加载配置
2. 初始化日志
3. 执行 [`VectorBootstrapService.initialize`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/vector/pgvector_service.py:50)
4. 创建 `vector` 扩展并建表
5. 如果 `docs/` 下有 Markdown，则自动尝试导入向量

注意：
- 如果 embedding API Key 配置不正确，应用仍可启动
- 但启动日志会提示知识库向量导入失败
- 此时聊天接口仍能调用模型，但 `references` 可能为空，RAG 效果会缺失

## 数据流说明

### 聊天消息表 `t_ai_chat_message`

保存：
- 会话 ID
- 消息类型
- 角色
- 消息内容
- 创建时间

用途：
- 历史记录查询
- 会话追踪

### 知识库向量表 `t_knowledge_embedding`

保存：
- 文档名
- 文档原文
- metadata
- 向量 embedding

用途：
- RAG 相似度检索

## 工具调用机制

### 地图搜索工具

项目已集成百度地图搜索工具，支持智能地点搜索。

**支持的地点类型（20+种）：**
- 餐饮类：餐厅、咖啡厅、酒吧、快餐
- 生活服务：酒店、超市、银行、加油站、医院、学校
- 休闲娱乐：电影院、KTV、公园、健身房、图书馆
- 交通设施：地铁站、公交站、停车场
- 政务服务：政府、邮局

**智能地址提取：**
- 支持完整地址："XX市XX区XX路/街/道"
- 支持行政区划："XX市XX区"、"XX市XX县"
- 支持地标建筑："XX小区"、"XX大厦"、"XX商场"
- 支持交通枢纽："XX地铁站"、"XX公交站"

**使用示例：**
```json
{
  "conversation_id": "test-001",
  "message": "北京市朝阳区附近找餐厅"
}
```

系统会自动：
1. 识别用户意图（找餐厅）
2. 提取地址信息（北京市朝阳区）
3. 调用百度地图API搜索
4. 将搜索结果整合到回复中

### 工具调用流程

```text
用户消息
  -> Agent节点（LLM决策）
  -> 是否需要工具？
     ├─ 是 -> ToolNode执行 -> 工具结果处理 -> 生成回复
     └─ 否 -> RAG流程 -> 生成回复
```

## 长期记忆机制

### 记忆提取流程

系统会在每次对话结束后，**异步**提取用户的关键信息并存储到长期记忆库：

```
对话结束
   │
   ▼
┌──────────────────────────────────────────────┐
│ 异步记忆提取（后台线程）                       │
│                                              │
│ 1. 组装对话文本:                              │
│    "用户: {message}\nAI: {reply}"            │
│                                              │
│ 2. 调用 LLM 提取记忆:                         │
│    - 直接信息: "我今年25岁"                   │
│    - 隐含推断: "第一次约会"→单身（推测）       │
│    - 重要度评分: 0.0~1.0                      │
│                                              │
│ 3. 保存到 t_user_memory:                      │
│    - user_id, memory_key, memory_value        │
│    - importance, source_conversation_id       │
│                                              │
│ 4. 淘汰低重要度记忆:                          │
│    - 超过 max_entries 时清理                  │
│    - 优先保留高重要度记忆                      │
└──────────────────────────────────────────────┘
```

### 记忆使用流程

在下一次对话开始时，系统会自动加载用户的长期记忆并注入 Prompt：

```
用户发送消息
   │
   ▼
┌──────────────────────────────────────────────┐
│ MemoryService.get_user_memories()            │
│                                              │
│ 1. 查询 t_user_memory:                        │
│    - 按 user_id 过滤                          │
│    - importance >= 0.3                        │
│    - 最多返回 100 条                          │
│                                              │
│ 2. 格式化记忆文本:                            │
│    "## 用户长期记忆"                          │
│    "- [关系状态] 单身（推测）"                 │
│    "- [年龄] 25岁"                            │
│                                              │
│ 3. 注入系统 Prompt:                           │
│    系统提示词 + 长期记忆 + 知识库 + 用户问题   │
└──────────────────────────────────────────────┘
```

### 记忆提取规则

**重要度评分标准**：
- `1.0`: 核心身份信息（姓名、性别、年龄）
- `0.9`: 重要关系信息（伴侣、婚姻状态）
- `0.8`: 关键偏好和价值观
c- `0.7`: 重要经历和事件、当前状态（如"准备第一次约会"）
- `0.6`: 日常偏好和习惯、关注的话题领域
c- `0.5`: 一般性信息、可能的兴趣点（标注为推测）

**隐含信息推断示例**：
- 用户问"第一次约会" → 推断"用户正在准备第一次约会"（重要度 0.7）
- 用户问"如何哄老婆开心" → 推断"用户已婚"（重要度 0.9）
- 用户问"如何挽回前女友" → 推断"用户刚分手"（重要度 0.8）

### 记忆数据表结构

**`t_user_memory` 表**：
- `id`: 主键
- `user_id`: 用户标识
c- `memory_key`: 记忆类别（如"年龄"、"关系状态"）
- `memory_value`: 记忆内容
c- `importance`: 重要度（0.0~1.0）
- `source_conversation_id`: 来源会话ID
c- `create_time`: 创建时间
c- `update_time`: 更新时间

## 当前实现特点

- LangGraph 采用多节点架构：Agent、ToolNode、工具结果处理、常规回复
- 支持 LLM 自主决策是否调用工具（LangGraph Tool机制）
- 智能地址提取：5层地址识别策略，覆盖各种表达习惯
- 丰富的POI类型：20+种地点类型，每种支持多个同义词
- 当前 RAG 是"整篇文档召回后直接拼 Prompt"，还没有做 chunk 切分
- 聊天接口已经走后端 RAG，不是纯模型直连
- 百度地图工具已完全接入主链路
- **长期记忆已实现完整生命周期**：提取→存储→检索→淘汰
- 记忆提取支持隐含信息推断，从用户问题中推测状态

## 后续可扩展方向

- [x] ~~增加多轮记忆摘要~~（已完成：长期记忆功能）
- 增加文档切片与分段向量化
- 增加更多工具（天气查询、日程管理等）
- 增加模型路由和降级策略
- 增加单元测试和接口测试
- 支持坐标定位（经纬度）搜索
- 增加工具调用的日志和监控
- 记忆提取优化：积累多轮对话后再提取（而非单次对话）
- 增加记忆可视化查看/编辑接口

## 完整项目架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI 应用层                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    main.py (入口)                              │   │
│  │  • 创建 FastAPI 实例                                          │   │
│  │  • 注册路由                                                  │   │
│  │  • 生命周期管理 (lifespan)                                    │   │
│  │  • 启动时初始化知识库向量                                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  Controller  │        │  Controller  │        │  Controller  │
│  (健康检查)   │        │  (聊天接口)   │        │  (向量接口)   │
│              │        │              │        │              │
│ GET /health  │        │ POST /send   │        │ POST /rebuild│
│              │        │ GET /history │        │              │
│              │        │ DELETE /{id} │        │              │
└──────────────┘        └──────────────┘        └──────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         业务服务层 (Services)                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  ChatService                                  │   │
│  │  • 保存用户消息到数据库                                        │   │
│  │  • 调用 LangGraph 生成回复                                    │   │
│  │  • 保存 AI 回复到数据库                                       │   │
│  │  • 支持流式输出 (SSE)                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  RAGService                                   │   │
│  │  • 将用户问题转换为 embedding                                 │   │
│  │  • 在 pgvector 中进行相似度检索                               │   │
│  │  • 返回 Top-K 相关文档                                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              LLM Factory + Services                           │   │
│  │  • 根据配置选择 OpenAI 或 Qwen                                │   │
│  │  • 统一聊天接口                                               │   │
│  │  • 统一 Embedding 接口                                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────────┐    ┌──────────────┐
│  Harness     │      │    DAO 层        │    │  Tools 层    │
│  (编排层)     │      │                  │    │              │
│              │      │ ChatMessageDAO   │    │ 百度地图搜索  │
│ • LangGraph  │      │ • 保存消息       │    │ • POI搜索    │
│ • Chain      │      │ • 查询历史       │    │ • 附近搜索    │
│ • Prompt     │      │ • 清空会话       │    │ • 20+类型    │
└──────────────┘      └──────────────────┘    └──────────────┘
        │                       │
        ▼                       ▼
┌──────────────┐      ┌──────────────────┐
│  Entity 层   │      │   数据库          │
│              │      │                  │
│ ChatMessage  │      │ PostgreSQL       │
│ Knowledge    │      │ + pgvector       │
│ Embedding    │      │                  │
└──────────────┘      └──────────────────┘
```

## 核心工作流：聊天请求完整链路

```
用户请求
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│ 1. HTTP 请求: POST /api/v1/chat/send                    │
│    {                                                     │
│      "conversation_id": "xxx",                          │
│      "message": "北京市朝阳区附近找餐厅"                 │
│    }                                                     │
└─────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│ 2. ChatController.send_message()                        │
│    • 接收请求参数                                        │
│    • 调用 ChatService.chat()                            │
└─────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│ 3. ChatService.chat()                                   │
│    • 开启数据库事务                                      │
│    • 保存用户消息到 t_ai_chat_message                    │
│    • 调用 LangGraph                                     │
└─────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│ 4. LangGraph 工作流执行                                  │
│                                                         │
│    ┌─────────┐                                         │
│    │  Entry  │  初始化 ChatState                        │
│    └────┬────┘                                         │
│         │                                               │
│         ▼                                               │
│    ┌──────────────────┐                                │
│    │ Agent Node       │  LLM 判断是否需要调用工具       │
│    │ (决策节点)        │  绑定工具: search_nearby_places │
│    └────┬─────────────┘                                │
│         │                                               │
│    ┌────▼─────┐                                        │
│    │ should_  │  检查 LLM 响应中的 tool_calls          │
│    │ use_tools│                                        │
│    └────┬─────┘                                        │
│         │                                               │
│    ┌────▼────────────────────┐                         │
│    │   条件路由               │                         │
│    └────┬───────────────┬────┘                         │
│         │               │                               │
│    ┌────▼────┐    ┌─────▼──────────┐                   │
│    │ tools   │    │ generate_reply │                   │
│    │ (工具)  │    │ _stream (RAG)  │                   │
│    └────┬────┘    └─────┬──────────┘                   │
│         │               │                               │
│    ┌────▼──────────┐   │                               │
│    │tools_result   │   │                               │
│    │(整合工具结果)  │   │                               │
│    └────┬──────────┘   │                               │
│         │               │                               │
│    ┌────▼───────┐ ┌────▼──────┐                        │
│    │    END     │ │    END    │                        │
│    └────────────┘ └───────────┘                        │
└─────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Agent Node 内部流程                                   │
│                                                         │
│    • 获取 LLM 服务并绑定工具                              │
│    • 构建消息历史: [HumanMessage]                        │
│    • 调用 llm_with_tools.invoke()                       │
│    • LLM 返回:                                           │
│      - 如果需要工具: AIMessage with tool_calls          │
│      - 如果不需要: AIMessage with content               │
└─────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│ 6a. 工具路径: ToolNode → tools_result_node               │
│                                                         │
│    • ToolNode 执行 search_nearby_places                 │
│      - 识别地点类型: "餐厅"                              │
│      - 提取地址: "北京市朝阳区"                          │
│      - 调用百度地图 API                                  │
│      - 返回 POI 列表                                    │
│                                                         │
│    • tools_result_node:                                 │
│      - 获取 RAG 检索结果                                 │
│      - 提取 ToolMessage 内容                            │
│      - 调用 PromptManager.build_chat_prompt_with_tools()│
│      - 生成最终 Prompt:                                 │
│        * 系统提示词                                      │
│        * 知识库参考                                      │
│        * 工具搜索结果                                    │
│        * 用户问题                                        │
│      - 调用 LLM 生成回复                                │
└─────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│ 6b. RAG 路径: generate_reply_stream                      │
│                                                         │
│    • 调用 RAGService.retrieve()                         │
│      - 将用户问题转换为 embedding                        │
│      - 在 pgvector 中相似度检索                          │
│      - 返回 Top-K 文档                                  │
│                                                         │
│    • 调用 PromptManager.build_chat_prompt()             │
│      - 系统提示词                                        │
│      - 知识库参考                                        │
│      - 用户问题                                          │
│                                                         │
│    • 流式调用 LLM:                                      │
│      for chunk in llm.stream(prompt):                   │
│          full_response += chunk.content                 │
└─────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│ 7. 返回 ChatService                                     │
│    • 获取 state["assistant_reply"]                      │
│    • 获取 state["references"]                           │
│    • 保存 AI 回复到 t_ai_chat_message                    │
│    • 提交数据库事务                                      │
└─────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│ 8. 返回 HTTP 响应                                        │
│    {                                                     │
│      "code": 0,                                         │
│      "msg": "success",                                  │
│      "data": {                                           │
│        "conversation_id": "xxx",                        │
│        "reply": "为您推荐以下餐厅...",                   │
│        "references": [                                   │
│          {                                               │
│            "doc_name": "恋爱篇.md",                     │
│            "content": "...",                            │
│            "metadata": {...}                            │
│          }                                               │
│        ]                                                 │
│      }                                                   │
│    }                                                     │
└─────────────────────────────────────────────────────────┘
```

## LangGraph 状态管理

```python
class ChatState(TypedDict, total=False):
    conversation_id: str                    # 会话 ID
    user_message: str                       # 用户当前消息
    messages: Annotated[list, lambda x, y: x + y]  # 消息历史(自动累加)
    assistant_reply: str                    # AI 回复文本
    references: list[dict]                  # 参考文档列表
```

**状态流转**:
```
Entry → Agent Node (更新 messages, assistant_reply)
      → ToolNode (更新 messages with ToolMessage)
      → tools_result (更新 assistant_reply, references)
      → END
```

## 完整数据流向

### RAG 检索链路
```
用户问题 → RAGService.retrieve()
         → LLM Factory → embed_text()
         → KnowledgeEmbeddingDAO.similarity_search()
         → pgvector cosine_distance 检索
         → 返回 Top-K 文档
```

### 知识库导入链路
```
应用启动 / POST /rebuild
         → VectorBootstrapService.initialize()
         → 扫描 docs/*.md
         → 读取 Markdown 内容
         → 调用 embedding 模型
         → 写入 t_knowledge_embedding
```

## 技术栈总结

| 层级 | 技术 | 用途 |
|------|------|------|
| **Web 框架** | FastAPI | HTTP 接口、路由、依赖注入 |
| **编排层** | LangGraph | Agent 工作流、状态管理、工具调用 |
| **ORM** | SQLAlchemy | 数据库访问、对象关系映射 |
| **数据库** | PostgreSQL + pgvector | 关系数据 + 向量存储 |
| **LLM** | OpenAI / DashScope(Qwen) | 聊天生成、Embedding、记忆提取 |
| **配置** | pydantic-settings | 环境变量管理 |
| **工具** | 百度地图 API | POI 搜索、附近推荐 |
| **记忆服务** | MemoryService | 长期记忆提取、检索、淘汰 |
