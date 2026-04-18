import dashscope

from common.exceptions import LLMInvokeException
from config.settings import get_settings
from services.llm.base_llm import BaseLLMService


class QwenService(BaseLLMService):
    def __init__(self) -> None:
        self.settings = get_settings()
        dashscope.api_key = self.settings.dashscope_api_key

    def invoke(self, prompt: str) -> str:
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
        """DashScope不支持LangChain工具绑定,返回None"""
        # TODO: 如果需要使用LangChain工具,建议使用OpenAI兼容接口
        raise NotImplementedError("DashScope API does not support LangChain tool binding. Please use OpenAI-compatible API instead.")

    def embed_text(self, text: str) -> list[float]:
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
        if isinstance(response, dict):
            return response
        try:
            return dict(response)
        except Exception as exc:
            raise LLMInvokeException(f"Unexpected DashScope response type: {type(response).__name__}") from exc

    def _raise_if_failed(self, payload: dict, operation: str, model: str) -> None:
        output = payload.get("output")
        if output is not None:
            return

        status_code = payload.get("status_code", "unknown")
        code = payload.get("code", "UnknownError")
        message = payload.get("message", "DashScope returned empty output.")
        request_id = payload.get("request_id", "unknown")

        if self.settings.dashscope_api_key == "your_dashscope_api_key":
            message = "DASHSCOPE_API_KEY is still the placeholder value in .env."

        raise LLMInvokeException(
            f"DashScope {operation} failed for model '{model}': "
            f"status={status_code}, code={code}, message={message}, request_id={request_id}"
        )
