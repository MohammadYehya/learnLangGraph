from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langchain_openai import ChatOpenAI
from typing import TypedDict, Literal
from dotenv import load_dotenv
load_dotenv()

class State(TypedDict):
    topic: str
    joke: str

def generateJoke(state: State) -> Command[Literal["generateJoke"]]:
    res = ChatOpenAI().invoke(f"Write a joke on the topic {state['topic']}.").content
    approved = interrupt({'revise_joke': res})
    # The interrupt function allows a halt in the execution of the program for human feedback
    # The next time the invoke function is called, the execution resumes from here
    return Command(update={'joke':res}, goto= END if approved == "Approve" else "generateJoke")

graph = (
    StateGraph(State)
    .add_node(generateJoke)
    .add_edge(START, "generateJoke")
    .compile(checkpointer=InMemorySaver())
)
config = {"configurable": {"thread_id": 1}}
print(graph.invoke({"topic": "Space"}, config=config))
# To resume an interupted flow, we use the Command function
print(graph.invoke(Command(resume="Reject"), config=config))
print(graph.invoke(Command(resume="Reject"), config=config))
print(graph.invoke(Command(resume="Approve"), config=config))

# This is one of the famous patterns of using HITL; Approve or Reject.

# It is also possible to resume a flow with two interrupts (parallel workflows with interrupts in each node in the super step) by creating a resume_map with the key of the interrupts id
# resume_map = {
#     i.id: f"edited text for {i.value['revisionVariable']}"
#     for i in graph.get_state(config).interrupts
# }
# print(graph.invoke(Command(resume=resume_map), config=config))