from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import TypedDict
from dotenv import load_dotenv
load_dotenv()

# Any langgraph graph needs a specific state defined, which basically defines all the shared variables that the graph nodes will use
class DensityState(TypedDict):
    mass: float
    volume: float
    density: float
    material: str

# Now the StateGraph will use the defined State
graph = StateGraph(DensityState)

# When defining the Nodes, each node's parameter and return types will be of the State's type
def calculateDensity(state: DensityState) -> DensityState:
    return {"density": state["mass"]/state["volume"]}   # You can also return the entire state, but returning a partial state also works

def findMaterialbyDensity(state: DensityState) -> DensityState:
    prompt = PromptTemplate(template = "Find the closest material which has the density of {density}kg/m^3. Only give me the name of the material, nothing more.", input_variables=['density'])
    llm = ChatOpenAI()
    parser = StrOutputParser()
    chain = prompt | llm | parser
    return {"material": chain.invoke({"density": state['density']})}

graph.add_node("calculateDensity", calculateDensity)
graph.add_node("findMaterialbyDensity", findMaterialbyDensity)
graph.add_edge(START, "calculateDensity")
graph.add_edge("calculateDensity", "findMaterialbyDensity")
graph.add_edge("findMaterialbyDensity", END)
graph = graph.compile()
result = graph.invoke({"mass":1000, "volume":1})
print(result['material'])