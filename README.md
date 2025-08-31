# learnLangGraph
Feel free to use any LLM provider that is compatible with Langchain. In this repository, I used a mixture of both OpenAI and GoogleGemini.

## Repo Structure
| Module         | Content                                                                            |
|----------------|-------------------------------------------------------------------------------------|
| `m01.*`        | Core graph types: Sequential, Parallel, Conditional, Reducers, Custom reducers, Iterative |
| `m02.*`        | Functional nodes: command sending, messaging behaviors                             |
| `m03`          | Deferred graph node execution                                                      |
| `m04.*`        | Human-in-the-loop patterns: approve/reject, review/edit                           |
| `m05`          | Utility tools and helpers for graph operations                                    |
| `m06.*`        | Memory modules: short-term persistence, long-term memory, knowledge-graph integration |
| `m07`          | Caching strategies for optimized graph execution                                  |
| `m08`          | Streaming workflows                            |
| `m09.*`        | Client/server orchestration (MCP Server / Client)                                 |
| `m10.*`        | Multi-agent systems: flat networks, supervisory control, tool-assisted, hierarchical |
| `m11`          | Graph visualization tools for structure                     |
| `p01`          | Dynamic distributed graph orchestration across nodes                              |

## Getting Started
1. Clone the repo:
```bash
git clone https://github.com/MohammadYehya/learnLangGraph.git
cd learnLangGraph
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Try out your first module:
```bash
python m01.1-SequentialGraph.py
```

## Recommended Resources
- [LangGraph Official Documentation](https://langchain-ai.github.io/langgraph/) - Deep dives into every feature.
- [YouTube Playlist - Agentic AI using LangGraph](https://www.youtube.com/playlist?list=PLKnIA16_RmvYsvB8qkUQuJmJNuiCUJFPL) - by CampusX.