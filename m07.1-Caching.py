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

graph = (
    StateGraph(State)
    .add_node(expensive_node, cache_policy=CachePolicy(ttl=120))    # To add a cache to a node, we add a CachePolicy with a ttl in seconds. If None is given then there is no ttl.
    .set_entry_point("expensive_node")
    .set_finish_point("expensive_node")
    .compile(cache=InMemoryCache(), checkpointer=InMemorySaver())
    # The cache is defined while compiling the graph
)

CONFIG = {'configurable': {'thread_id':1, 'user_id':1}}
CONFIG2 = {'configurable': {'thread_id':2, 'user_id':1}}
print(graph.invoke({"x": 5}, config=CONFIG, stream_mode="updates", debug=True))
print(graph.invoke({"x": 5}, config=CONFIG, stream_mode="updates", debug=True))
# Caching across different threads is allowed, as the cache is independent of the config.

# IMPORTANT
# In this example, if the second invocation used the same config as the first one, the cache would not be used.
# This is because the default cache key uses the entire input state as the key. 
# Since the checkpointer, accumulates the state, the second invocation would have a different state than the first one, therefore a cache miss would occur.
# For an indepth view, you can add the debug flag to the invoke method when using the same config; debug=True
# This would show that the input state for the second invocation is {'x': 5, 'result': 10} which is different from the first invocation's input state: {'x': 5}
# To avoid this, we can define a custom key function that only uses the relevant parts of the state for caching.
# This is shown in the next example.
# See m07.2-Caching.py
