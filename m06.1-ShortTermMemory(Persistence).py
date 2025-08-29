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
    return {"poem": ChatOpenAI(model="gpt-4o").invoke(f"Write a short poem about the topic: {state['topic']}")}

graph = (
    StateGraph(State)
    .add_node(generatePoem)
    .add_edge(START, "generatePoem")
    .add_edge("generatePoem", END)
    .compile(checkpointer=InMemorySaver())
)
# LangGraph makes a checkpoint after every superstep, so we are passing an InMemorySaver to store the state vales at each checkpoint in our memory

# When using a checkpointer, it is necessary to pass a config object
config = {"configurable": {"thread_id": 1}}

print(graph.invoke({"topic": "Agentic AI"}, config=config), end='\n\n')
print(graph.get_state(config=config), end='\n\n')
print(list(graph.get_state_history(config=config)), end='\n\n')

# Checkpointers are also used to implement a lot of other things like the following
# Fault Tolerance:
#   Let's say while executing a node, the program crashed. We can resume the program by doing this
#   graph.invoke(None, config=config)
#   Here, None, replaces the initial state, hinting at resuming the previous execution
# Human-in-the-loop:
#   We will take a look at this in the next module
# Time Travel:
#   We can pick which node we want to start re-executing the workflow
#   Each StateSnapshot has a checkpoint_id which we can find from the state history
#   graph.invoke(None, config= {"configurable": {"thread_id":1, "checkpoint_id":checkpoint_id}})