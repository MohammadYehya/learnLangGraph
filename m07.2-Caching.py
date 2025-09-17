from langgraph.graph import StateGraph
from langgraph.cache.memory import InMemoryCache
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import CachePolicy
from typing import TypedDict
import time

class State(TypedDict):
    x: int
    result: int

def expensive_node(state: State) -> State:
    time.sleep(2)
    return {"result": state["x"] * 2}

def cache_key(state: State) -> str:
    return str(state["x"])
# The CachePolicy has another parameter called key_func which can be used to define a custom key for the cache (as the cache is basically a hashmap). If None is given then the key is generated from the input state.
# This states that the cache key will only depend on the value of "x" in the state. Therefore, if the input state has the same "x" value, the cache will be used, regardless of other parts of the state.

graph = (
    StateGraph(State)
    .add_node(expensive_node, cache_policy=CachePolicy(key_func=cache_key))
    .set_entry_point("expensive_node")
    .set_finish_point("expensive_node")
    .compile(cache=InMemoryCache(), checkpointer=InMemorySaver())
)

CONFIG = {'configurable': {'thread_id':1, 'user_id':1}}
print(graph.invoke({"x": 5}, config=CONFIG, stream_mode="updates"))
print(graph.invoke({"x": 5}, config=CONFIG, stream_mode="updates"))