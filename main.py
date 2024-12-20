from confirm import create_agent
from langchain_core.messages import HumanMessage, ToolMessage

graph = create_agent()

def stream_graph_updates(user_input: str):
    config = {"configurable": {"thread_id": "123"}}
    messages = [HumanMessage(content=user_input)]

    while True:
        # グラフを実行
        events = graph.stream({"messages": messages}, config)
        for event in events:
            for value in event.values():
                if isinstance(value, dict) and "messages" in value:
                    message = value["messages"][-1]
                    if hasattr(message, "content"):
                        print("Assistant:", message.content)
                    else:
                        print("Assistant:", message)

        # 状態をチェック
        snapshot = graph.get_state(config)
        if not snapshot.next:
            break

        # ツール実行の確認
        try:
            user_approval = input("天気を確認しますか？ (y/n): ")
            if user_approval.lower() == 'y':
                # ツールの実行を継続
                result = graph.invoke(None, config)
            else:
                # ツールの実行結果の形式を修正
                last_message = event["messages"][-1]
                tool_call_id = last_message.tool_calls[0]["id"]
                result = graph.invoke(
                    {
                        "messages": [
                            ToolMessage(
                                content="キャンセルされました",
                                tool_call_id=tool_call_id,
                                name="today_weather",  # ツール名を指定
                            )
                        ]
                    },
                    config,
                )
        except Exception as e:
            print(f"Error during tool execution: {e}")
            break

if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(user_input)
        except Exception as e:
            print(f"Error: {e}")
            break
