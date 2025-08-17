
# WIP


from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, Send
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import TypedDict, Literal, Annotated
import operator
from dotenv import load_dotenv
load_dotenv()

class State(TypedDict):
    map: list[list[int]]
    interMap: Annotated[list[list[int]], operator.add]
    reduce: list[int]
    value: Annotated[int, operator.add]

class MapSchema(BaseModel):
    map: list[list[int]] = Field(description="A 2D map of integers.")

def generateMap(state: State) -> Command[Literal["intermediateNode", "reduceMap"]]:
    print('GENERATEMAP',state)
    if(len(state['interMap']) == 0):
        # result = ChatOpenAI(model = 'gpt-4o').with_structured_output(schema=MapSchema).invoke('Generate a huge 2D map of integers. Also make the inner lists vary in size.')
        result = {'map': [[1,2,3], [4,5,6,7,8,9,10]]}
        return Command(
            update={'map': result['map']},
            goto=[Send("reduceMap" if len(vals) > 7 else "intermediateNode", {'reduce': vals}) for vals in result['map']]
        )
    else:
        result = {'map': state['interMap']}
        state['interMap'] = []
        return Command(
            update=state,
            goto=[Send("reduceMap" if len(vals) > 7 else "intermediateNode", {'reduce': vals}) for vals in result['map']]
        )

def intermediateNode(state: State) -> Command[Literal["generateMap"]]:
    print('INTERMEDIATE', state)
    return Command(
        update= {'interMap': [state['reduce'] + [0]]},
        goto="generateMap",
        
    )

def reduceMap(state: State) -> State:
    return {'value': sum(state["reduce"])}

builder = StateGraph(State)
builder.add_node(generateMap)
builder.add_node(intermediateNode)
builder.add_node(reduceMap)

builder.add_edge(START, "generateMap")
builder.add_edge("reduceMap", END)


graph = builder.compile(checkpointer=InMemorySaver())
result = graph.invoke({'interMap':[]}, config={"configurable": {"thread_id":1}, 'recursion_limit': 10})
print(result)