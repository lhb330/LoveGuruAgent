# LoveGuruAgent

基于 FastAPI + LangGraph + pgvector 的恋爱咨询 AI 后端项目。

项目提供：
- 聊天接口
- 聊天历史持久化
- 基于 Markdown 知识库的 RAG 检索
- OpenAI / 通义千问双模型适配
- 启动时自动导入知识库向量

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
- `harness`：LangGraph、Prompt 拼装、调用链编排
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

### `dao/`

- [`dao/chat_message_dao.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/dao/chat_message_dao.py:1)
  聊天消息的增删查。

- [`dao/knowledge_embedding_dao.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/dao/knowledge_embedding_dao.py:1)
  向量数据的保存、清空、相似度检索。

### `services/`

#### `services/chat/`

- [`services/chat/chat_service.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/chat/chat_service.py:1)
  聊天主流程：保存用户消息、调用图编排、保存 AI 回复、返回引用文档。

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

### `harness/`

- [`harness/graph_builder.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/graph_builder.py:1)
  LangGraph 图定义。当前只有一个 `generate_reply` 节点。

- [`harness/chain_builder.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/chain_builder.py:1)
  把“检索 -> Prompt 拼装 -> 模型生成”串成一条链。

- [`harness/prompt_manager.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/prompt_manager.py:1)
  把知识库引用内容和用户问题拼成最终 Prompt。

### `docs/`

知识库目录。这里放 Markdown 文档，启动时或调用重建接口时会被导入向量库。

### `logs/`

运行日志目录。

### `tools/`

预留工具模块目录，当前包含日期、情绪、聊天相关工具代码，但未接入主聊天链路。

## 当前接口

### 健康检查

- `GET /api/v1/health/`

### 聊天接口

- `POST /api/v1/chat/send`
- `GET /api/v1/chat/history/{conversation_id}`
- `DELETE /api/v1/chat/{conversation_id}`

### 向量接口

- `POST /api/v1/vector/rebuild`

## 接口请求流程

### 1. 聊天请求流程

接口：`POST /api/v1/chat/send`

请求示例：

```json
{
  "conversation_id": "test-001",
  "message": "我刚分手，很难受，怎么调整？"
}
```

执行流程：

1. 请求进入 [`controller/chat_controller.py`](D:/lhb_work/py_charm_work/LoveGuruAgent/controller/chat_controller.py:12)
2. Controller 调用 [`ChatService.chat`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/chat/chat_service.py:16)
3. `ChatService` 先把用户消息写入 `t_ai_chat_message`
4. `ChatService` 调用 LangGraph：[`build_chat_graph()`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/graph_builder.py:16)
5. 图中的 `generate_reply` 节点执行 [`ChatChainBuilder.run`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/chain_builder.py:11)
6. `ChatChainBuilder` 先调用 [`RAGService.retrieve`](D:/lhb_work/py_charm_work/LoveGuruAgent/services/chat/rag_service.py:10) 检索知识库
7. 检索结果交给 [`PromptManager.build_chat_prompt`](D:/lhb_work/py_charm_work/LoveGuruAgent/harness/prompt_manager.py:5) 组装 Prompt
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
  -> LangGraph(generate_reply)
  -> ChatChainBuilder.run
  -> RAGService.retrieve
  -> PromptManager.build_chat_prompt
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

## 当前实现特点

- 当前 LangGraph 只有一个节点，结构简单，适合后续扩展多节点流程
- 当前 RAG 是“整篇文档召回后直接拼 Prompt”，还没有做 chunk 切分
- 当前 `tools/` 目录下的工具尚未接入主链路
- 聊天接口已经走后端 RAG，不是纯模型直连

## 后续可扩展方向

- 增加文档切片与分段向量化
- 增加多轮记忆摘要
- 增加工具调用节点
- 增加模型路由和降级策略
- 增加单元测试和接口测试
