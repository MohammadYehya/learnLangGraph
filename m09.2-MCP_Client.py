import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
import asyncio
from dotenv import load_dotenv
load_dotenv(override=True)

client = MultiServerMCPClient({
    # "Stock_Search": {
    #     "transport":"streamable_http",
    #     "url":"http://localhost:8000/mcp/"
    # },
    "Local_File_System": {
        "command": "python",
        "args": ["m08.1-MCP_Server.py"],
        "transport":"stdio",
    },
    "Github": {
        "transport": "streamable_http",
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": {
            # "Authorization": "Bearer ${GITHUB_PAT}"
            "Authorization": f"Bearer {os.getenv('GITHUB_PAT')}"
        }
    },
    # "context7": {
    #   "transport": "streamable_http",
    #   "url": "https://mcp.context7.com/mcp"
    # }
    # "Calculator": {
    #     "transport":"streamable_http",
    #     "url":"http://localhost:8001/mcp/"
    # }
})

async def main():
    tools = await client.get_tools()
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash").bind_tools(tools)

    def generateContext(state: MessagesState):
        for i, message in enumerate(state["messages"]):
            print(f"MESSAGE{i}: ", message, end='\n\n')
        response = model.invoke(state["messages"])
        return {'messages': [response]}
        # Can not use Command here because the state needs to be updated first
        # return Command(update={'messages': response}, goto=tools_condition(state))

    graph = (
        StateGraph(MessagesState)
        .add_node(generateContext)
        .add_node("tools", ToolNode(tools))
        .add_edge(START, "generateContext")
        .add_conditional_edges("generateContext", tools_condition)  # REMOVE PRINT STATEMENT FROM INNER LIBRARY
        .add_edge("tools", "generateContext")
        .compile()
    )

    # question = "Make a file called poem.txt and write a short poem in it."
    # question = "Get me the latest version of NextJS."
    # question = "Retrieve the contents of the readme of the repo MohammadYehya/GridForge using the Github MCP. Then get the information from the tool call by accessing it's artifact attribute. Then use the Local_File_System MCP to store the retrieved content in a new file in this local machine called test.md."
    question = "Retrieve the contents of the readme of the repo MohammadYehya/GridForge using the Github MCP. Then ouput the tool's response as is and display it."
    print(question)
    async for message in graph.astream({"messages":question}, stream_mode="updates"):
        # print(message, end='\n\n')
        pass

asyncio.run(main())