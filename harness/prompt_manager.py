"""Prompt管理模块

负责组装不同类型的Prompt，包括常规聊天Prompt和带工具结果的Prompt。
将系统提示词、知识库引用、工具结果、用户问题等组合成完整的Prompt。
"""
from common.constants import LOVE_GURU_SYSTEM_PROMPT


class PromptManager:
    """Prompt管理器类
    
    提供静态方法组装不同类型的Prompt：
    1. 常规聊天Prompt（仅包含知识库）
    2. 带工具结果的Prompt（包含知识库和工具搜索结果）
    """
    
    @staticmethod
    def build_chat_prompt(user_message: str, references: list[dict]) -> str:
        """构建常规聊天Prompt
        
        将系统提示词、知识库引用和用户问题组合成完整的Prompt。
        
        Args:
            user_message: 用户消息文本
            references: 知识库参考文档列表
            
        Returns:
            str: 组装好的完整Prompt
        """
        reference_text = "\n\n".join(
            f"[{item['doc_name']}]\n{item['content']}" for item in references
        ) or "暂无知识库参考内容。"
        return (
            f"{LOVE_GURU_SYSTEM_PROMPT}\n\n"
            f"知识库参考：\n{reference_text}\n\n"
            f"用户问题：\n{user_message}\n\n"
            "请给出真诚、具体、可执行的回答。"
        )
    
    @staticmethod
    def build_chat_prompt_with_tools(
        user_message: str, 
        references: list[dict], 
        tool_results: dict
    ) -> str:
        """构建带工具结果的聊天Prompt
        
        将系统提示词、知识库引用、工具搜索结果和用户问题组合成完整的Prompt。
        用于需要整合外部工具（如地图搜索）结果的场景。
        
        Args:
            user_message: 用户消息文本
            references: 知识库参考文档列表
            tool_results: 工具搜索结果字典，包含status和results字段
            
        Returns:
            str: 组装好的完整Prompt，包含工具搜索结果
        """
        reference_text = "\n\n".join(
            f"[{item['doc_name']}]\n{item['content']}" for item in references
        ) or "暂无知识库参考内容。"
        
        # 添加工具调用结果
        tool_text = ""
        results = tool_results.get("results", [])
        
        if results:
            tool_text = "\n\n工具搜索结果：\n"
            for i, result in enumerate(results, 1):
                tool_text += f"{result}\n\n"
        else:
            tool_text = "\n\n工具搜索未找到相关结果。"
        
        return (
            f"{LOVE_GURU_SYSTEM_PROMPT}\n\n"
            f"知识库参考：\n{reference_text}\n"
            f"{tool_text}\n\n"
            f"用户问题：\n{user_message}\n\n"
            "请基于以上信息(包括工具搜索结果)给出真诚、具体、可执行的回答。"
        )
