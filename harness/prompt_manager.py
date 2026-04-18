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
