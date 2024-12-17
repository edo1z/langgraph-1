from chatbot import create_chatbot

graph = create_chatbot()


def stream_graph_updates(user_input: str):
    print("stream_graph_updates start", user_input)
    for event in graph.stream({"messages": [("user", user_input)]}):
        print("event", event)
        for value in event.values():
            print("value", value)
            print("Assistant:", value["messages"][-1].content)


while True:
    print("start")
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break
