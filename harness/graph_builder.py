from typing import TypedDict

from langgraph.graph import END, StateGraph

from harness.chain_builder import ChatChainBuilder


class ChatState(TypedDict, total=False):
    conversation_id: str
    user_message: str
    assistant_reply: str
    references: list[dict]


def build_chat_graph():
    builder = StateGraph(ChatState)
    chain = ChatChainBuilder()

    def generate_reply(state: ChatState) -> ChatState:
        answer, references = chain.run(state["user_message"])
        return {
            "assistant_reply": answer,
            "references": references,
        }

    builder.add_node("generate_reply", generate_reply)
    builder.set_entry_point("generate_reply")
    builder.add_edge("generate_reply", END)
    return builder.compile()
