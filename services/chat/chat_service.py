"""聊天服务模块

提供聊天相关的业务逻辑处理，包括消息发送、历史查询、会话清空等。
协调DAO层和LangGraph编排层完成完整的聊天流程。
"""
from pydantic import BaseModel, Field

from common.constants import MessageType
from config.database import SessionLocal
from dao.chat_message_dao import ChatMessageDAO
from harness.graph_builder import build_chat_graph


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
    
    Attributes:
        graph: LangGraph编译后的图对象，用于执行聊天流程
    """
    
    def __init__(self) -> None:
        """初始化聊天服务
        
        构建LangGraph图对象，后续用于处理聊天请求。
        """
        self.graph = build_chat_graph()

    def chat(self, request: ChatRequest) -> dict:
        """处理聊天请求
        
        完整的聊天流程：
        1. 保存用户消息到数据库
        2. 调用LangGraph生成回复（包括RAG检索和工具调用）
        3. 保存AI回复到数据库
        4. 返回回复和参考文档
        
        Args:
            request: 聊天请求对象
            
        Returns:
            dict: 包含conversation_id、reply、references的字典
            
        Raises:
            Exception: 数据库操作或AI调用失败时抛出异常
        """
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
        """查询聊天历史
        
        获取指定会话的完整聊天记录，按时间升序排列。
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            list[dict]: 聊天消息列表，每个消息包含id、role、content等字段
        """
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
        """清空聊天历史
        
        删除指定会话的所有消息记录。
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            dict: 包含conversation_id和deleted（删除数量）的字典
            
        Raises:
            Exception: 数据库操作失败时抛出异常
        """
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            try:
                deleted = dao.clear_messages(conversation_id)
                session.commit()
            except Exception:
                session.rollback()
                raise
            return {"conversation_id": conversation_id, "deleted": deleted}
