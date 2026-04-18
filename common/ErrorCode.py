from enum import Enum


# 错误码枚举
class ErrorCode(Enum):
    SUCCESS = (0, "success")
    BUSINESS = (40000,"业务异常")
    SYSTEM_ERROR = (50000, "系统繁忙，请稍后再试")
    OPERATION_ERROR = (50001, "操作失败，请重试")

    # MCP调用自定义码
    MCP_CALL_ERROR = (60000, "工具调用失败")
    # 工具调用自定义码
    TOOL_CALL_ERROR = (70000, "工具调用失败")
    # 大模型调用自定义码
    LLM_CALL_ERROR = (80000, "AI服务调用异常")

    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg

    def get_code(self):
        return self.code

    def get_msg(self):
        return self.msg
