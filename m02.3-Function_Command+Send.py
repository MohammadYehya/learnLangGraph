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

# Correspondingly, if we use the Command function, we can update the state and use the Send function for distributed workloads
def generateMap(state: State) -> State:
    llm = ChatOpenAI(model = "gpt-4o").with_structured_output(schema=MapSchema)
    result = llm.invoke("Generate a 2D map of integers.")
    return Command(
        update={'map': result.map},
        goto=[Send("reduceMap", {'reduce': vals}) for vals in result.map]
    )

def reduceMap(state: State) -> State:
    return {'value': sum(state["reduce"])}

graph = StateGraph(State)
graph.add_node(generateMap)
graph.add_node(reduceMap)

# However, for this aproach, since the Command function handles all dynamic routing we dont need to add conditional edges
graph.add_edge(START, "generateMap")
graph.add_edge("reduceMap", END)

graph = graph.compile()
print(graph.invoke({}))