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
    # expensive computation
    time.sleep(2)
    return {"result": state["x"] * 2}

cache = InMemoryCache()
graph = (
    StateGraph(State)
    .add_node(expensive_node, cache_policy=CachePolicy(ttl=120))    # To add a cache to a node, we add a CachePolicy with a ttl in seconds. If None is given then there is no ttl.
    .set_entry_point("expensive_node")
    .set_finish_point("expensive_node")
    .compile(cache=cache, checkpointer=InMemorySaver())
    # The cache is defined while compiling the graph
)

CONFIG = {'configurable': {'thread_id':1, 'user_id':1}}
CONFIG2 = {'configurable': {'thread_id':2, 'user_id':1}}
print(graph.invoke({"x": 5}, config=CONFIG, stream_mode="updates"))
print(graph.invoke({"x": 5}, config=CONFIG2, stream_mode="updates"))
# Caching can not be achieved in the same thread
# Therefore we made a new CONFIG2 for showcasing the cache in action