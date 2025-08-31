from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
import requests
from dotenv import load_dotenv
load_dotenv(override=True)

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

# Defining tools is the same as in LangChain
@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}
    
@tool
def get_user_data(url: str) -> dict:
    """
    Fetch a users info from a Github URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}

tools = [calculator, get_user_data]
llm_with_tools = llm.bind_tools(tools)

def chat_node(state: MessagesState):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

graph = (
    StateGraph(MessagesState)
    .add_node("chat_node", chat_node)
    .add_node("tools", ToolNode(tools))     # When using Tools in Agentic Workflows, we use the ToolNode which is a prebuilt Node that bundles all the tools in one Node.
    .add_edge(START, "chat_node")
    .add_conditional_edges("chat_node", tools_condition)
    .add_edge('tools', 'chat_node')
    .compile(checkpointer=InMemorySaver())
)

CONFIG={'configurable': {'thread_id': 1}}
query = "Could you get all the users data from https://api.github.com/users/MohammadYehya and ouput it. Also, what is 15123747 multiplied by 31231?"
for message in graph.stream({"messages": [HumanMessage(content=query)]}, config=CONFIG, stream_mode="updates"):
    for node, updates in message.items():
        print(f"Update from node: {node}")
        if "messages" in updates:
            updates["messages"][-1].pretty_print()
        else:
            print(updates)
        print("\n")