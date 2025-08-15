from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    x: float
    y: float
    z: float

# For parallel nodes, make sure that they always return partial states, so that it doesnt conflict with the other states
def step1(state: State):
    return {"y": state['x']**2}

def step2(state: State):
    return {'z': state['x']+state['y']}

graph = StateGraph(State)
graph.add_node("step1", step1)
graph.add_node("step2", step2)

# To define a parallel route, just make multiple edges from a node
graph.add_edge(START, "step1")
graph.add_edge(START, "step2")
graph.add_edge("step1", END)
graph.add_edge("step2", END)

graph = graph.compile()
result = graph.invoke({"x":3, "y":2})
print(result)