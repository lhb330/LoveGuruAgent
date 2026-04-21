"""聊天服务模块

提供聊天相关的业务逻辑处理，包括消息发送、历史查询、会话清空等。
协调DAO层和LangGraph编排层完成完整的聊天流程。
"""
import json

from pydantic import BaseModel, Field
import logging

from common.constants import MessageType
import common.constants as constants
from config.database import SessionLocal
from dao.chat_message_dao import ChatMessageDAO
from harness.graph_builder import build_chat_graph


logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """聊天请求数据模型

    Attributes:
        conversation_id: 会话ID，用于标识一次独立的对话
        message: 用户发送的消息内容
    """
    conversation_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="用户消息")


class ChatService:
    """聊天服务类
    处理聊天相关的核心业务逻辑：
    1. 保存用户消息
    2. 调用LangGraph生成AI回复
    3. 保存AI回复
    4. 查询聊天历史
    5. 清空会话记录
    """
    def __init__(self) -> None:
        self.graph = build_chat_graph()

    def chat(self, request: ChatRequest) -> dict:
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            try:
                # 保存用户消息
                dao.save_message(
                    conversation_id=request.conversation_id,
                    message_type=MessageType.USER.value,
                    content=request.message,
                    role="user",
                )

                # 调用LangGraph生成回复
                state = self.graph.invoke(
                    {
                        "conversation_id": request.conversation_id,
                        "user_message": request.message,
                    }
                )
                reply = state["assistant_reply"]

                # 保存AI回复
                dao.save_message(
                    conversation_id=request.conversation_id,
                    message_type=MessageType.ASSISTANT.value,
                    content=reply,
                    role="assistant",
                )
                session.commit()
            except Exception:
                session.rollback()
                raise

            return {
                "conversation_id": request.conversation_id,
                "reply": reply,
                "references": state.get("references", []),
            }

    def history(self, conversation_id: str) -> list[dict]:
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            messages = dao.list_messages(conversation_id)
            return [
                {
                    "id": item.id,
                    "conversation_id": item.conversation_id,
                    "message_type": item.message_type,
                    "role": item.role,
                    "content": item.content,
                    "create_time": item.create_time.isoformat(),
                }
                for item in messages
            ]

    def clear(self, conversation_id: str) -> dict:
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            try:
                deleted = dao.clear_messages(conversation_id)
                session.commit()
            except Exception:
                session.rollback()
                raise
            return {"conversation_id": conversation_id, "deleted": deleted}

    def historyAllMessage(self) -> list[dict]:
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            # 查询所有消息
            all_messages = dao.list_all_messages()
            logger.info(f"查询到消息数量: {len(all_messages)}")
            
            result = [
                {
                    "id": item.id,
                    "conversation_id": item.conversation_id,
                    "message_type": item.message_type,
                    "role": item.role,
                    "content": item.content,
                    "create_time": item.create_time.isoformat(),
                }
                for item in all_messages
            ]
            logger.info(f"返回结果数量: {len(result)}")
            return result

    def get_conversation_groups(self) -> list[dict]:
        """获取按conversation_id分组的对话列表
        
        将相同conversation_id的消息合并成一条记录，
        以role=user的最后一条消息内容为准。
        
        Returns:
            list[dict]: 分组后的对话列表
        """
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            grouped_messages = dao.list_grouped_by_conversation()
            logger.info(f"查询到分组对话数量: {len(grouped_messages)}")
            return grouped_messages


    def get_conv_id(self) -> str:
        """开启新会话时生成新id"""
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            return constants.generate_conversation_id(dao.max_seq())

    # ===================== 【流式输出：打字机效果】 =====================
    async def chat_stream(self, request: ChatRequest):
        """
        流式聊天接口（打字机效果）
        SSE 标准格式返回，前端直接解析
        """
        full_reply = ""
        references = []

        # 1. 先保存用户消息
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            try:
                dao.save_message(
                    conversation_id=request.conversation_id,
                    message_type=MessageType.USER.value,
                    content=request.message,
                    role="user",
                )
                session.commit()
            except Exception:
                session.rollback()
                raise

        # 2. 流式调用 LangGraph
        try:
            # 使用 stream_mode="messages" 获取LLM的流式输出
            async for event in self.graph.astream(
                    {
                        "conversation_id": request.conversation_id,
                        "user_message": request.message,
                    },
                    stream_mode="messages"
            ):
                # event 是一个元组: (message, metadata)
                if isinstance(event, tuple) and len(event) == 2:
                    message, metadata = event
                    # 只处理AIMessage类型的流式输出
                    if hasattr(message, 'content') and message.content:
                        content = message.content
                        full_reply += content
                        # 逐字发送
                        yield f"data: {json.dumps({'content': content, 'done': False}, ensure_ascii=False)}\n\n"
                # 处理updates模式
                elif isinstance(event, dict):
                    for node_name, node_output in event.items():
                        if "assistant_reply" in node_output:
                            reply_chunk = node_output["assistant_reply"]
                            if reply_chunk and isinstance(reply_chunk, str):
                                full_reply = reply_chunk
                        if "references" in node_output:
                            references = node_output["references"]

        except Exception as e:
            logger.error(f"流式生成失败: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'content': '', 'error': str(e), 'done': True}, ensure_ascii=False)}\n\n"
            return

        # 3. 保存完整的AI回复到数据库
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            try:
                dao.save_message(
                    conversation_id=request.conversation_id,
                    message_type=MessageType.ASSISTANT.value,
                    content=full_reply,
                    role="assistant",
                )
                session.commit()
            except Exception:
                session.rollback()

        # 4. 结束标志
        yield f"data: {json.dumps({'content': '', 'done': True, 'references': references}, ensure_ascii=False)}\n\n"
    # ==================================================================