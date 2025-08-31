from time import sleep
from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.types import Command
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv(override=True)

class Schema(BaseModel):
    next_agent: Literal["Scout", "Writer", f"{END}"]
    content: str
supervisor_model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash").with_structured_output(Schema)
worker_model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash")

def Supervisor(state: MessagesState) -> Command[Literal["Scout", "Writer", f"{END}"]]:
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
You are the Supervisor. Your job is to assign work to the two worker agents.
Worker 1 (Scout) can gather the necessary information.
Worker 2 (Writer) can create a polished final response by using the output of the first worker. 
DONT MODIFY THE OUTPUT FROM WORKER 1.
Then decide when the task is complete and you can send the final response to the user.
"""),
        MessagesPlaceholder(variable_name="messages")
    ])
    response = (prompt | supervisor_model).invoke({'messages': state["messages"]})
    return Command(
        goto=response.next_agent,
        update={"messages": [AIMessage(content = response.content)]},
    )

def Scout(state: MessagesState) -> Command[Literal["Supervisor"]]:
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
You are the Researcher. Your job is to collect key facts and details relevant to the user's request.
Do not write long answers or polished text—just provide structured notes, bullet points, or facts that Worker 2 can use. Be accurate and concise.
"""),
        MessagesPlaceholder(variable_name="messages")
    ])
    response = (prompt | worker_model).invoke({'messages': state["messages"]})
    return Command(
        goto="Supervisor",
        update={"messages": [AIMessage(content = response.content)]},
    )

def Writer(state: MessagesState) -> Command[Literal["Supervisor"]]:
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
You are the Writer. Your job is to take the notes from Worker 1 (Researcher) and turn them into a clear, well-written response for the user.
Use a natural, user-friendly tone. Do not add new facts that were not in Worker 1's notes—focus on clarity and readability.
"""),
        MessagesPlaceholder(variable_name="messages")
    ])
    response = (prompt | worker_model).invoke({'messages': state["messages"]})
    return Command(
        goto="Supervisor",
        update={"messages": [AIMessage(content = response.content)]},
    )

graph = (
    StateGraph(MessagesState)
    .add_node(Supervisor, defer=True)
    .add_node(Scout, defer=True)
    .add_node(Writer, defer=True)
    .add_edge(START, "Supervisor")
    .compile(checkpointer=InMemorySaver())
)

CONFIG = {'configurable':{'thread_id':1}}
for message in graph.stream({"messages":[HumanMessage(content="Write a generalized email to a boss asking for a day off tomorrow.")]}, config=CONFIG, stream_mode="updates"):
    for node, updates in message.items():
            print(f"Update from node: {node}")
            if "messages" in updates:
                updates["messages"][-1].pretty_print()
            else:
                print(updates)
            print("\n")