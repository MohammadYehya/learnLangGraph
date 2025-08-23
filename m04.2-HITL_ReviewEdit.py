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
    edit = interrupt({
        "task": "Review the output from the LLM and make any necessary edits.",
        "llm_generated_summary": res
    })
    return Command(update={'joke': edit['edited_text']}, goto= END)
    # We can use objects sent from the Command function's resume parameter

graph = (
    StateGraph(State)
    .add_node(generateJoke)
    .add_edge(START, "generateJoke")
    .compile(checkpointer=InMemorySaver())
)
config = {"configurable": {"thread_id": 1}}
print(graph.invoke({"topic": "Space"}, config=config))
print(graph.invoke(Command(resume={"edited_text": "THIS IS FUNNY JOKE!"}), config=config))

# This is one of the famous patterns of using HITL; Review & Edit.