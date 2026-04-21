"""LangGraph图构建模块

定义聊天处理的LangGraph工作流，包括Agent决策、工具调用、结果处理等节点。
实现智能工具路由：LLM自主决定是否调用外部工具。
"""
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

from harness.chain_builder import ChatChainBuilder
from harness.prompt_manager import PromptManager
from services.chat.rag_service import RAGService
from services.llm.factory import get_llm_service
from tools.baidu_map_tool import search_nearby_places


class ChatState(TypedDict, total=False):
    """聊天状态类型定义
    
    LangGraph中传递的状态对象，包含所有节点需要共享的数据。
    
    Attributes:
        conversation_id: 会话ID
        user_message: 用户消息文本
        messages: 消息历史列表（自动累加）
        assistant_reply: AI回复文本
        references: 参考文档列表
    """
    conversation_id: str
    user_message: str
    messages: Annotated[list, lambda x, y: x + y]  # 消息历史（自动合并）
    assistant_reply: str
    references: list[dict]


def build_chat_graph():
    """构建聊天LangGraph工作流
    
    创建包含以下节点的图：
    1. agent: LLM决策节点，判断是否需要调用工具
    2. tools: 工具执行节点，执行LLM选择的工具
    3. tools_result: 工具结果处理节点，整合工具结果和RAG检索
    4. generate_reply: 常规回复节点，仅使用RAG检索
    
    Returns:
        CompiledStateGraph: 编译后的LangGraph图对象
    """
    builder = StateGraph(ChatState)
    chain = ChatChainBuilder()
    
    # 定义工具列表
    tools = [search_nearby_places]
    
    # 创建Tool Node
    tool_node = ToolNode(tools)
    
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
        messages.append(HumanMessage(content=user_message))
        
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
        }
    
    # 添加节点
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_node)
    builder.add_node("tools_result", tools_result_node)
    builder.add_node("generate_reply", generate_reply)
    builder.add_node("generate_reply_stream", generate_reply_stream)
    
    # 设置入口点
    builder.set_entry_point("agent")
    
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
    
    # 结束节点
    builder.add_edge("tools_result", END)
    builder.add_edge("generate_reply_stream", END)
    
    return builder.compile()
