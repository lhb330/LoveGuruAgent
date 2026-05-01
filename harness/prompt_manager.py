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
    
    @staticmethod
    def build_reflection_prompt(
        user_message: str,
        assistant_reply: str,
        references: list[dict],
        reflection_count: int = 0
    ) -> str:
        """构建自我反思 Prompt
        
        用于审查 AI 生成的回复质量，确保回复符合恋爱咨询的专业标准。
        
        Args:
            user_message: 用户原始问题
            assistant_reply: AI 生成的回复
            references: 知识库参考文档列表
            reflection_count: 当前反思次数
            
        Returns:
            str: 反思审查 Prompt
        """
        # 构建参考文档摘要
        reference_summary = ""
        if references:
            ref_names = [ref.get('doc_name', '') for ref in references[:3]]
            reference_summary = f"\n已参考知识库: {', '.join(ref_names)}"
        else:
            reference_summary = "\n未使用知识库参考"
        
        prompt = f"""你是一位资深的恋爱心理咨询专家，现在需要审查一位AI助手的回复质量。

## 用户问题
{user_message}

## AI助手的回复
{assistant_reply}
{reference_summary}

## 审查标准
请从以下5个维度评估回复质量：

1. **针对性**：回复是否直接回应了用户的核心问题？
2. **可执行性**：是否提供了具体、可操作的建议？
3. **情感温度**：语气是否温暖、共情、给予情感支持？
4. **专业安全**：是否避免了有害、极端或不恰当的建议？
5. **知识引用**：是否合理引用了恋爱心理学知识？

## 输出要求
请用简洁的中文回答，包含：
- 总体评价（合格/需要改进）
- 具体不足（如果有）
- 改进建议（如果需要重新生成）

**注意**：
- 如果回复质量良好，请直接说"合格，无需改进"
- 如果有明显不足，请指出并说"需要改进，建议重新生成"
- 这是第 {reflection_count + 1} 次审查，请严格把关"""
        
        return prompt
