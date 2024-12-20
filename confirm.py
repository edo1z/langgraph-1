from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import os

load_dotenv()


@tool
def today_weather(place: str) -> str:
    """今日の天気予報を返します"""
    return "晴れ"


tool_list = [today_weather]
llm = ChatAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"), model="claude-3-5-sonnet-20240620"
).bind_tools(tool_list)


# State型の定義を追加
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ツールの実行前に割り込み
def interrupt_before_tools():
    user_input = input("天気を取得しますか？ (y/n): ")
    if user_input.strip().lower() == "y":
        return True
    else:
        print("終了します。")
        exit()


# チャットボット関数の追加
def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# グラフの設定を修正
builder = StateGraph(State)  # dictではなくState型を使用

# ノードの設定を修正
builder.add_node("assistant", chatbot)  # llmではなくchatbot関数を使用
builder.add_node("tools", ToolNode(tools=tool_list))

# エントリーポイントの設定
builder.set_entry_point("assistant")

# 他の設定はそのまま
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")

# グラフの実行
state = {"messages": [HumanMessage(content="今日の天気は？")]}
graph = builder.compile(
    interrupt_before=["tools"],
)
result = graph.invoke(state)
print(result)
