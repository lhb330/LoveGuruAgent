from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from common.exceptions import LLMInvokeException
from config.settings import get_settings
from services.llm.base_llm import BaseLLMService


class OpenAIService(BaseLLMService):
    def __init__(self) -> None:
        settings = get_settings()
        self.chat_model = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7,
        )
        self.embedding_model = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    def invoke(self, prompt: str) -> str:
        try:
            return self.chat_model.invoke(prompt).content
        except Exception as exc:
            raise LLMInvokeException(str(exc)) from exc

    def embed_text(self, text: str) -> list[float]:
        try:
            return self.embedding_model.embed_query(text)
        except Exception as exc:
            raise LLMInvokeException(str(exc)) from exc
