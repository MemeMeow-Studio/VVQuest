from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from duckduckgo_search import DDGS

# 定义搜索工具
@tool
def get_web_data(query: str) -> str:
    """使用DuckDuckGo搜索引擎进行搜索"""
    results = DDGS().text(query, max_results=10)
    return results

# 初始化模型
api_key = "你的api_key"
base_url = "https://api.siliconflow.cn/v1"
model = init_chat_model("Qwen/Qwen2.5-72B-Instruct", model_provider="openai", api_key=api_key, base_url=base_url)

# 绑定工具
tools = [get_web_data]
llm_with_tools = model.bind_tools(tools)

# 用户查询
query = "mingupup是谁？"
messages = [HumanMessage(query)]

# 调用模型
ai_msg = llm_with_tools.invoke(messages)
print(ai_msg.tool_calls)

# 调用搜索工具
messages.append(ai_msg)
for tool_call in ai_msg.tool_calls:
    selected_tool = {"get_web_data": get_web_data}[tool_call["name"].lower()]
    tool_msg = selected_tool.invoke(tool_call)
    print(tool_msg)
    messages.append(tool_msg)

# 获取最终回答
print(llm_with_tools.invoke(messages).content)