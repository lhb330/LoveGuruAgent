from config.settings import get_settings
from services.llm.base_llm import BaseLLMService
from services.llm.openai_service import OpenAIService
from services.llm.qwen_service import QwenService


def get_llm_service() -> BaseLLMService:
    settings = get_settings()
    if settings.llm_provider.lower() == "openai":
        return OpenAIService()
    return QwenService()
