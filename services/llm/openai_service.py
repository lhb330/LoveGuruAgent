from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import openai

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
        settings = get_settings()
        self.settings = settings
        # 聊天模型正常
        self.chat_model = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key.get_secret_value(),  # 修复：SecretStr 转字符串
            base_url=settings.openai_base_url,
            request_timeout=120,  # 超时时间加长
            max_retries=3,  # 自动重试
            temperature=0.7,
        )
        # 初始化，但我们自己重写调用逻辑
        self.embedding_model = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key.get_secret_value(),  # 修复：SecretStr 转字符串
            base_url=settings.openai_base_url,
            default_headers={"Accept": "application/json"},
        )

    def invoke(self, prompt: str) -> str:
        try:
            return self.chat_model.invoke(prompt).content
        except Exception as exc:
            raise LLMInvokeException(str(exc)) from exc

    def get_llm(self):
        return self.chat_model

    def embed_text(self, text: str) -> list[float]:
        """
        🔥 终极修复：直接调用原生 openai SDK，只传字符串，绝对不转 token！
        """
        try:
            # 直接原生调用，只传字符串！！！
            client = openai.OpenAI(
                api_key=self.settings.openai_api_key.get_secret_value(),  # 修复：SecretStr 转字符串
                base_url=self.settings.openai_base_url,
            )
            response = client.embeddings.create(
                model=self.settings.openai_embedding_model,
                input=text,  # 只传字符串，阿里最爱！
            )
            return response.data[0].embedding
        except Exception as exc:
            raise LLMInvokeException(str(exc)) from exc