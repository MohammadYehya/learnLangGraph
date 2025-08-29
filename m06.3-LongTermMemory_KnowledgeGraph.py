from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode
from langchain.tools import tool
from typing_extensions import Literal, TypedDict
from langchain_core.documents import Document
from langchain.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from dotenv import load_dotenv
import uuid
load_dotenv(override=True)

store = Chroma(persist_directory = ".chromadb", collection_name = "m06.2-Memory", embedding_function = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001"))

#____________________________________
#   UTILS
#____________________________________
def get_user_id(config: RunnableConfig) -> str:
    user_id = config["configurable"].get("user_id")
    if user_id is None:
        raise ValueError("User ID needs to be provided to save a memory.")
    return user_id

def pretty_print_stream_chunk(chunk):
    for node, updates in chunk.items():
        print(f"Update from node: {node}")
        if "messages" in updates:
            updates["messages"][-1].pretty_print()
        else:
            print(updates)
        print("\n")

def pretty_print(generator):
    for chunk in generator:
        pretty_print_stream_chunk(chunk)
    print('_'*50)


#____________________________________
#   TOOLS
#____________________________________
class KnowledgeTriple(TypedDict):
    subject: str
    predicate: str
    object_: str

@tool   # This tool is the only change from m06.2-LongTermMemory.py
def save_recall_memory(memories: list[KnowledgeTriple], config: RunnableConfig) -> str:
    """Save memory to vectorstore for later semantic retrieval."""
    user_id = get_user_id(config)
    for memory in memories:
        serialized = " ".join(memory.values())
        document = Document(
            serialized,
            id=str(uuid.uuid4()),
            metadata={
                "user_id": user_id,
                **memory,
            },
        )
        store.add_documents([document])
    return memories

@tool
def search_recall_memories(query: str, config: RunnableConfig) -> list[str]:
    """Search for relevant memories."""
    user_id = get_user_id(config)
    documents = store.similarity_search(query, k=30, filter={"user_id": user_id})
    return [document.page_content for document in documents]

tools = [save_recall_memory, search_recall_memories]

model_with_tools = ChatGoogleGenerativeAI(model="gemini-2.5-flash").bind_tools(tools)

#____________________________________
#   PROMPT
#____________________________________
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant with advanced long-term memory"
            " capabilities. Powered by a stateless LLM, you must rely on"
            " external memory to store information between conversations."
            " Utilize the available memory tools to store and retrieve"
            " important details that will help you better attend to the user's"
            " needs and understand their context.\n\n"
            "Memory Usage Guidelines:\n"
            "1. Actively use memory tools (save_core_memory, save_recall_memory)"
            " to build a comprehensive understanding of the user.\n"
            "2. Make informed suppositions and extrapolations based on stored"
            " memories.\n"
            "3. Regularly reflect on past interactions to identify patterns and"
            " preferences.\n"
            "4. Update your mental model of the user with each new piece of"
            " information.\n"
            "5. Cross-reference new information with existing memories for"
            " consistency.\n"
            "6. Prioritize storing emotional context and personal values"
            " alongside facts.\n"
            "7. Use memory to anticipate needs and tailor responses to the"
            " user's style.\n"
            "8. Recognize and acknowledge changes in the user's situation or"
            " perspectives over time.\n"
            "9. Leverage memories to provide personalized examples and"
            " analogies.\n"
            "10. Recall past challenges or successes to inform current"
            " problem-solving.\n\n"
            "## Recall Memories\n"
            "Recall memories are contextually retrieved based on the current"
            " conversation:\n{recall_memories}\n\n"
            "## Instructions\n"
            "Engage with the user naturally, as a trusted colleague or friend."
            " There's no need to explicitly mention your memory capabilities."
            " Instead, seamlessly incorporate your understanding of the user"
            " into your responses. Be attentive to subtle cues and underlying"
            " emotions. Adapt your communication style to match the user's"
            " preferences and current emotional state. Use tools to persist"
            " information you want to retain in the next conversation. If you"
            " do call tools, all text preceding the tool call is an internal"
            " message. Respond AFTER calling the tool, once you have"
            " confirmation that the tool completed successfully.\n\n",
        ),
        ("placeholder", "{messages}"),
    ]
)

#____________________________________
#   STATE
#____________________________________
class State(MessagesState):
    recall_memories: list[str]

#____________________________________
#   NODES
#____________________________________
def agent(state: State) -> Command[Literal["tools", "__end__"]]:
    """Process the current state and generate a response using the LLM.
    Args:
        state (schemas.State): The current state of the conversation.
    Returns:
        schemas.State: The updated state with the agent's response.
    """
    bound = prompt | model_with_tools
    recall_str = ("<recall_memory>\n" + "\n".join(state["recall_memories"]) + "\n</recall_memory>")
    prediction = bound.invoke({"messages": state["messages"], "recall_memories": recall_str,})
    return Command(
        update = {"messages": [prediction]},
        goto = "tools" if prediction.tool_calls else END
    )

def load_memories(state: State, config: RunnableConfig) -> State:
    """Load memories for the current conversation.
    Args:
        state (schemas.State): The current state of the conversation.
        config (RunnableConfig): The runtime configuration for the agent.
    Returns:
        State: The updated state with loaded memories.
    """
    recall_memories = search_recall_memories.invoke(state["messages"][-1].content, config)
    return {"recall_memories": recall_memories}

#____________________________________
#   GRAPH
#____________________________________
graph = (
    StateGraph(State)
    .add_node(agent)
    .add_node(load_memories)
    .add_node("tools", ToolNode(tools))
    .add_edge(START, "load_memories")
    .add_edge("load_memories", "agent")
    .add_edge("tools", "agent")
    .compile(checkpointer=InMemorySaver())
)

pretty_print(graph.stream({"messages": [("user", "Hi my name is Mohammad Yehya! I love learning AI tech!")]}, config={"configurable": {"thread_id":1, "user_id": 1}}, stream_mode="updates"))
pretty_print(graph.stream({"messages": [("user", "I am currently working a comprehensive LangGraph repository every day. Tomorrow will be the last day.")]}, config={"configurable": {"thread_id":1, "user_id": 1}}, stream_mode="updates"))

pretty_print(graph.stream({"messages": [("user", "Is today the last day of the LangGraph repo?")]}, config={"configurable": {"thread_id":2, "user_id": 1}}, stream_mode="updates"))

pretty_print(graph.stream({"messages": [("user", "Is today the last day of the LangGraph repo?")]}, config={"configurable": {"thread_id":2, "user_id": 2}}, stream_mode="updates"))

pretty_print(graph.stream({"messages": [("user", "Is today the last day of the LangGraph repo?")]}, config={"configurable": {"thread_id":3, "user_id": 2}}, stream_mode="updates"))