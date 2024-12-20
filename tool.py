from langchain_core.tools import tool


@tool
def today_weather(place: str) -> str:
    """今日の天気予報を返します"""
    return "晴れ"


@tool
def today_fortune(seiza: str) -> str:
    """今日の運勢を返します"""
    return "大吉"


print(today_weather.name)
print(today_weather.invoke({"place": "東京"}))
print(today_fortune.invoke({"seiza": "牡羊座"}))
