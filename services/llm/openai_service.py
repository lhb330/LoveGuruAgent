"""OpenAI LLM服务实现

提供OpenAI兼容接口的聊天和embedding功能。
支持所有OpenAI兼容的API服务（如OpenAI本身、Azure OpenAI、本地部署等）。
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from common.exceptions import LLMInvokeException
from config.settings import get_settings
from services.llm.base_llm import BaseLLMService


class OpenAIService(BaseLLMService):
    """OpenAI LLM服务类
    
    封装OpenAI兼容API的调用，包括：
    1. 聊天生成（ChatCompletion）
    2. 文本向量化（Embedding）
    
    Attributes:
        chat_model: ChatOpenAI实例，用于聊天生成
        embedding_model: OpenAIEmbeddings实例，用于文本向量化
    """
    
    def __init__(self) -> None:
        """初始化OpenAI服务
        
        从配置中读取API密钥、基础URL、模型名称等，创建聊天和embedding模型实例。
        """
        settings = get_settings()
        self.chat_model = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7,  # 温度参数，控制输出的随机性
        )
        self.embedding_model = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    def invoke(self, prompt: str) -> str:
        """调用OpenAI聊天模型生成回复
        
        Args:
            prompt: 提示词文本
            
        Returns:
            str: AI生成的回复文本
            
        Raises:
            LLMInvokeException: API调用失败时抛出
        """
        try:
            return self.chat_model.invoke(prompt).content
        except Exception as exc:
            raise LLMInvokeException(str(exc)) from exc
    
    def get_llm(self):
        """获取底层ChatOpenAI实例
        
        用于绑定工具等高级功能。
        
        Returns:
            ChatOpenAI: LangChain的ChatOpenAI对象实例
        """
        return self.chat_model

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
            return self.embedding_model.embed_query(text)
        except Exception as exc:
            raise LLMInvokeException(str(exc)) from exc
