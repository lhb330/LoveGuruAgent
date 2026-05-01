"""LangGraph图构建模块

定义聊天处理的LangGraph工作流，包括Agent决策、工具调用、结果处理等节点。
实现智能工具路由：LLM自主决定是否调用外部工具。

五大核心功能集成点：
- 持久执行：通过checkpointer参数注入PostgresSaver/MemorySaver
- 人工参与：sensitive_filter_node + interrupt机制
- 全面记忆：load_context_node加载历史消息（短期）+长期记忆
"""
import logging
from typing import Optional, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import interrupt
from langchain_core.tools import tool

from harness.chain_builder import ChatChainBuilder
from harness.prompt_manager import PromptManager
from services.chat.rag_service import RAGService
from services.llm.factory import get_llm_service
from tools.baidu_map_tool import search_nearby_places
from config.settings import get_settings
from common.constants import SENSITIVE_KEYWORDS_DEFAULT

logger = logging.getLogger(__name__)


class ChatState(TypedDict, total=False):
    """聊天状态类型定义
    
    LangGraph中传递的状态对象，包含所有节点需要共享的数据。
    
    Attributes:
        conversation_id: 会话ID
        user_id: 用户标识（用于长期记忆关联）
        user_message: 用户消息文本
        messages: 消息历史列表（自动累加）
        assistant_reply: AI回复文本
        references: 参考文档列表
        is_sensitive: 是否检测到敏感内容
        sensitive_keywords: 命中的敏感关键词列表
        long_term_memory: 长期记忆上下文文本
        chat_history: 当前会话的历史对话文本
        reflection_count: 当前反思次数（用于限制最大反思轮数）
        self_evaluation: 自我评估结果（审查节点的反馈）
        need_regenerate: 是否需要重新生成回复
    """
    conversation_id: str
    user_id: str
    user_message: str
    messages: Annotated[list, lambda x, y: x + y]  # 消息历史（自动合并）
    assistant_reply: str
    references: list[dict]
    is_sensitive: bool
    sensitive_keywords: list[str]
    long_term_memory: str
    chat_history: str
    reflection_count: int
    self_evaluation: str
    need_regenerate: bool


def build_chat_graph(checkpointer: Optional[BaseCheckpointSaver] = None) -> CompiledStateGraph:
    """构建聊天LangGraph工作流
    
    创建包含以下节点的图：
    0. sensitive_filter: 敏感词检测节点（人工参与入口）
    1. agent: LLM决策节点，判断是否需要调用工具
    2. tools: 工具执行节点，执行LLM选择的工具
    3. tools_result: 工具结果处理节点，整合工具结果和RAG检索
    4. generate_reply: 常规回复节点，仅使用RAG检索
    5. generate_reply_stream: 流式回复节点
    
    Args:
        checkpointer: LangGraph检查点存储器，用于持久执行。
                      传入PostgresSaver实现数据库持久化，
                      传入MemorySaver实现内存级持久化，
                      None则不启用断点续传。
    
    Returns:
        CompiledStateGraph: 编译后的LangGraph图对象
    """
    builder = StateGraph(ChatState)
    chain = ChatChainBuilder()
    
    # 定义工具列表
    tools = [search_nearby_places]
    
    # 创建Tool Node
    tool_node = ToolNode(tools)
    
    # ========== 敏感词检测节点（人工参与 - Human-in-the-loop） ==========
    def sensitive_filter_node(state: ChatState) -> ChatState:
        """敏感词检测节点
        
        检测用户消息是否包含敏感内容。
        如果检测到敏感词且启用了敏感词过滤，则调用 interrupt() 挂起流程，
        等待人工审批后再继续执行。
        
        Args:
            state: 当前聊天状态
            
        Returns:
            ChatState: 更新后的状态（包含敏感词检测结果）
        """
        settings = get_settings()
        
        # 如果未启用敏感词过滤，直接放行
        if not settings.enable_sensitive_filter:
            return {"is_sensitive": False, "sensitive_keywords": []}
        
        user_message = state.get("user_message", "")
        
        # 获取敏感词列表（优先使用配置中的自定义列表）
        custom_keywords = settings.sensitive_keywords
        if custom_keywords:
            # 从逗号分隔字符串解析为列表
            keywords = [kw.strip() for kw in custom_keywords.split(",") if kw.strip()]
        else:
            keywords = SENSITIVE_KEYWORDS_DEFAULT
        
        # 检测命中的敏感词
        matched_keywords = [kw for kw in keywords if kw in user_message]
        
        if matched_keywords:
            # 调用 LangGraph interrupt，暂停图执行，等待人工审批
            interrupt({
                "type": "sensitive_content",
                "message": "检测到敏感内容，需要人工审批",
                "matched_keywords": matched_keywords,
                "user_message": user_message,
            })
            return {
                "is_sensitive": True,
                "sensitive_keywords": matched_keywords,
            }
        
        return {"is_sensitive": False, "sensitive_keywords": []}
    
    def check_sensitive(state: ChatState) -> str:
        """判断是否检测到敏感内容
        
        条件路由函数，根据敏感词检测结果决定下一步：
        - 敏感: 进入 agent 节点（正常执行，但 interrupt 已暂停等待审批）
        - 安全: 直接进入 agent 节点
        
        注意：当 interrupt() 被调用后，图执行会在该节点暂停。
        审批通过后，执行会从此节点恢复并继续到 agent。
        
        Args:
            state: 当前聊天状态
            
        Returns:
            str: 始终返回 "continue"，导向 agent 节点
        """
        return "continue"
    
    # ========== 上下文加载节点（全面记忆 - Comprehensive Memory） ==========
    def load_context_node(state: ChatState) -> ChatState:
        """上下文加载节点
        
        在对话开始前加载两类记忆：
        1. 短期记忆：从数据库加载当前会话的历史消息
        2. 长期记忆：从长期记忆库加载与用户相关的跨会话记忆
        
        Args:
            state: 当前聊天状态
            
        Returns:
            ChatState: 更新后的状态（包含加载的上下文）
        """
        from services.memory.memory_service import MemoryService
        from config.database import SessionLocal
        from dao.chat_message_dao import ChatMessageDAO
        
        conversation_id = state.get("conversation_id", "")
        user_id = state.get("user_id", "default_user")
        user_message = state.get("user_message", "")
        
        result = {}
        
        # 1. 加载短期记忆（当前会话历史消息）
        try:
            with SessionLocal() as session:
                dao = ChatMessageDAO(session)
                history_messages = dao.list_messages(conversation_id)
                if history_messages:
                    history_lines = []
                    for msg in history_messages[-10:]:  # 只取最近10条
                        role_label = "用户" if msg.role == "user" else "AI"
                        history_lines.append(f"{role_label}: {msg.content}")
                    result["chat_history"] = "\n".join(history_lines)
        except Exception as e:
            logger.warning(f"加载对话历史失败: {e}")
            result["chat_history"] = ""
        
        # 2. 加载长期记忆（跨会话记忆）
        try:
            memory_service = MemoryService()
            long_term_memory = memory_service.get_user_memories(user_id, user_message)
            result["long_term_memory"] = long_term_memory
        except Exception as e:
            logger.warning(f"加载长期记忆失败: {e}")
            result["long_term_memory"] = ""
        
        return result
    
    def should_use_tools(state: ChatState) -> str:
        """判断是否需要使用工具
        
        检查LLM的响应中是否包含工具调用请求。
        
        Args:
            state: 当前聊天状态
            
        Returns:
            str: "tools" 表示需要工具，"no_tools" 表示不需要
        """
        # 检查最后一条消息是否包含工具调用
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
        return "no_tools"
    
    def agent_node(state: ChatState) -> ChatState:
        """Agent节点 - LLM决策是否使用工具
        
        将工具绑定到LLM，让LLM自主判断是否需要调用工具。
        注入长期记忆和对话历史作为上下文。
        
        Args:
            state: 当前聊天状态
            
        Returns:
            ChatState: 更新后的状态（包含消息历史和初步回复）
        """
        user_message = state["user_message"]
        
        # 获取LLM服务并绑定工具
        llm_service = get_llm_service()
        llm = llm_service.get_llm()
        
        # 绑定工具到LLM
        llm_with_tools = llm.bind_tools(tools)
        
        # 构建消息历史
        messages = state.get("messages", [])
        
        # 注入长期记忆和对话历史作为系统上下文
        long_term_memory = state.get("long_term_memory", "")
        chat_history = state.get("chat_history", "")
        
        context_parts = []
        if long_term_memory:
            context_parts.append(long_term_memory)
        if chat_history:
            context_parts.append(f"## 当前会话历史\n{chat_history}")
        
        if context_parts:
            context_text = "\n\n".join(context_parts)
            # 在用户消息前插入上下文
            enriched_message = f"{context_text}\n\n## 用户最新消息\n{user_message}"
            messages.append(HumanMessage(content=enriched_message))
        else:
            messages.append(HumanMessage(content=user_message))

        # 只保留最近 5/6 条对话，防止体积爆炸
        messages = messages[-6:]  # 👈 加这一行
        # 调用LLM
        response = llm_with_tools.invoke(messages)
        
        # 更新消息历史
        messages.append(response)
        
        return {
            "messages": messages,
            "assistant_reply": response.content if response.content else ""
        }
    
    def tools_result_node(state: ChatState) -> ChatState:
        """工具执行后的处理节点
        
        整合工具执行结果和RAG检索结果，生成最终回复。
        
        Args:
            state: 当前聊天状态
            
        Returns:
            ChatState: 更新后的状态（包含最终回复和参考文档）
        """
        messages = state.get("messages", [])
        
        # 获取RAG参考
        references = chain.rag_service.retrieve(state["user_message"])
        
        # 构建最终回复
        # 提取工具调用结果
        tool_results = []
        for msg in messages:
            if isinstance(msg, ToolMessage):
                tool_results.append(msg.content)
        
        # 使用工具结果生成最终回复
        if tool_results:
            prompt = PromptManager.build_chat_prompt_with_tools(
                state["user_message"], 
                references, 
                {"status": 0, "results": tool_results}
            )
        else:
            prompt = PromptManager.build_chat_prompt(
                state["user_message"], 
                references
            )
        
        # 生成最终回复
        final_response = chain.llm_service.invoke(prompt)
        
        return {
            "assistant_reply": final_response,
            "references": references
        }
    
    def generate_reply(state: ChatState) -> ChatState:
        """常规回复节点（不使用工具）
        
        使用RAG检索和LLM生成回复，不调用外部工具。
        
        Args:
            state: 当前聊天状态
            
        Returns:
            ChatState: 更新后的状态（包含回复和参考文档）
        """
        answer, references = chain.run(state["user_message"])
        return {
            "assistant_reply": answer,
            "references": references,
        }
    
    def generate_reply_stream(state: ChatState) -> ChatState:
        """流式回复节点（不使用工具）
        
        使用RAG检索和LLM流式生成回复，不调用外部工具。
        支持逐字输出效果。
        
        Args:
            state: 当前聊天状态
            
        Returns:
            ChatState: 更新后的状态（包含回复和参考文档）
        """
        # 获取RAG参考
        references = chain.rag_service.retrieve(state["user_message"])
        
        # 构建提示词
        prompt = PromptManager.build_chat_prompt(
            state["user_message"], 
            references
        )
        
        # 流式调用LLM
        llm_service = get_llm_service()
        llm = llm_service.get_llm()
        
        # 使用流式调用
        full_response = ""
        for chunk in llm.stream(prompt):
            if chunk.content:
                full_response += chunk.content
        
        return {
            "assistant_reply": full_response,
            "references": references,
            "reflection_count": 0,  # 初始化反思计数
        }
    
    # ========== 自我反思节点（Self-Correction） ==========
    def critic_node(state: ChatState) -> ChatState:
        """自我审查节点 - 反思回复质量
        
        对生成的回复进行质量检查，确保：
        1. 回复针对用户问题
        2. 提供可执行的建议
        3. 语气温暖且专业
        4. 避免有害或不当建议
        5. 引用了知识库内容
        
        如果质量不达标，标记需要重新生成。
        最多反思2次，避免无限循环。
        
        Args:
            state: 当前聊天状态
            
        Returns:
            ChatState: 更新后的状态（包含审查结果）
        """
        from config.settings import get_settings
        
        settings = get_settings()
        
        # 检查是否启用反思机制
        if not hasattr(settings, 'enable_self_reflection') or not settings.enable_self_reflection:
            return {"need_regenerate": False, "self_evaluation": "反思机制未启用"}
        
        # 检查反思次数
        reflection_count = state.get("reflection_count", 0)
        max_reflections = getattr(settings, 'max_reflection_count', 2)
        
        if reflection_count >= max_reflections:
            logger.info(f"已达到最大反思次数 ({max_reflections})，跳过审查")
            return {"need_regenerate": False, "self_evaluation": "已达到最大反思次数"}
        
        user_message = state.get("user_message", "")
        assistant_reply = state.get("assistant_reply", "")
        references = state.get("references", [])
        
        # 构建反思 Prompt
        reflection_prompt = PromptManager.build_reflection_prompt(
            user_message=user_message,
            assistant_reply=assistant_reply,
            references=references,
            reflection_count=reflection_count
        )
        
        # 调用 LLM 进行审查
        try:
            llm_service = get_llm_service()
            llm = llm_service.get_llm()
            
            evaluation_response = llm.invoke(reflection_prompt)
            evaluation_text = evaluation_response.content if hasattr(evaluation_response, 'content') else str(evaluation_response)
            
            logger.info(f"自我审查结果: {evaluation_text[:200]}")
            
            # 解析审查结果（简单判断是否包含负面关键词）
            need_regenerate = False
            negative_keywords = ["需要改进", "不合格", "重新生成", "不够", "缺乏", "不适当"]
            for keyword in negative_keywords:
                if keyword in evaluation_text:
                    need_regenerate = True
                    break
            
            return {
                "need_regenerate": need_regenerate,
                "self_evaluation": evaluation_text,
                "reflection_count": reflection_count + 1
            }
            
        except Exception as e:
            logger.error(f"自我审查失败: {str(e)}", exc_info=True)
            # 审查失败时，默认通过
            return {"need_regenerate": False, "self_evaluation": f"审查失败: {str(e)}"}
    
    def should_regenerate(state: ChatState) -> str:
        """判断是否需要重新生成回复
        
        条件路由函数，根据审查结果决定下一步：
        - 需要改进: 返回 generate_reply_stream 重新生成
        - 通过审查: 结束流程
        
        Args:
            state: 当前聊天状态
            
        Returns:
            str: "regenerate" 或 "approve"
        """
        need_regenerate = state.get("need_regenerate", False)
        reflection_count = state.get("reflection_count", 0)
        max_reflections = getattr(get_settings(), 'max_reflection_count', 2)
        
        if need_regenerate and reflection_count < max_reflections:
            logger.info(f"审查未通过，第 {reflection_count} 次重新生成")
            return "regenerate"
        else:
            logger.info("审查通过或已达到最大反思次数")
            return "approve"
    
    # 添加节点
    builder.add_node("sensitive_filter", sensitive_filter_node)
    builder.add_node("load_context", load_context_node)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_node)
    builder.add_node("tools_result", tools_result_node)
    builder.add_node("generate_reply", generate_reply)
    builder.add_node("generate_reply_stream", generate_reply_stream)
    builder.add_node("critic", critic_node)  # 自我反思节点
    
    # 设置入口点：先经过敏感词过滤
    builder.set_entry_point("sensitive_filter")
    
    # 敏感词过滤 -> 上下文加载（条件边，interrupt 在此生效）
    builder.add_conditional_edges(
        "sensitive_filter",
        check_sensitive,
        {
            "continue": "load_context",
        }
    )
    
    # 上下文加载 -> agent
    builder.add_edge("load_context", "agent")
    
    # 添加条件边: agent -> tools 或 generate_reply
    builder.add_conditional_edges(
        "agent",
        should_use_tools,
        {
            "tools": "tools",
            "no_tools": "generate_reply_stream"  # 使用流式节点
        }
    )
    
    # tools执行后 -> tools_result
    builder.add_edge("tools", "tools_result")
    
    # 反思机制：generate_reply_stream -> critic -> [regenerate | approve]
    builder.add_edge("generate_reply_stream", "critic")
    builder.add_edge("tools_result", "critic")  # 工具结果也需经过反思
    
    # 反思后的条件路由
    builder.add_conditional_edges(
        "critic",
        should_regenerate,
        {
            "regenerate": "generate_reply_stream",  # 重新生成
            "approve": END  # 通过审查，结束
        }
    )
    
    # 编译图，注入checkpointer实现持久执行
    compile_kwargs = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    return builder.compile(**compile_kwargs)
