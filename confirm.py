from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
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
        print(f"🔍 {place}の天気を確認中...")
        return "晴れ"

    tool_list = [today_weather]
    llm = ChatAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"), model="claude-3-5-sonnet-20240620"
    ).bind_tools(tool_list)

    # チャットボット関数
    def chatbot(state: State):
        return {"messages": [llm.invoke(state["messages"])]}

    # ツール実行前の確認ノード
    def human_review(state: State) -> Command[Literal["chatbot", "tools"]]:
        last_message = state["messages"][-1]
        tool_call = last_message.tool_calls[-1]

        # 人間に確認を求める
        review = interrupt({
            "question": "天気確認の実行確認",
            "tool_call": tool_call,
            "options": ["実行", "編集", "キャンセル"]
        })

        action = review.get("action")
        data = review.get("data")

        if action == "continue":
            return Command(goto="tools")

        elif action == "update":
            updated_message = {
                "role": "ai",
                "content": last_message.content,
                "tool_calls": [{
                    "id": tool_call["id"],
                    "name": tool_call["name"],
                    "args": data,
                }],
                "id": last_message.id
            }
            return Command(goto="tools", update={"messages": [updated_message]})

        else:  # cancel
            # キャンセルをツールからのフィードバックとして処理
            tool_message = {
                "role": "tool",
                "content": "ユーザーが天気確認をキャンセルしました。",
                "name": tool_call["name"],
                "tool_call_id": tool_call["id"],
            }
            return Command(goto="chatbot", update={"messages": [tool_message]})

    def route_after_llm(state) -> Literal["human_review", END]:
        if len(state["messages"][-1].tool_calls) == 0:
            return END
        return "human_review"

    # グラフの設定
    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot)
    builder.add_node("tools", ToolNode(tools=tool_list))
    builder.add_node("human_review", human_review)
    builder.set_entry_point("chatbot")

    builder.add_conditional_edges("chatbot", route_after_llm)
    builder.add_edge("tools", "chatbot")
    builder.add_edge("human_review", "tools")

    return builder.compile(
        checkpointer=memory,
    )
