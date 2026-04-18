from common.constants import LOVE_GURU_SYSTEM_PROMPT


class PromptManager:
    @staticmethod
    def build_chat_prompt(user_message: str, references: list[dict]) -> str:
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
        """构建包含工具调用结果的提示词"""
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
