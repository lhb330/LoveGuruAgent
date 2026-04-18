"""LLM服务工厂模块

根据配置动态创建对应的LLM服务实例。
支持OpenAI和通义千问两种模型提供商。
"""
from config.settings import get_settings
from services.llm.base_llm import BaseLLMService
from services.llm.openai_service import OpenAIService
from services.llm.qwen_service import QwenService


def get_llm_service() -> BaseLLMService:
    """获取LLM服务实例
    
    根据.env配置中的LLM_PROVIDER值，创建对应的LLM服务实例。
    使用工厂模式实现多模型支持的解耦。
    
    Returns:
        BaseLLMService: LLM服务实例（OpenAIService或QwenService）
        
    Example:
        >>> llm_service = get_llm_service()
        >>> response = llm_service.invoke("你好")
    """
    settings = get_settings()
    if settings.llm_provider.lower() == "openai":
        return OpenAIService()
    return QwenService()
