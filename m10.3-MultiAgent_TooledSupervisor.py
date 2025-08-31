from typing import Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.prebuilt import InjectedState, create_react_agent
from dotenv import load_dotenv
load_dotenv(override=True)

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# This is the agent function that will be called as tool
# Notice that you can pass the state to the tool via InjectedState annotation
def Scout(state: Annotated[list[BaseMessage], InjectedState]):
    """
    You are the Researcher. Your job is to collect key facts and details relevant to the user's request.
    Do not write long answers or polished text—just provide structured notes, bullet points, or facts that Worker 2 can use. Be accurate and concise.
    """
    response = model.invoke({'messages': state["messages"]})
    return response.content

def Writer(state: Annotated[list[BaseMessage], InjectedState]):
    """
    You are the Researcher. Your job is to collect key facts and details relevant to the user's request.
    Do not write long answers or polished text—just provide structured notes, bullet points, or facts that Worker 2 can use. Be accurate and concise.
    """
    response = model.invoke({'messages': state["messages"]})
    return response.content

tools = [Scout, Writer]
# The simplest way to build a supervisor w/ tool-calling is to use prebuilt ReAct agent graph that consists of a tool-calling LLM node (i.e. supervisor) and a tool-executing node
supervisor = create_react_agent(model, tools)

CONFIG = {'configurable':{'thread_id':1}}
for message in supervisor.stream({"messages":[HumanMessage(content="Write a generalized email to a boss asking for a day off tomorrow.")]}, config=CONFIG, stream_mode="updates"):
    for node, updates in message.items():
            print(f"Update from node: {node}")
            if "messages" in updates:
                updates["messages"][-1].pretty_print()
            else:
                print(updates)
            print("\n")