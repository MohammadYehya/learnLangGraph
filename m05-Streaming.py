from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from typing import TypedDict
from dotenv import load_dotenv
load_dotenv()

class State(TypedDict):
    topic: str
    poem: str

def generatePoem(state: State) -> State:
    return {"poem": ChatOpenAI(model="gpt-4o").invoke(f"Write a huge poem about the topic: {state['topic']}").content}

graph = (
    StateGraph(State)
    .add_node(generatePoem)
    .add_edge(START, "generatePoem")
    .add_edge("generatePoem", END)
    .compile(checkpointer=InMemorySaver())
)

config = {"configurable": {"thread_id": 1}}
# .stream basically returns a generator function, so we can use it in a for loop to pipe out all the incoming data
for message, metadata in graph.stream({"topic": "Agentic AI"}, config=config, stream_mode="messages"):
    print(message.content, end='')