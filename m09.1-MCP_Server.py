from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Local_File_System")

@mcp.tool()
def readFile(filename:str) -> str | None:
    """Takes a the name of a file and reads its content."""
    try:
        with open(filename, mode="r") as f:
            return f.read()
    except:
        return None
    

@mcp.tool()
def writeFile(filename:str, content: str) -> int | None:
    """Takes a the name of a file and writes the content into that file."""
    print(content)
    try:
        with open(filename, mode="w") as f:
            return f.write(content)
    except:
        return None

mcp.run(transport="stdio")