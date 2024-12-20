from typing import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command

# シンプルな状態管理用のクラス
class State(TypedDict):
    message: str

# 人間の確認を求めるノード
def human_check(state: State):
    value = interrupt({
        "question": "この内容でよいですか？",
        "current_message": state["message"]
    })
    return {"message": value}

# グラフの構築
graph = (
    StateGraph(State)
    .add_node("human_check", human_check)
    .add_edge(START, "human_check")
    .compile(checkpointer=MemorySaver())
)

# 実行例
if __name__ == "__main__":
    # スレッドID設定
    config = {"configurable": {"thread_id": "test_1"}}

    # 初期実行
    print("=== 初期実行 ===")
    result = None
    for chunk in graph.stream({"message": "こんにちは！"}, config=config):
        print(chunk)
        if "__interrupt__" in chunk:
            # 人間からの入力を受け付ける
            user_input = input("\n👉 メッセージを編集してください: ")

            # 再開実行
            print("\n=== 再開実行 ===")
            for response in graph.stream(Command(resume=user_input), config=config):
                print(response)
