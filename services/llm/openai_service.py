"""OpenAI LLM服务实现

提供OpenAI兼容接口的聊天和embedding功能。
支持所有OpenAI兼容的API服务（如OpenAI本身、Azure OpenAI、本地部署等）。
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import openai

from common.exceptions import LLMInvokeException
from config.settings import get_settings
from services.llm.base_llm import BaseLLMService


# class OpenAIService(BaseLLMService):
#     """OpenAI LLM服务类
#
#     封装OpenAI兼容API的调用，包括：
#     1. 聊天生成（ChatCompletion）
#     2. 文本向量化（Embedding）
#
#     Attributes:
#         chat_model: ChatOpenAI实例，用于聊天生成
#         embedding_model: OpenAIEmbeddings实例，用于文本向量化
#     """
#
#     def __init__(self) -> None:
#         """初始化OpenAI服务
#
#         从配置中读取API密钥、基础URL、模型名称等，创建聊天和embedding模型实例。
#         """
#         settings = get_settings()
#         self.chat_model = ChatOpenAI(
#             model=settings.openai_model,
#             api_key=settings.openai_api_key,
#             base_url=settings.openai_base_url,
#             temperature=0.7,  # 温度参数，控制输出的随机性
#         )
#         self.embedding_model = OpenAIEmbeddings(
#             model=settings.openai_embedding_model,
#             api_key=settings.openai_api_key,
#             base_url=settings.openai_base_url,
#             # 【关键修复】强制让阿里接口接收字符串，不发送token数组
#             default_headers={"Accept": "application/json"},
#             # 【关键修复】禁用分词，直接传文本给阿里
#             embedding_ctx_length=8191,
#             chunk_size=1000,
#         )
#
#     def invoke(self, prompt: str) -> str:
#         """调用OpenAI聊天模型生成回复
#
#         Args:
#             prompt: 提示词文本
#
#         Returns:
#             str: AI生成的回复文本
#
#         Raises:
#             LLMInvokeException: API调用失败时抛出
#         """
#         try:
#             return self.chat_model.invoke(prompt).content
#         except Exception as exc:
#             raise LLMInvokeException(str(exc)) from exc
#
#     def get_llm(self):
#         """获取底层ChatOpenAI实例
#
#         用于绑定工具等高级功能。
#
#         Returns:
#             ChatOpenAI: LangChain的ChatOpenAI对象实例
#         """
#         return self.chat_model
#
#     def embed_text(self, text: str) -> list[float]:
#         """将文本转换为向量
#
#         Args:
#             text: 要转换的文本
#
#         Returns:
#             list[float]: 浮点数向量，维度取决于embedding模型
#
#         Raises:
#             LLMInvokeException: API调用失败时抛出
#         """
#         try:
#             return self.embedding_model.embed_query(text)
#         except Exception as exc:
#             raise LLMInvokeException(str(exc)) from exc



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
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7,
        )
        # 初始化，但我们自己重写调用逻辑
        self.embedding_model = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
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
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_base_url,
            )
            response = client.embeddings.create(
                model=self.settings.openai_embedding_model,
                input=text,  # 只传字符串，阿里最爱！
            )
            return response.data[0].embedding
        except Exception as exc:
            raise LLMInvokeException(str(exc)) from exc