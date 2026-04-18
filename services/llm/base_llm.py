from abc import ABC, abstractmethod


class BaseLLMService(ABC):
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError
