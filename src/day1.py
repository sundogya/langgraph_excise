import os

# 强制让 Python 的网络请求（httpx/requests等）跳过本地代理
os.environ["no_proxy"] = "localhost,127.0.0.1,::1"
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"

# 如果你发现加上面还不行，可以顺便把全局的 http_proxy 临时清空（仅在当前 Python 进程生效）
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

import operator
from typing import Annotated, Literal, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langchain_ollama import ChatOllama


# 1. 定义外部工具
@tool
def calculate(expression: str) -> str:
    """计算数学表达式的值。
    
    【极其重要的规则（违反会导致计算严重错误）】
    1. 【流水线整体性原则】：如果用户的自然语言中包含“然后（then）”这一类的连词，说明前面的所有运算是一个【绝对的整体】，在编写表达式时，最外层必须用一对大括号或括号将前面的全部包起来再去做“然后”的运算。
       - 错误示范：(A + B) * C + D / E / F  （这样 F 只除到了 E，大包围失效）
       - 正确示范：((A + B) * C + D / E) / F （必须用最外层括号框住前面所有人）
    2. 【括号严格对齐】：所有出现的左括号 `(` 必须有对应的右括号 `)` 闭合，严禁出现 unmatched 语法错误。
    3. 如果句子极其复杂，严禁擅自胡乱嵌套括号（如 `/(9/32)` 这种行为），必须保证数学层级的纯粹性。
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算出错: {str(e)}"


tools = [calculate]
tools_by_name = {tool.name: tool for tool in tools}

# 2. 定义图的状态 (State)
# 使用 Annotated 和 operator.add 确保消息列表是“追加”而不是“覆盖”
class State(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]

# 初始化本地 Ollama 运行的 llama3.1 (前提是你已经在本地终端执行过: ollama run llama3.1)
model = ChatOllama(
    model="llama3.1:8b",
    temperature=0,
    # 可选：如果你需要更强的本地调试输出，可以加 format="json" 或其他参数
).bind_tools(tools)


# 4. 定义节点：大模型推理节点
def call_model(state: State):
    print("--- 🤖 正在调用大模型推理 ---")
    messages = state["messages"]
    system_prompt = SystemMessage(content="""
    你是一个严谨的数学计算助手。
    当用户请求进行复杂的数学运算时：
    1. 必须使用 `calculate` 工具。
    2. 翻译数学表达式时，必须仔细揣摩用户的运算先后顺序，严格使用括号 `()` 来控制优先级，绝不能把顺序搞错！
    3. 数学表达式很长的时候，你需要使用括号 `()`来进行多次运算拆解，多次调用`calculate`工具，确保每次计算的优先级正确。
    """)
    response = model.invoke([system_prompt] + messages)
    # 返回一个字典，键必须与 State 定义一致。这里会通过 operator.add 自动追加到 messages 列表
    return {"messages": [response]}


# 5. 定义节点：工具执行节点
def call_tools(state: State):
    print("--- 🛠️ 正在执行外部工具 ---")
    messages = state["messages"]
    last_message = messages[-1]
    
    # 解析大模型要求调用的工具和参数
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        print(f"执行工具: {tool_name}, 参数: {tool_args}")
        
        selected_tool = tools_by_name[tool_name]
        tool_result = selected_tool.invoke(tool_args)
        
        tool_messages.append(
            ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"]
            )
        )
    return {"messages": tool_messages}


# 6. 定义条件路由边：判断大模型是否需要调用工具
def should_continue(state: State) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    # 如果大模型发起了 tool_calls，说明需要走工具节点
    if last_message.tool_calls:
        return "tools"
    # 否则流程结束
    return "__end__"


# 7. 构建状态图 (Workflow)
workflow = StateGraph(State)

# 添加节点
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)

# 设置入口
workflow.add_edge(START, "agent")

# 添加条件边：从 agent 节点出发，根据 should_continue 的返回值决定去哪里
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "__end__": END
    }
)

# 工具执行完后，必须无条件流转回 agent，让大模型根据工具返回结果继续回答
workflow.add_edge("tools", "agent")

# 编译成可执行的 App
app = workflow.compile()


# 8. 运行测试
if __name__ == "__main__":
    # query = "请帮我计算一下 (1024 * 512) / 32 等于多少？"
    query = "请帮我计算一下1024加上512乘以48加上45除以9然后除以32等于多少？"
    print(f"用户输入: {query}\n")
    
    initial_state = {"messages": [HumanMessage(content=query)]}
    
    # 运行图
    for step in app.stream(initial_state, stream_mode="values"):
        latest_msg = step["messages"][-1]
        print(f"[{latest_msg.__class__.__name__}]: {latest_msg.content}")
        
        # 修复：加上 hasattr 检查，避免 HumanMessage 报错
        if hasattr(latest_msg, "tool_calls") and latest_msg.tool_calls:
            print(f"-> 触发工具调用请求: {latest_msg.tool_calls}")
            
        print("-" * 40)