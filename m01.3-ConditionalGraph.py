from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()

class State(TypedDict):
    review: str
    sentiment: Literal["Positive", "Negative"]
    email: str
    response: str

class Sentiment(BaseModel):
    sentiment: Literal["Positive", "Negative"] = Field(description="The sentiment of the review.")

class Email(BaseModel):
    email: str = Field(description="The Emaol to send to Customer Support.")

def generateSentiment(state: State) -> State:
    parser = PydanticOutputParser(pydantic_object=Sentiment)
    prompt = PromptTemplate(template="Find the sentiment in POSITIVE or NEGATIVE of the following review:\n\n{review}\n\n{format_instruction}", input_variables=['review'], partial_variables={'format_instruction':parser.get_format_instructions()})
    chain = prompt | ChatOpenAI() | parser
    return chain.invoke({'review': state['review']})

def generateFeedbackEmail(state: State) -> State:
    parser = PydanticOutputParser(pydantic_object=Email)
    prompt = PromptTemplate(template="Generate an email to send to customer support explaining this NEGATIVE review sent by the user:\n\n{review}\n\n{format_instruction}", input_variables=['review'], partial_variables={'format_instruction':parser.get_format_instructions()})
    chain = prompt | ChatOpenAI() | parser
    return chain.invoke({'review': state['review']})

def generateResponse(state: State) -> State:
    return {"response": "Thank you for your support!"}

def route(state: State):
    return "generateResponse" if state['sentiment'] == 'Positive' else "generateFeedbackEmail"

builder = StateGraph(State)

builder.add_node("generateSentiment", generateSentiment)
builder.add_node("generateFeedbackEmail", generateFeedbackEmail)
builder.add_node("generateResponse", generateResponse)

builder.add_edge(START, "generateSentiment")
builder.add_conditional_edges("generateSentiment", route)
# To create a conditional route, we use the add_conditional_edges function. It takes the starting node, and a function which on condition outputs the name of the second node.
# Another way to do it is that the route function returns a string and we pass another argument, which is a mapping from the string to the node
# add_conditional_edges("generateSentiment", route, {'gotoEmail':'generateFeedbackEmail', 'gotoResponse':'generateResponse'})
builder.add_edge("generateResponse", END)
builder.add_edge("generateFeedbackEmail", END)

graph = builder.compile()
result = graph.invoke({'review': 'Nice App, for a dead man! The UI is dog shit!'})
print(result)