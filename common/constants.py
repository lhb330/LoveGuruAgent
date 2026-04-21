from enum import Enum

from common.utils.DateUtil import DateUtil


class MessageType(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"



LOVE_GURU_SYSTEM_PROMPT = """
你是“恋爱大师”AI助手，专注解决恋爱沟通、情绪安抚、关系经营问题。
回答温柔真诚、简洁精炼，**只给核心结论与可执行建议，不展开多余解释，不写长篇内容**。
有知识库依据时，结合知识库简要回答。
""".strip()

@staticmethod
def generate_conversation_id(seq: int) -> str:
    """
    生成会话ID
    :param seq: 序列号
    :return: conv-yyyyMMdd-seq
    """
    date_str = DateUtil.local_date_to_string(DateUtil.get_now_date(), DateUtil.YMD)
    return f"conv-{date_str}-{seq}"