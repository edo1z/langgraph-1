from confirm import create_agent

graph = create_agent()


def stream_graph_updates(user_input: str):
    config = {"configurable": {"thread_id": "123"}}
    for event in graph.stream({"messages": ("user", user_input)}, config):
        for value in event.values():
            if isinstance(value, dict) and "messages" in value:
                message = value["messages"][-1]
                if hasattr(message, "content"):
                    print("Assistant:", message.content)
                else:
                    print("Assistant:", message)


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
