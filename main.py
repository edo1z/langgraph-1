from confirm import create_agent
from langchain_core.messages import HumanMessage

graph = create_agent()


def stream_graph_updates(user_input: str):
    print("update")
    messages = [HumanMessage(content=user_input)]
    for event in graph.stream({"messages": messages}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


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
