from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import AIMessage


@tool
def weather_search(city: str):
    """Search for the weather"""
    print("----")
    print(f"Searching for: {city}")
    print("----")
    return "Sunny!"


model = ChatAnthropic(model_name="claude-3-5-sonnet-latest").bind_tools(
    [weather_search]
)


def call_llm(state):
    return {"messages": [model.invoke(state["messages"])]}


def human_review_node(state) -> Command[Literal["call_llm", "run_tool"]]:
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[-1]

    # this is the value we'll be providing via Command(resume=<human_review>)
    human_review = interrupt(
        {
            "question": "Is this correct?",
            # Surface tool calls for review
            "tool_call": tool_call,
        }
    )

    review_action = human_review["action"]
    review_data = human_review.get("data")

    # if approved, call the tool
    if review_action == "continue":
        return Command(goto="run_tool")

    # update the AI message AND call tools
    elif review_action == "update":
        updated_message = {
            "role": "ai",
            "content": last_message.content,
            "tool_calls": [
                {
                    "id": tool_call["id"],
                    "name": tool_call["name"],
                    # This the update provided by the human
                    "args": review_data,
                }
            ],
            # This is important - this needs to be the same as the message you replacing!
            # Otherwise, it will show up as a separate message
            "id": last_message.id,
        }
        return Command(goto="run_tool", update={"messages": [updated_message]})

    # provide feedback to LLM
    elif review_action == "feedback":
        # NOTE: we're adding feedback message as a ToolMessage
        # to preserve the correct order in the message history
        # (AI messages with tool calls need to be followed by tool call messages)
        tool_message = {
            "role": "tool",
            # This is our natural language feedback
            "content": review_data,
            "name": tool_call["name"],
            "tool_call_id": tool_call["id"],
        }
        return Command(goto="call_llm", update={"messages": [tool_message]})


def run_tool(state):
    new_messages = []
    tools = {"weather_search": weather_search}
    tool_calls = state["messages"][-1].tool_calls
    for tool_call in tool_calls:
        tool = tools[tool_call["name"]]
        result = tool.invoke(tool_call["args"])
        new_messages.append(
            {
                "role": "tool",
                "name": tool_call["name"],
                "content": result,
                "tool_call_id": tool_call["id"],
            }
        )
    return {"messages": new_messages}


def route_after_llm(state) -> Literal[END, "human_review_node"]:
    if len(state["messages"][-1].tool_calls) == 0:
        return END
    else:
        return "human_review_node"


builder = StateGraph(MessagesState)
builder.add_node(call_llm)
builder.add_node(run_tool)
builder.add_node(human_review_node)
builder.add_edge(START, "call_llm")
builder.add_conditional_edges("call_llm", route_after_llm)
builder.add_edge("run_tool", "call_llm")

# Set up memory
memory = MemorySaver()

# Add
graph = builder.compile(checkpointer=memory)

# View
graph.get_graph().draw_mermaid_png(output_file_path="workflow.png")

if __name__ == "__main__":
    print("🤖 チャットボットを起動しました！")
    print("終了するには 'quit' または 'exit' または 'q' を入力してください。")

    while True:
        try:
            # ユーザー入力を受け付ける
            user_input = input("\nUser: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break

            # 初期入力
            initial_input = {"messages": [{"role": "user", "content": user_input}]}

            # スレッドID設定
            thread = {"configurable": {"thread_id": "2"}}

            # グラフ実行
            for event in graph.stream(initial_input, thread, stream_mode="updates"):
                print(event)
                print("\n")
                if "__interrupt__" in event:  # 人間の確認が必要な時点
                    # 承認を求める
                    choice = input("\n👉 ツールを実行しますか？ (Y/N): ")

                    if choice.upper() == "Y":
                        # 承認して実行
                        print("=== ツール使用を承認して実行 ===")
                        for response in graph.stream(
                            Command(resume={"action": "continue"}),
                            thread,
                            stream_mode="updates",
                        ):
                            print(response)
                            print("\n")
                    else:
                        # キャンセル
                        print("=== ツール使用をキャンセル ===")
                        for response in graph.stream(
                            Command(
                                resume={
                                    "action": "feedback",
                                    "data": "ツールの使用をキャンセルしました",
                                }
                            ),
                            thread,
                            stream_mode="updates",
                        ):
                            print(response)
                            print("\n")

        except Exception as e:
            print(f"❌ Error: {e}")
            break
