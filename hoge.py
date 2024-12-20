from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END


class State(TypedDict):
    total: int


def add_one(state: State):
    return {"total": state["total"] + 1}


def is_over_10(state: State):
    print("☆ " * state["total"])
    return state["total"] > 10


graph_builder = StateGraph(State)
graph_builder.add_node("add_one", add_one)
graph_builder.set_entry_point("add_one")
graph_builder.add_node("is_over_10", is_over_10)
graph_builder.add_conditional_edges(
    source="add_one",
    path=is_over_10,
    path_map={True: END, False: "add_one"},
)
graph = graph_builder.compile()
graph.get_graph().draw_mermaid_png(output_file_path="workflow.png")

graph.invoke({"total": 0})
