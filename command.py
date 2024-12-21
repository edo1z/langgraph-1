from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from typing import TypedDict


class State(TypedDict):
    num: int


def a(state: State):
    number = interrupt("please input number: ")
    return Command(goto="b", update={"num": number})


def b(state: State):
    return {"num": state["num"] * 2}


builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)
builder.set_entry_point("a")

graph = builder.compile(checkpointer=MemorySaver())
graph.get_graph().draw_mermaid_png(output_file_path="workflow.png")


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "1"}}
    result = None
    for event in graph.stream({"num": 0}, config=config):
        if "__interrupt__" in event:
            user_input = input(event["__interrupt__"][0].value)
            result = graph.invoke(Command(resume=int(user_input)), config=config)
    print(result)
