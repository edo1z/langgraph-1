from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
import os

load_dotenv()


def create_agent():
    memory = MemorySaver()

    # State型の定義
    class State(TypedDict):
        messages: Annotated[list[BaseMessage], add_messages]

    # ツールの設定
    @tool
    def today_weather(place: str) -> str:
        """今日の天気予報を返します"""
        return "晴れ"

    tool_list = [today_weather]
    llm = ChatAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"), model="claude-3-5-sonnet-20240620"
    ).bind_tools(tool_list)

    # チャットボット関数
    def chatbot(state: State):
        return {"messages": [llm.invoke(state["messages"])]}

    # グラフの設定
    builder = StateGraph(State)
    builder.add_node("assistant", chatbot)
    builder.add_node("tools", ToolNode(tools=tool_list))
    builder.set_entry_point("assistant")

    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")

    return builder.compile(
        checkpointer=memory,
        interrupt_before=["tools"],
    )
