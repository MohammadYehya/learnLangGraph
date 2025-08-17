from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, Command
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field
import operator
from dotenv import load_dotenv
load_dotenv()

class State(TypedDict):
    map: list[list[int]]
    reduce: list[int]
    value: Annotated[int, operator.add]

class MapSchema(BaseModel):
    map: list[list[int]] = Field(description="A 2D map of integers.")

# The Send command is mostly used during distributed tasks like Map-Reduce. It sends dynamic data to be processed parallely. Each parallel node has its own copy of the state.
def generateMap(state: State) -> State:
    llm = ChatOpenAI(model = "gpt-4o").with_structured_output(schema=MapSchema)
    result = llm.invoke("Generate a 2D map of integers.")
    return [Send("reduceMap", {'reduce': vals}) for vals in result.map]

def reduceMap(state: State) -> State:
    return {'value': sum(state["reduce"])}

graph = StateGraph(State)
graph.add_node(generateMap)
graph.add_node(reduceMap)

# The node containing the Send function is always going to act as a conditional router, since it is dynamically passing data to parallel nodes.
graph.add_conditional_edges(START, generateMap)
graph.add_edge("reduceMap", END)

# Another thing to note is that each concurrent branch doesnt wait for the rest of the branch, but they expect to be reduced some way.
graph = graph.compile()
print(graph.invoke({}))