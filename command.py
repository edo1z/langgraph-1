from langgraph.types import Command
from langgraph.graph import StateGraph
from typing import TypedDict


class State(TypedDict):
    num: int


def a(state: State):
    print("a", state)
    return Command(goto="b", update={"num": 100})


def b(state: State):
    print("b", state)
    return {"num": 200}


builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)
builder.set_entry_point("a")

graph = builder.compile()
graph.get_graph().draw_mermaid_png(output_file_path="workflow.png")

print(graph.invoke({"num": 1}))
