from harness.prompt_manager import PromptManager
from services.chat.rag_service import RAGService
from services.llm.factory import get_llm_service


class ChatChainBuilder:
    def __init__(self) -> None:
        self.rag_service = RAGService()
        self.llm_service = get_llm_service()

    def run(self, user_message: str) -> tuple[str, list[dict]]:
        references = self.rag_service.retrieve(user_message)
        prompt = PromptManager.build_chat_prompt(user_message, references)
        answer = self.llm_service.invoke(prompt)
        return answer, references
