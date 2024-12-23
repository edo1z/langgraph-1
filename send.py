import operator
from typing import Annotated
from typing_extensions import TypedDict

from langchain_anthropic import ChatAnthropic

from langgraph.types import Send
from langgraph.graph import END, StateGraph, START

from pydantic import BaseModel, Field

# モデルとプロンプト
# 使用するモデルとプロンプトを定義
subjects_prompt = (
    """以下のトピックに関連する2〜5個の例をカンマ区切りで生成してください: {topic}"""
)
joke_prompt = """{subject}に関するジョークを生成してください"""
best_joke_prompt = """以下は{topic}に関するジョークの一覧です。最高のものを選んでください！最高のジョークのIDを返してください。

{jokes}"""


class Subjects(BaseModel):
    subjects: list[str]


class Joke(BaseModel):
    joke: str


class BestJoke(BaseModel):
    id: int = Field(description="最高のジョークのインデックス（0から開始）", ge=0)


model = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# グラフコンポーネント: グラフを構成するコンポーネントを定義


# これはメイングラフの全体的な状態です。
# トピック（ユーザーから提供されることを想定）を含み、
# その後、サブジェクトのリストを生成し、
# 各サブジェクトに対してジョークを生成します
class OverallState(TypedDict):
    topic: str
    subjects: list
    # ここでoperator.addを使用していることに注意
    # これは個々のノードから生成された全てのジョークを
    # 1つのリストに結合したいためです - これが本質的に
    # "reduce"の部分となります
    jokes: Annotated[list, operator.add]
    best_selected_joke: str


# これは全てのサブジェクトに対して"map"する
# ノードの状態となります（ジョークを生成するため）
class JokeState(TypedDict):
    subject: str


# これはジョークのサブジェクトを生成するために使用する関数です
def generate_topics(state: OverallState):
    prompt = subjects_prompt.format(topic=state["topic"])
    response = model.with_structured_output(Subjects).invoke(prompt)
    return {"subjects": response.subjects}


# ここでは、与えられたサブジェクトに対してジョークを生成します
def generate_joke(state: JokeState):
    prompt = joke_prompt.format(subject=state["subject"])
    response = model.with_structured_output(Joke).invoke(prompt)
    return {"jokes": [response.joke]}


# ここでは生成されたサブジェクトに対してマップする論理を定義します
# これはグラフのエッジとして使用します
def continue_to_jokes(state: OverallState):
    # Sendオブジェクトのリストを返します
    # 各Sendオブジェクトはグラフ内のノードの名前と
    # そのノードに送信する状態で構成されます
    return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]


# ここで最高のジョークを判定します
def best_joke(state: OverallState):
    jokes = "\n\n".join(state["jokes"])
    prompt = best_joke_prompt.format(topic=state["topic"], jokes=jokes)
    response = model.with_structured_output(BestJoke).invoke(prompt)
    return {"best_selected_joke": state["jokes"][response.id]}


# グラフの構築: ここで全てを組み合わせてグラフを構築します
graph = StateGraph(OverallState)
graph.add_node("generate_topics", generate_topics)
graph.add_node("generate_joke", generate_joke)
graph.add_node("best_joke", best_joke)
graph.add_edge(START, "generate_topics")
graph.add_conditional_edges("generate_topics", continue_to_jokes, ["generate_joke"])
graph.add_edge("generate_joke", "best_joke")
graph.add_edge("best_joke", END)
app = graph.compile()
