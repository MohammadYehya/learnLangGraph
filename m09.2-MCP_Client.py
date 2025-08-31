import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate
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
        "args": ["m09.1-MCP_Server.py"],
        "transport":"stdio",
    },
    "Github": {
        "transport": "streamable_http",
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": {
            "Authorization": f"Bearer {os.getenv('GITHUB_PAT')}"
        }
    },
    # "Calculator": {
    #     "transport":"streamable_http",
    #     "url":"http://localhost:8001/mcp/"
    # }
})

@tool
def parseGithubToolOutput(content):
    """Parse the output of the Github tool call and add the content of the artifact to the last message."""
    print("CONTENT: ", content)
    return {'messages': content.artifact[0].resource}

async def main():
    tools = await client.get_tools()
    tools += [parseGithubToolOutput]
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash").bind_tools(tools)

    def generateContext(state: MessagesState) -> MessagesState:
        try:
            # print("ARTIFACT: ", state['messages'][-1].artifact[0].resource.text)
            print("ARTIFACT: ", state['messages'][-1].artifact[0].resource)
        except:
            pass
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that helps the user to decide what tool to use to answer their question. You have access to the following tools:"
            "Github MCP Server, Local_File_System MCP Server. You can call any of these tools to help you answer the user's question."),
            ("placeholder", "{messages}")
        ])
        response = (prompt | model).invoke({'messages': state["messages"]})
        print("RESPONSE: ", type(response))
        return {'messages': [response]}
        # Can not use Command here because the state needs to be updated first
        # return Command(update={'messages': response}, goto=tools_condition(state))

    graph = (
        StateGraph(MessagesState)
        .add_node(generateContext)
        .add_node("tools", ToolNode(tools))
        .add_edge(START, "generateContext")
        .add_conditional_edges("generateContext", tools_condition)
        .add_edge("tools", "generateContext")
        .compile()
    )

    # question = "Make a file called poem.txt and write a short poem in it."
    # question = "Get me the latest version of NextJS."
    question = "Retrieve the contents of the readme of the repo MohammadYehya/GridForge using the Github MCP."
    # question = "Retrieve the contents of the readme of the repo MohammadYehya/GridForge using the Github MCP. Then get the information from the tool call by accessing it's artifact attribute. Then use the Local_File_System MCP to store the retrieved content in a new file in this local machine called test.md."
    # question = "Retrieve the logo of the repo MohammadYehya/GridForge from gitassets/images/name.png using the Github MCP."
    # question = "Retrieve both test.cpp and test2.cpp from the repo MohammadYehya/GridForge using the Github MCP. Make 2 new files in this local machine called test.cpp and test2.cpp and store the retrieved content in them using the Local_File_System MCP."
    print(question)
    async for message in graph.astream({"messages":question}, stream_mode="updates"):
        for node, updates in message.items():
            print(f"Update from node: {node}")
            if "messages" in updates:
                updates["messages"][-1].pretty_print()
            else:
                print(updates)
            print("\n")
        # print(message)
asyncio.run(main())