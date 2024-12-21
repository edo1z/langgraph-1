from dotenv import load_dotenv
from typing import Annotated, Literal
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.types import Command
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

load_dotenv()

tavily_tool = TavilySearchResults(api_key=os.getenv("TAVILY_API_KEY"), max_results=5)
repl = PythonREPL()


@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        if "plt." in code:
            # matplotlibを使用するコードの場合
            code_with_save = f"""
{code}
plt.savefig('chart.png')
plt.close()
"""
            result = repl.run(code_with_save)
        else:
            # 通常のコードの場合
            result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"


def make_system_prompt(suffix: str) -> str:
    return (
        "あなたは他のAIアシスタントと協力して作業を行う、優秀なAIアシスタントです。"
        " 与えられたツールを使用して、質問に対する回答を進めてください。"
        " データや情報が不十分な場合は、その旨を明確に伝え、必要な情報を具体的に示してください。"
        " 他のアシスタントと協力して作業を進める場合は、不足している情報や必要なデータを"
        " 明確に伝えてください。"
        " 最終的な成果物が完成し、必要な情報が全て揃っている場合のみ、"
        " 回答の先頭に「FINAL ANSWER」と付けてください。"
        " 不完全な状態では決して「FINAL ANSWER」は使用しないでください。"
        " また、基本的に全て日本語で回答してください（FINAL ANSWERは英語のまま）。"
        f"\n{suffix}"
    )


llm = ChatAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"), model="claude-3-5-sonnet-20240620"
)


def get_next_node(last_message: BaseMessage, goto: str):
    if "FINAL ANSWER" in last_message.content:
        # Any agent decided the work is done
        return END
    return goto


# Research agent and node
research_agent = create_react_agent(
    llm,
    tools=[tavily_tool],
    state_modifier=make_system_prompt(
        "あなたはデータ調査専門です。チャート作成の同僚と協力して作業します。"
    ),
)


def research_node(
    state: MessagesState,
) -> Command[Literal["chart_generator", END]]:
    result = research_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "chart_generator")
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="researcher"
    )
    return Command(
        update={
            # share internal message history of research agent with other agents
            "messages": result["messages"],
        },
        goto=goto,
    )


# Chart generator agent and node
# NOTE: THIS PERFORMS ARBITRARY CODE EXECUTION, WHICH CAN BE UNSAFE WHEN NOT SANDBOXED
chart_agent = create_react_agent(
    llm,
    [python_repl_tool],
    state_modifier=make_system_prompt(
        "あなたはチャート作成専門です。調査担当の同僚と協力して作業します。作成するチャートの文字列は全て英語で作成してください。"
    ),
)


def chart_node(state: MessagesState) -> Command[Literal["researcher", END]]:
    result = chart_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "researcher")
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="chart_generator"
    )
    return Command(
        update={
            # share internal message history of chart agent with other agents
            "messages": result["messages"],
        },
        goto=goto,
    )


workflow = StateGraph(MessagesState)
workflow.add_node("researcher", research_node)
workflow.add_node("chart_generator", chart_node)

workflow.add_edge(START, "researcher")
graph = workflow.compile()

graph.get_graph().draw_mermaid_png(output_file_path="workflow.png")

events = graph.stream(
    {
        "messages": [
            (
                "user",
                "まず、10年間のトヨタ、日産、ホンダの売上と最終利益を取得し、それらの折れ線グラフを作成してください。"
                "グラフが完成したら終了してください。",
            )
        ],
    },
    # Maximum number of steps to take in the graph
    {"recursion_limit": 150},
)
for s in events:
    print(s)
    print("----")
