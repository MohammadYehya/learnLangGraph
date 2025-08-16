from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
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

def generateSentiment(state: State) -> Command[Literal["generateFeedbackEmail", "generateResponse"]]:
    parser = PydanticOutputParser(pydantic_object=Sentiment)
    prompt = PromptTemplate(template="Find the sentiment in POSITIVE or NEGATIVE of the following review:\n\n{review}\n\n{format_instruction}", input_variables=['review'], partial_variables={'format_instruction':parser.get_format_instructions()})
    chain = prompt | ChatOpenAI() | parser
    result = chain.invoke({'review': state['review']}).sentiment
    return Command(update={'sentiment': result}, goto="generateFeedbackEmail" if result == "Negative" else "generateResponse")
    # Command can update the state and dynamically route to the next node effectively removing the need for add_conditional_edges

def generateFeedbackEmail(state: State) -> State:
    parser = PydanticOutputParser(pydantic_object=Email)
    prompt = PromptTemplate(template="Generate an email to send to customer support explaining this NEGATIVE review sent by the user:\n\n{review}\n\n{format_instruction}", input_variables=['review'], partial_variables={'format_instruction':parser.get_format_instructions()})
    chain = prompt | ChatOpenAI() | parser
    return chain.invoke({'review': state['review']})

def generateResponse(state: State) -> State:
    return {"response": "Thank you for your support!"}

builder = StateGraph(State)

builder.add_node("generateSentiment", generateSentiment)
builder.add_node("generateFeedbackEmail", generateFeedbackEmail)
builder.add_node("generateResponse", generateResponse)

# No need for add_conditional_edges since the Command is taking care of it
builder.add_edge(START, "generateSentiment")
builder.add_edge("generateResponse", END)
builder.add_edge("generateFeedbackEmail", END)

graph = builder.compile()
result = graph.invoke({'review': 'Nice App, for a dead man! The UI is dog shit!'})
print(result)