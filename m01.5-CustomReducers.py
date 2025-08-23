from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated

def sortedAdd(a:list[int], b:list[int]):
    if type(b) == int:
        a+=[b]
    else:
        a+=b
    return sorted(a)
    
class State(TypedDict):
    x: Annotated[list[int], sortedAdd]
    # The reducer can be any regular python function

def node1(state: State):
    return {'x': 5}
def node2(state: State):
    return {'x': 11}
def node3(state: State):
    return {'x': 27}

graph = (
    StateGraph(State)
    .add_node(node1)
    .add_node(node2)
    .add_node(node3)
    .add_edge(START, "node1")
    .add_edge("node1", "node2")
    .add_edge("node2", "node3")
    .add_edge("node3", END)
    .compile()
)

print(graph.invoke({'x': [1,9,34,0]}))