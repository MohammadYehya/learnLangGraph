from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
import operator

class State(TypedDict):
    x: Annotated[list[str], operator.add]
    # A reducer is used to change the default behavior of overriding the state
    # In this case, whenever the state attribute 'x' is updated, instead of being overrided, it will be added to the previous value

def node1(state: State):
    return {'x': ['A']}
def node2(state: State):
    return {'x': ['B']}
def node3(state: State):
    return {'x': ['C']}

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

print(graph.invoke({}))