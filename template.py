import pprint
from langchain_core.prompts import ChatPromptTemplate

template = ChatPromptTemplate(
    [
        ("system", "あなたは天才ボット{name}です。"),
        ("ai", "どうされましたか？"),
        ("human", "{messages}"),
    ]
)
prompt_value = template.invoke({"name": "正義", "messages": "今日の天気は？"})
pprint.pp(prompt_value.messages)

print("--------------------------------")

template2 = ChatPromptTemplate.from_messages(
    [
        ("system", "あなたは天才ボット{name}です。"),
        ("placeholder", "{messages}"),
    ]
)

prompt_value2 = template2.invoke(
    {
        "name": "太郎",
        "messages": [
            ("human", "こんにちは！"),
            ("ai", "どうもこんにちは！誰ですか？"),
            ("human", "私は次郎です！！"),
        ],
    }
)
pprint.pp(prompt_value2.messages)

print("--------------------------------")

template3 = ChatPromptTemplate.from_messages(
    [
        ("system", "You are super AI {name}."),
        "{messages}",
    ]
)

prompt_value3 = template3.invoke(
    {
        "name": "Alice",
        "messages": [
            ("human", "Hello!!"),
            ("ai", "Who are you??"),
            ("human", "I am Bob!!"),
        ],
    }
)
pprint.pp(prompt_value3.messages)
