from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv(override=True)


class Team1SupervisorSchema(BaseModel):
    next: Literal["team_1_agent_1", "team_1_agent_2", "__end__"]

class Team2SupervisorSchema(BaseModel):
    next: Literal["team_2_agent_1", "team_2_agent_2", "__end__"]

class TopSupervisorSchema(BaseModel):
    next: Literal["team_1_graph", "team_2_graph", "__end__"]

supervisor1_model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash").with_structured_output(Team1SupervisorSchema)
supervisor2_model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash").with_structured_output(Team2SupervisorSchema)
top_supervisor_model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash").with_structured_output(TopSupervisorSchema)
worker_model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash")

def team_1_supervisor(state: MessagesState) -> Command[Literal["team_1_agent_1", "team_1_agent_2", f"{END}"]]:
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=
            """
            You are the Issue Understanding Supervisor.
            Split the customer ticket into two tasks:
            Extract order details.
            Detect customer sentiment.

            Send each task to your workers (A1, A2), then merge their outputs into a structured JSON summary.
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    response = (prompt | supervisor1_model).invoke({"messages": state['messages']})
    return Command(goto=response.next, update={"messages": [response]} if response.next == END else {"messages": []})

def team_1_agent_1(state: MessagesState) -> Command[Literal["team_1_supervisor"]]:
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=
            """
            Given a customer support ticket, extract:
            Order number (if mentioned)
            Product(s)
            Timeline (when issue happened)
            Issue type (delivery delay, damaged item, wrong product, etc.)

            Output as structured JSON.
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    response = (prompt | worker_model).invoke({"messages": state['messages']})
    return Command(goto="team_1_supervisor", update={"messages": [response]})

def team_1_agent_2(state: MessagesState) -> Command[Literal["team_1_supervisor"]]:
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=
            """
            You are the Sentiment Detector.
            Given a customer support ticket, classify customer sentiment as one of:
            angry
            frustrated
            neutral
            positive

            Explain briefly why.
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    response = (prompt | worker_model).invoke({"messages": state['messages']})
    return Command(goto="team_1_supervisor", update={"messages": [response]})

team_1_graph = (
    StateGraph(MessagesState)
    .add_node(team_1_supervisor)
    .add_node(team_1_agent_1)
    .add_node(team_1_agent_2)
    .add_edge(START, "team_1_supervisor")
    .compile()
)

def team_2_supervisor(state: MessagesState) -> Command[Literal["team_2_agent_1", "team_2_agent_2", f"{END}"]]:
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=
            """
            You are the Resolution Supervisor.
            Receive the structured summary from Graph A.
            Split the task into:
            Find the best resolution policy.
            Draft a customer-facing response.
            
            Collect outputs from your workers (B1, B2) and merge them into a proposed solution + ready-to-send reply.
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    response = (prompt | supervisor2_model).invoke({"messages": state['messages']})
    return Command(goto=response.next, update={"messages": [response]} if response.next == END else {"messages": []})

def team_2_agent_1(state: MessagesState) -> Command[Literal["team_2_supervisor"]]:
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=
            """
            You are the Policy Finder.
            Given the structured issue summary, check company policy.
            Decide the correct resolution (refund, resend item, apology, escalation, etc.).
            Output the resolution in plain text.
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    response = (prompt | worker_model).invoke({"messages": state['messages']})
    return Command(goto="team_2_supervisor", update={"messages": [response]})

def team_2_agent_2(state: MessagesState) -> Command[Literal["team_2_supervisor"]]:
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=
            """
            You are the Response Drafter.
            Using the structured issue summary + resolution, write a polite, empathetic, and professional customer response.
            Keep it short, clear, and supportive.
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    response = (prompt | worker_model).invoke({"messages": state['messages']})
    return Command(goto="team_2_supervisor", update={"messages": [response]})

team_2_graph = (
    StateGraph(MessagesState)
    .add_node(team_2_supervisor)
    .add_node(team_2_agent_1)
    .add_node(team_2_agent_2)
    .add_edge(START, "team_2_supervisor")
    .compile()
)

def top_level_supervisor(state: MessagesState) -> Command[Literal["team_1_graph", "team_2_graph", f"{END}"]]:
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=
            """
            You are the Support Manager Agent.
            Your job is to coordinate two subteams:
            Graph A (Issue Understanding): extracts structured info from the ticket.
            Graph B (Resolution): proposes a solution and drafts a reply.
                                
            Take the ticket, send it to Graph A, then pass the structured summary to Graph B.
            Review Graph B's output and provide the final polished response to the customer.
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    response = (prompt | top_supervisor_model).invoke({"messages": state['messages']})
    return Command(goto=response.next, update={"messages": [response]} if response.next == END else {"messages": []})

graph = (
    StateGraph(MessagesState)
    .add_node(top_level_supervisor)
    .add_node("team_1_graph", team_1_graph)
    .add_node("team_2_graph", team_2_graph)
    .add_edge(START, "top_level_supervisor")
    .add_edge("team_1_graph", "top_level_supervisor")
    .add_edge("team_2_graph", "top_level_supervisor")
    .compile()
)

CONFIG = {'configurable':{'thread_id':1}}
for message in graph.stream({"messages":[HumanMessage(content="My order didn't arrive on time.")]}, config=CONFIG, stream_mode="updates"):
    for node, updates in message.items():
            print(f"Update from node: {node}")
            try:
                if "messages" in updates:
                        updates["messages"][-1].pretty_print()
                else:
                    print(updates)
            except:
                pass
            print("\n")