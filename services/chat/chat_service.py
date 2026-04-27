"""聊天服务模块

提供聊天相关的业务逻辑处理，包括消息发送、历史查询、会话清空等。
协调DAO层和LangGraph编排层完成完整的聊天流程。

LangGraph五大核心功能集成：
- 持久执行：通过checkpointer + thread_id(configurable)实现断点续传
- 人工参与：存储被中断的graph state引用，支持审批后恢复
- 全面记忆：对话结束后异步提取长期记忆
- 生产部署：graph调用重试机制（max 3 retries）
"""
import json
import time
from typing import Optional

from pydantic import BaseModel, Field
import logging

from common.constants import MessageType
import common.constants as constants
from config.database import SessionLocal
from dao.chat_message_dao import ChatMessageDAO
from harness.graph_builder import build_chat_graph
from langgraph.checkpoint.base import BaseCheckpointSaver


logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """聊天请求数据模型

    Attributes:
        conversation_id: 会话ID，用于标识一次独立的对话
        message: 用户发送的消息内容
        user_id: 用户标识（用于长期记忆关联），默认为 'default_user'
    """
    conversation_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="用户消息")
    user_id: str = Field(default="default_user", description="用户标识")


class ChatService:
    """聊天服务类
    处理聊天相关的核心业务逻辑：
    1. 保存用户消息
    2. 调用LangGraph生成AI回复（支持断点续传）
    3. 保存AI回复
    4. 查询聊天历史
    5. 清空会话记录
    6. 人工审批恢复
    
    Attributes:
        graph: 编译后的LangGraph图（已注入checkpointer）
        checkpointer: 检查点存储器，用于状态持久化
        _interrupted_states: 被中断的图状态引用 {thread_id: graph_state}
    """
    def __init__(self, checkpointer: Optional[BaseCheckpointSaver] = None) -> None:
        self.checkpointer = checkpointer
        self.graph = build_chat_graph(checkpointer=checkpointer)
        # 存储被中断的 graph state，用于人工审批后恢复
        self._interrupted_states: dict[str, dict] = {}

    def _build_graph_config(self, conversation_id: str) -> dict:
        """构建 LangGraph 调用配置
        
        注入 thread_id 用于 checkpointer 状态持久化，
        使得每次对话都能从上次中断处恢复。
        
        Args:
            conversation_id: 会话ID，作为 LangGraph 的 thread_id
            
        Returns:
            dict: LangGraph config，包含 configurable.thread_id
        """
        return {"configurable": {"thread_id": conversation_id}}

    def _invoke_graph_with_retry(self, state_input: dict, config: dict, max_retries: int = 3) -> dict:
        """带重试机制的图调用
        
        生产部署保护：当 graph.invoke 因临时错误失败时，
        自动重试最多 max_retries 次，采用指数退避策略。
        
        Args:
            state_input: 图输入状态
            config: LangGraph 配置（含 thread_id）
            max_retries: 最大重试次数，默认3次
            
        Returns:
            dict: 图执行结果状态
            
        Raises:
            Exception: 所有重试均失败时抛出最后一次异常
        """
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                return self.graph.invoke(state_input, config=config)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = 2 ** (attempt - 1)  # 指数退避: 1s, 2s, 4s
                    logger.warning(
                        f"图调用失败 (attempt {attempt}/{max_retries}), "
                        f"{wait_time}s 后重试: {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"图调用最终失败 (attempt {attempt}/{max_retries}): {str(e)}",
                        exc_info=True,
                    )
        raise last_exception

    def _extract_memories_async(
        self,
        user_id: str,
        user_message: str,
        assistant_reply: str,
        conversation_id: str,
    ) -> None:
        """对话结束后异步提取长期记忆
        
        使用 LLM 从对话中提取关键事实，存储到长期记忆库。
        此方法设计为非阻塞调用，不影响对话响应速度。
        
        Args:
            user_id: 用户标识
            user_message: 用户消息
            assistant_reply: AI回复
            conversation_id: 会话ID
        """
        if not user_message or not assistant_reply:
            logger.warning(f"记忆提取跳过: user_message或assistant_reply为空")
            return
        
        if len(assistant_reply) < 20:
            logger.warning(f"记忆提取跳过: assistant_reply太短({len(assistant_reply)}字符)")
            return
        
        try:
            from services.memory.memory_service import MemoryService
            memory_service = MemoryService()
            conversation_text = f"用户: {user_message}\nAI: {assistant_reply}"
            
            logger.info(f"启动记忆提取线程: user_id={user_id}, conversation_text长度={len(conversation_text)}")
            logger.debug(f"对话内容预览 - 用户消息: {user_message[:100]}")
            
            # 记忆提取（在后台线程中执行）
            import threading
            def _extract():
                try:
                    logger.info(f"记忆提取开始: user_id={user_id}, conversation_id={conversation_id}")
                    logger.info(f"完整对话内容:\n{conversation_text[:500]}")
                    count = memory_service.extract_and_save_memories(
                        user_id=user_id,
                        conversation_text=conversation_text,
                        conversation_id=conversation_id,
                    )
                    logger.info(
                        f"记忆提取完成: user_id={user_id}, "
                        f"conversation_id={conversation_id}, "
                        f"new_memories={count}"
                    )
                except Exception as e:
                    logger.error(f"后台记忆提取失败: {e}", exc_info=True)
            
            thread = threading.Thread(target=_extract, daemon=True)
            thread.start()
            logger.info(f"记忆提取线程已启动")
            
        except Exception as e:
            logger.error(f"启动记忆提取失败: {e}", exc_info=True)

    def chat(self, request: ChatRequest) -> dict:
        """同步聊天接口（支持断点续传）
        
        通过 checkpointer + thread_id 实现持久执行：
        - 如果该 conversation_id 之前因异常中断，可以从断点恢复
        - 如果该 conversation_id 之前被敏感词拦截，可以从审批处恢复
        
        Args:
            request: 聊天请求
            
        Returns:
            dict: 包含回复和参考文档的响应
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
                    user_id=request.user_id,
                )

                # 调用LangGraph生成回复（带thread_id实现持久执行 + 重试机制）
                config = self._build_graph_config(request.conversation_id)
                state = self._invoke_graph_with_retry(
                    {
                        "conversation_id": request.conversation_id,
                        "user_message": request.message,
                        "user_id": request.user_id,
                    },
                    config=config,
                )
                reply = state.get("assistant_reply", "")

                # 检查是否被敏感词拦截（人工参与）
                if state.get("__interrupt__"):
                    # 存储被中断的状态，等待人工审批
                    self._interrupted_states[request.conversation_id] = state
                    return {
                        "conversation_id": request.conversation_id,
                        "reply": "",
                        "references": [],
                        "pending_approval": True,
                        "interrupt_info": state.get("__interrupt__"),
                    }

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

            # 对话结束后异步提取长期记忆（全面记忆）
            self._extract_memories_async(
                user_id=getattr(request, 'user_id', 'default_user'),
                user_message=request.message,
                assistant_reply=reply,
                conversation_id=request.conversation_id,
            )

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
        流式聊天接口（打字机效果，支持断点续传）
        SSE 标准格式返回，前端直接解析。
        通过 checkpointer + thread_id 实现状态持久化。
        """
        full_reply = ""
        references = []
        config = self._build_graph_config(request.conversation_id)

        # 1. 先保存用户消息
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            try:
                dao.save_message(
                    conversation_id=request.conversation_id,
                    message_type=MessageType.USER.value,
                    content=request.message,
                    role="user",
                    user_id=request.user_id,
                )
                session.commit()
            except Exception:
                session.rollback()
                raise

        # 2. 流式调用 LangGraph（带 config 支持持久执行）
        try:
            # 使用 stream_mode="messages" 获取LLM的流式输出
            async for event in self.graph.astream(
                    {
                        "conversation_id": request.conversation_id,
                        "user_message": request.message,
                        "user_id": request.user_id,
                    },
                    stream_mode="messages",
                    config=config,
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
                    user_id=request.user_id,  # 修复：添加user_id参数
                )
                session.commit()
            except Exception as e:
                logger.error(f"保存AI回复失败: {str(e)}", exc_info=True)
                session.rollback()

        # 4. 对话结束后异步提取长期记忆（全面记忆）
        # 添加日志以便调试
        logger.info(f"准备提取记忆: user_id={request.user_id}, conversation_id={request.conversation_id}")
        logger.info(f"对话内容长度: user_message={len(request.message)}, assistant_reply={len(full_reply)}")
        
        self._extract_memories_async(
            user_id=request.user_id,
            user_message=request.message,
            assistant_reply=full_reply,
            conversation_id=request.conversation_id,
        )

        # 5. 结束标志
        yield f"data: {json.dumps({'content': '', 'done': True, 'references': references}, ensure_ascii=False)}\n\n"
    # ==================================================================

    # ===================== 【人工参与：审批恢复】 =====================
    def approve_message(self, conversation_id: str, approved: bool, override_reply: str = None) -> dict:
        """人工审批接口
        
        对被敏感词拦截的消息进行人工审批：
        - 审批通过：恢复图执行，继续生成回复
        - 审批拒绝：返回预设的安全回复
        - 覆盖回复：审批者可以直接指定回复内容
        
        Args:
            conversation_id: 会话ID
            approved: 是否审批通过
            override_reply: 人工指定的回复内容（可选）
            
        Returns:
            dict: 包含最终回复的响应
        """
        if not self.checkpointer:
            return {
                "conversation_id": conversation_id,
                "reply": "系统未启用人工审批功能（checkpointer未配置）",
                "approved": False,
            }

        config = self._build_graph_config(conversation_id)

        try:
            if approved:
                if override_reply:
                    # 审批者直接指定了回复内容
                    reply = override_reply
                else:
                    # 恢复图执行，从敏感词拦截点继续
                    from langgraph.types import Command
                    state = self.graph.invoke(
                        Command(resume={"approved": True}),
                        config=config,
                    )
                    reply = state.get("assistant_reply", "")

                # 保存AI回复
                with SessionLocal() as session:
                    dao = ChatMessageDAO(session)
                    try:
                        dao.save_message(
                            conversation_id=conversation_id,
                            message_type=MessageType.ASSISTANT.value,
                            content=reply,
                            role="assistant",
                        )
                        session.commit()
                    except Exception:
                        session.rollback()

                # 清理中断状态
                self._interrupted_states.pop(conversation_id, None)

                # 对话结束后异步提取长期记忆（全面记忆）
                # 注意：审批通过的对话也需要提取记忆
                # 这里需要从 state 或数据库中获取用户消息
                # 为简化处理，如果 override_reply 有值，使用空的用户消息（不提取记忆）
                if not override_reply:
                    try:
                        with SessionLocal() as session:
                            dao = ChatMessageDAO(session)
                            user_messages = dao.list_messages(conversation_id)
                            # 获取最后一条用户消息
                            last_user_msg = None
                            for msg in reversed(user_messages):
                                if msg.role == "user":
                                    last_user_msg = msg.content
                                    break
                            
                            if last_user_msg:
                                self._extract_memories_async(
                                    user_id="default_user",  # 审批场景暂时使用默认用户
                                    user_message=last_user_msg,
                                    assistant_reply=reply,
                                    conversation_id=conversation_id,
                                )
                    except Exception as e:
                        logger.warning(f"审批后记忆提取失败: {e}")

                return {
                    "conversation_id": conversation_id,
                    "reply": reply,
                    "approved": True,
                }
            else:
                # 审批拒绝，返回安全提示
                safe_reply = "抱歉，您的问题涉及敏感内容，暂时无法提供回复。如需帮助，请尝试其他话题。"
                # 清理中断状态
                self._interrupted_states.pop(conversation_id, None)
                return {
                    "conversation_id": conversation_id,
                    "reply": safe_reply,
                    "approved": False,
                }
        except Exception as e:
            logger.error(f"审批恢复失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
            return {
                "conversation_id": conversation_id,
                "reply": "审批处理失败，请重试",
                "approved": False,
                "error": str(e),
            }

    def resume_conversation(self, conversation_id: str) -> dict:
        """断点续传恢复接口
        
        基于 thread_id（conversation_id）恢复因异常中断的对话。
        LangGraph 的 checkpointer 会自动从最后保存的状态继续执行。
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            dict: 包含恢复后回复的响应
        """
        if not self.checkpointer:
            return {
                "conversation_id": conversation_id,
                "reply": "断点续传功能未启用（checkpointer未配置）",
            }

        config = self._build_graph_config(conversation_id)

        try:
            # 传入 None 作为输入，LangGraph 会从 checkpointer 恢复最后的状态继续执行
            state = self.graph.invoke(None, config=config)
            reply = state.get("assistant_reply", "")

            # 保存恢复后的回复
            if reply:
                with SessionLocal() as session:
                    dao = ChatMessageDAO(session)
                    try:
                        dao.save_message(
                            conversation_id=conversation_id,
                            message_type=MessageType.ASSISTANT.value,
                            content=reply,
                            role="assistant",
                        )
                        session.commit()
                    except Exception:
                        session.rollback()

            return {
                "conversation_id": conversation_id,
                "reply": reply,
                "references": state.get("references", []),
            }
        except Exception as e:
            logger.error(f"断点续传恢复失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
            raise
    # ==================================================================