---
name: loveguru-developer
description: LoveGuruAgent项目开发指南。基于FastAPI+LangGraph+pgvector的恋爱咨询AI后端项目。提供聊天接口、RAG检索、长期记忆管理和智能工具调用。用于开发新功能、调试问题、理解架构或添加Agent/工具时使用。
---

# LoveGuruAgent 项目开发技能

## 📋 项目概述

LoveGuruAgent是一个基于 FastAPI + LangGraph + pgvector 的恋爱咨询 AI 后端项目。

**核心功能**：
- 聊天接口（支持流式 SSE 输出）
- 聊天历史持久化
- 基于 Markdown 知识库的 RAG 检索
- OpenAI / 通义千问双模型适配
- 启动时自动导入知识库向量
- 智能工具调用（百度地图搜索等）
- 长期记忆管理（自动提取用户关键信息并跨会话使用）

## 🛠️ 技术栈

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

## 🏗️ 项目架构

### 分层结构
```
controller -> services -> dao -> entity
                |
             harness
                |
           llm / rag / vector
```

### 目录职责
- `controller/`：对外暴露 HTTP 接口，只做参数接收和响应返回
- `services/`：业务逻辑层，负责聊天、RAG、向量导入、模型调用
- `dao/`：数据库访问层，负责 ORM 查询与持久化
- `entity/`：数据库表映射
- `harness/`：LangGraph、Prompt 拼装、调用链编排、工具集成
- `tools/`：外部工具模块（百度地图搜索等）
- `common/`：通用返回体、异常、常量、工具函数
- `config/`：配置、数据库连接、日志初始化

## 📡 API接口列表

### 健康检查
- `GET /api/v1/health/` - 服务健康状态检查

### 聊天接口（同步）
- `POST /api/v1/chat/send` - 发送聊天消息
- `GET /api/v1/chat/history/{conversation_id}` - 获取会话历史
- `GET /api/v1/chat/history/all` - 获取所有消息
- `GET /api/v1/chat/history/grouped` - 按会话分组获取
- `DELETE /api/v1/chat/{conversation_id}` - 删除会话

### 聊天接口（流式 SSE）
- `POST /api/v1/chat/send-stream` - 流式聊天（打字机效果）

### 人工审批与断点续传
- `POST /api/v1/chat/approve` - 人工审批敏感词拦截
- `POST /api/v1/chat/resume/{conversation_id}` - 断点续传恢复

### 向量接口
- `POST /api/v1/vector/rebuild` - 重建知识库向量

## 🔄 核心数据流

### 聊天请求完整链路
```
用户请求 → ChatController → ChatService → LangGraph工作流
   → Agent节点决策 → [需要工具] → ToolNode → 工具结果处理
                        → [不需要工具] → RAG检索 → Prompt组装
   → LLM生成回复 → 保存到数据库 → 异步提取记忆 → 返回响应
```

### RAG 检索链路
```
用户问题 → RAGService → embedding模型 → pgvector相似度检索 → Top-K文档
```

### 知识库导入链路
```
应用启动/rebuild → 扫描docs/*.md → embedding模型 → t_knowledge_embedding表
```

### 长期记忆链路
```
对话结束 → 异步提取 → LLM分析 → t_user_memory表 → 下次对话加载到Prompt
```

## 🔧 核心功能模块

### 1. 聊天服务 (services/chat/chat_service.py)
- 同步/流式聊天接口（支持 SSE 打字机效果）
- LangGraph 图调用（带重试机制，最多3次）
- 异步记忆提取（后台线程，不影响响应速度）
- 人工审批恢复（敏感词拦截场景）
- 断点续传（checkpointer 状态恢复）

### 2. RAG 检索服务 (services/chat/rag_service.py)
- 将用户问题转换为 embedding
- 在 pgvector 中进行相似度检索
- 返回 Top-K 相关文档

### 3. 长期记忆管理 (services/memory/memory_service.py)
- **记忆提取**：使用 LLM 从对话中提取用户关键信息
- **隐含信息推断**：从用户问题中推断隐含状态
- **记忆检索**：对话开始时加载用户长期记忆，注入 Prompt
- **记忆淘汰**：按重要度评分自动清理低价值记忆

### 4. 工具调用机制 (tools/baidu_map_tool.py)
- 百度地图搜索工具，支持20+种POI类型
- 智能地址提取：5层地址识别策略
- LLM 自主决策是否调用工具

## 🚀 开发工作流

### 1. 环境配置
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的API密钥
```

### 2. 关键配置项

**数据库配置**：
- `DATABASE_URL`：PostgreSQL 连接串
- `CHECKPOINTER_URI`：LangGraph检查点存储连接串

**LLM配置**：
- `LLM_PROVIDER`：选择 `openai` 或 `qwen`
- `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL`
- `DASHSCOPE_API_KEY` / `QWEN_MODEL` / `QWEN_EMBEDDING_MODEL`

**向量配置**：
- `VECTOR_DIMENSION`：向量维度（需与embedding模型输出维度一致）
- `KNOWLEDGE_DOCS_DIR`：知识库Markdown目录（默认 `docs`）

**功能开关**：
- `ENABLE_LONG_MEMORY`：是否启用长期记忆（默认 `true`）
- `LONG_MEMORY_MAX_ENTRIES`：单用户最大记忆数（默认 `100`）
- `BAIDU_MAP_AK`：百度地图API密钥

### 3. 启动服务
```bash
python main.py
```

启动后访问：
- Swagger文档：http://127.0.0.1:9000/docs
- 健康检查：http://127.0.0.1:9000/api/v1/health/

### 4. 启动时自动执行流程
1. 加载 `.env` 配置
2. 初始化日志系统
3. 创建数据库连接池
4. 初始化 pgvector 扩展和表结构
5. 自动导入 `docs/` 目录下的知识库向量
6. 初始化 LangGraph Checkpointer
7. 启动 FastAPI 服务

## 📝 开发规范

### 代码结构规范
1. **Controller层**：只负责参数接收和响应返回，不包含业务逻辑
2. **Service层**：处理核心业务逻辑，调用DAO和外部服务
3. **DAO层**：封装数据库操作，使用SQLAlchemy ORM
4. **Entity层**：定义数据模型和表映射

### 命名规范
- 模块名：小写字母+下划线（如 `chat_service.py`）
- 类名：大驼峰命名（如 `ChatService`）
- 函数/方法名：小写字母+下划线（如 `get_user_memories`）
- 常量：大写字母+下划线（如 `MAX_MEMORY_ENTRIES`）

### API设计规范
- 统一使用 `/api/v1/` 前缀
- RESTful 风格设计
- 统一返回格式：`{"code": 0, "msg": "success", "data": {...}}`
- 支持流式输出使用SSE格式

## 🔍 常见问题排查

### 1. 数据库连接问题
- 检查 `DATABASE_URL` 配置是否正确
- 确认PostgreSQL服务正在运行
- 验证pgvector扩展是否已安装

### 2. LLM API调用失败
- 检查API Key是否正确配置
- 验证网络连接和代理设置
- 查看日志中的具体错误信息

### 3. 向量检索无结果
- 确认知识库文档位于 `docs/` 目录
- 检查embedding模型配置
- 尝试手动重建向量：`POST /api/v1/vector/rebuild`

### 4. 记忆提取为空
- 检查 `ENABLE_LONG_MEMORY` 配置
- 确认对话内容包含可提取的关键信息
- 查看记忆提取相关日志

## 📚 扩展开发指南

### 添加新工具
1. 在 `tools/` 目录创建工具模块
2. 实现工具函数并使用 `@tool` 装饰器
3. 在 `harness/graph_builder.py` 的 `build_chat_graph()` 中注册工具
4. 更新Prompt以支持工具调用

**示例**：
```python
from langchain_core.tools import tool

@tool
def my_custom_tool(param1: str, param2: int) -> str:
    """工具描述，用于LLM理解工具用途"""
    # 实现逻辑
    return result
```

### 添加新Agent（多智能体模式）
1. 创建 `agents/` 目录（如尚未存在）
2. 创建新的Agent类，继承基类或独立实现
3. 在 `harness/graph_builder.py` 中添加节点和路由逻辑
4. 更新 `ChatState` 状态定义（如需要）

### 优化RAG效果
1. 改进文档切片策略（使用 LangChain text splitters）
2. 调整embedding模型参数
3. 优化相似度检索算法（调整 top_k）
4. 增加重排序机制（reranking）

## 📊 监控与维护

### 日志管理
- 日志按日期自动分割存储在 `logs/` 目录（如 `app-2026-04-29.log`）
- 第三方库日志级别已抑制，避免干扰
- 关键操作均有详细日志记录

### 关键监控指标
- API响应时间（P99 < 3秒）
- LLM调用成功率（> 99%）
- 向量检索准确率
- 记忆提取成功率
- 错误率和降级率

## 🔐 安全注意事项

1. **敏感信息保护**：API密钥等敏感信息存储在 `.env` 文件中，不提交到版本控制
2. **输入验证**：对用户输入进行敏感词检测
3. **权限控制**：根据用户ID隔离数据和记忆
4. **错误处理**：统一异常处理，避免敏感信息泄露

## 🔄 版本控制

- 主分支：`main`
- 功能开发：从 `main` 创建特性分支
- 代码审查：合并前需通过PR审查
- 标签管理：重要版本打tag

## 📞 支持资源

遇到问题时：
1. 查看日志文件：`logs/app-YYYY-MM-DD.log`
2. 查阅项目README.md和本文档
3. 参考LangGraph和FastAPI官方文档
4. 检查 `.env` 配置是否正确

---

**技能版本**: v1.0  
**适用项目**: LoveGuruAgent  
**更新日期**: 2026-04-29
