import dashscope

from common.exceptions import LLMInvokeException
from config.settings import get_settings
from services.llm.base_llm import BaseLLMService


class QwenService(BaseLLMService):
    """通义千问LLM服务类
    
    封装阿里云DashScope API的调用，包括：
    1. 聊天生成（通义千问模型）
    2. 文本向量化（通义千问Embedding模型）
    
    Note:
        DashScope API不支持LangChain的工具绑定功能，
        如果需要使用工具，建议使用OpenAI兼容接口。
    
    Attributes:
        settings: 应用配置实例
    """
    
    def __init__(self) -> None:
        """初始化通义千问服务
        
        设置DashScope API密钥。
        """
        self.settings = get_settings()
        dashscope.api_key = self.settings.dashscope_api_key.get_secret_value()  # 修复：SecretStr 转字符串

    def invoke(self, prompt: str) -> str:
        """调用通义千问聊天模型生成回复
        
        Args:
            prompt: 提示词文本
            
        Returns:
            str: AI生成的回复文本
            
        Raises:
            LLMInvokeException: API调用失败时抛出
        """
        try:
            response = dashscope.Generation.call(
                model=self.settings.qwen_model,
                prompt=prompt,
                result_format="message",
            )
            payload = self._normalize_response(response)
            self._raise_if_failed(payload, operation="generation", model=self.settings.qwen_model)
            return payload["output"]["choices"][0]["message"]["content"]
        except Exception as exc:
            raise LLMInvokeException(str(exc)) from exc
    
    def get_llm(self):
        """获取底层LLM实例
        
        DashScope不支持LangChain工具绑定，因此抛出异常。
        
        Raises:
            NotImplementedError: 始终抛出，提示使用OpenAI兼容接口
        """
        # TODO: 如果需要使用LangChain工具,建议使用OpenAI兼容接口
        raise NotImplementedError("DashScope API does not support LangChain tool binding. Please use OpenAI-compatible API instead.")

    def embed_text(self, text: str) -> list[float]:
        """将文本转换为向量
        
        Args:
            text: 要转换的文本
            
        Returns:
            list[float]: 浮点数向量，维度取决于embedding模型
            
        Raises:
            LLMInvokeException: API调用失败时抛出
        """
        try:
            response = dashscope.TextEmbedding.call(
                model=self.settings.qwen_embedding_model,
                input=text,
            )
            payload = self._normalize_response(response)
            self._raise_if_failed(
                payload,
                operation="embedding",
                model=self.settings.qwen_embedding_model,
            )
            return payload["output"]["embeddings"][0]["embedding"]
        except Exception as exc:
            raise LLMInvokeException(str(exc)) from exc

    @staticmethod
    def _normalize_response(response: object) -> dict:
        """标准化API响应为字典格式
        
        Args:
            response: API原始响应对象
            
        Returns:
            dict: 标准化后的字典格式响应
            
        Raises:
            LLMInvokeException: 响应格式不支持时抛出
        """
        if isinstance(response, dict):
            return response
        try:
            return dict(response)
        except Exception as exc:
            raise LLMInvokeException(f"Unexpected DashScope response type: {type(response).__name__}") from exc

    def _raise_if_failed(self, payload: dict, operation: str, model: str) -> None:
        """检查API响应是否失败，如果失败则抛出异常
        
        Args:
            payload: API响应字典
            operation: 操作类型（generation/embedding）
            model: 模型名称
            
        Raises:
            LLMInvokeException: 当API调用失败时抛出，包含详细错误信息
        """
        output = payload.get("output")
        if output is not None:
            return

        status_code = payload.get("status_code", "unknown")
        code = payload.get("code", "UnknownError")
        message = payload.get("message", "DashScope returned empty output.")
        request_id = payload.get("request_id", "unknown")

        # 检查API Key是否还是默认值
        if self.settings.dashscope_api_key == "your_dashscope_api_key":
            message = "DASHSCOPE_API_KEY is still the placeholder value in .env."

        raise LLMInvokeException(
            f"DashScope {operation} failed for model '{model}': "
            f"status={status_code}, code={code}, message={message}, request_id={request_id}"
        )
