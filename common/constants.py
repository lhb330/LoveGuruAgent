from enum import Enum

from common.utils.DateUtil import DateUtil


class MessageType(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"



LOVE_GURU_SYSTEM_PROMPT = """
你是“恋爱大师”AI 助手，擅长帮助用户处理恋爱、沟通、情绪管理和关系经营问题。
回答要温柔、具体、真诚，优先给出可执行建议；当知识库提供了相关依据时，要结合知识库内容生成答案。
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