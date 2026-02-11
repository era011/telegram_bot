import os
from typing_extensions import TypedDict, Annotated

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, END
from const import COLLECTION_NAME
from connections.wv_client import get_weaviate_client
from langgraph1.prompts import SYSTEM_PROMPT

llm = ChatOpenAI(
    model="gpt-4.1",
    streaming=True,
    api_key=os.getenv("OPENAI_API_KEY"),
)

class State(TypedDict):
    messages: Annotated[list, add_messages]

client = get_weaviate_client()


@tool
def rag(query: str) -> list[dict]:
    """Ищет релевантные чанки в базе знаний Weaviate и возвращает топ результатов."""
    collection = client.collections.get(COLLECTION_NAME)
    res = collection.query.near_text(query=query, limit=15)

    out = []
    for obj in res.objects:
        out.append({
            "content": obj.properties.get("content", ""),
            "name": obj.properties.get("name", ""),
            "id_doc": obj.properties.get("id_doc", ""),
            "chunk_index": obj.properties.get("chunk_index", None),
            "source": obj.properties.get("source", ""),  # если есть
        })
    return out


llm_with_tools = llm.bind_tools([rag])


def assistant_node(state: State) -> dict:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
    resp = llm_with_tools.invoke(msgs)  # вернёт AIMessage (возможен tool call)
    return {"messages": [resp]}


tool_node = ToolNode([rag])

builder = StateGraph(State)
builder.add_node("assistant", assistant_node)
builder.add_node("tools", tool_node)

builder.set_entry_point("assistant")

builder.add_conditional_edges(
    "assistant",
    tools_condition,
    {
        "tools": "tools",
        "__end__": END,
    },
)

builder.add_edge("tools", "assistant")

graph = builder.compile()
