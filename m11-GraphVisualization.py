from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.runnables.graph import CurveStyle

def node1(state: MessagesState) -> MessagesState:
    return {"messages": state["messages"]}

def node2(state: MessagesState) -> MessagesState:
    return {"messages": state["messages"]}

def node3(state: MessagesState) -> MessagesState:
    return {"messages": state["messages"]}

graph = (
    StateGraph(MessagesState)
    .add_node(node1)
    .add_node(node2)
    .add_node(node3)
    .add_edge(START, "node1")
    .add_edge("node1", "node2")
    .add_edge("node1", "node3")
    .add_edge("node2", "node3")
    .add_edge("node3", END)
    .compile()
)

graph.get_graph().draw_mermaid_png(curve_style=CurveStyle.BASIS, output_file_path="m11-GraphVisualization.png")