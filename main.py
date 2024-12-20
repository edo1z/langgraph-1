from confirm import create_agent
from langchain_core.messages import HumanMessage
from langgraph.types import Command

graph = create_agent()

def stream_graph_updates(user_input: str):
    config = {"configurable": {"thread_id": "123"}}
    messages = [HumanMessage(content=user_input)]

    for chunk in graph.stream({"messages": messages}, config):
        if "__interrupt__" in chunk:
            print("\n=== 天気確認の実行確認 ===")
            print("1: 実行")
            print("2: パラメータを編集")
            print("3: キャンセル")

            choice = input("\n👉 選択してください (1-3): ")

            if choice == "1":
                # そのまま実行
                action = "continue"
                data = None
            elif choice == "2":
                # パラメータを編集
                place = input("👉 場所を入力してください: ")
                action = "update"
                data = {"place": place}
            else:
                # キャンセル
                action = "cancel"
                data = None

            # グラフを再開
            for response in graph.stream(
                Command(resume={"action": action, "data": data}),
                config
            ):
                if "messages" in response.get("chatbot", {}):
                    message = response["chatbot"]["messages"][-1]
                    print("Assistant:", message.content)
        else:
            if "messages" in chunk.get("chatbot", {}):
                message = chunk["chatbot"]["messages"][-1]
                print("Assistant:", message.content)

if __name__ == "__main__":
    print("🤖 チャットボットを起動しました！")
    print("終了するには 'quit' または 'exit' または 'q' を入力してください。")

    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break
            stream_graph_updates(user_input)
        except Exception as e:
            print(f"❌ Error: {e}")
            break
