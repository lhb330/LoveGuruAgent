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
    conversation_id: str
    user_message: str
    messages: Annotated[list, lambda x, y: x + y]  # 消息历史
    assistant_reply: str
    references: list[dict]


def build_chat_graph():
    builder = StateGraph(ChatState)
    chain = ChatChainBuilder()
    
    # 定义工具列表
    tools = [search_nearby_places]
    
    # 创建Tool Node
    tool_node = ToolNode(tools)
    
    def should_use_tools(state: ChatState) -> str:
        """判断是否需要使用工具"""
        # 检查最后一条消息是否包含工具调用
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
        return "no_tools"
    
    def agent_node(state: ChatState) -> ChatState:
        """Agent节点 - 决定是使用工具还是直接回答"""
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
        """工具执行后的处理节点"""
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
        """常规回复节点(不使用工具)"""
        answer, references = chain.run(state["user_message"])
        return {
            "assistant_reply": answer,
            "references": references,
        }
    
    # 添加节点
    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_node)
    builder.add_node("tools_result", tools_result_node)
    builder.add_node("generate_reply", generate_reply)
    
    # 设置入口点
    builder.set_entry_point("agent")
    
    # 添加条件边: agent -> tools 或 generate_reply
    builder.add_conditional_edges(
        "agent",
        should_use_tools,
        {
            "tools": "tools",
            "no_tools": "generate_reply"
        }
    )
    
    # tools执行后 -> tools_result
    builder.add_edge("tools", "tools_result")
    
    # 结束节点
    builder.add_edge("tools_result", END)
    builder.add_edge("generate_reply", END)
    
    return builder.compile()
