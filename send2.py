import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.types import Send
from langgraph.graph import StateGraph, START


class State(TypedDict):
    first_numbers: list[int]
    calced_numbers: Annotated[list[int], operator.add]
    total: int


def start(state: State):
    return {"total": 0, "first_numbers": [1, 2, 3, 4, 5]}


def continue_to_calc(state: State):
    return [Send("calc", num) for num in state["first_numbers"]]


def calc(number: int):
    return {"calced_numbers": [number * 100]}


def calc_total(state: State):
    return {"total": sum(state["calced_numbers"])}


graph = StateGraph(State)
graph.add_node("start", start)
graph.add_node("calc", calc)
graph.add_node("calc_total", calc_total)
graph.add_edge(START, "start")
graph.add_conditional_edges("start", continue_to_calc, ["calc"])
graph.add_edge("calc", "calc_total")

app = graph.compile()
app.get_graph().draw_mermaid_png(output_file_path="workflow.png")

state = State({"first_numbers": [], "calced_numbers": [], "total": 0})
result = app.invoke(state)
print(result["total"])
