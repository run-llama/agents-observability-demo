import os
from dotenv import load_dotenv

from llama_index.tools.mcp import McpToolSpec, BasicMCPClient
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

load_dotenv()

llm = OpenAI(model="gpt-4.1", api_key=os.getenv("OPENAI_API_KEY"))
mcp_client = BasicMCPClient(command_or_url="http://localhost:8000/mcp")
tool_spec = McpToolSpec(client=mcp_client)
tools = tool_spec.to_tool_list()

agent = FunctionAgent(
    name="SyllabusAgent",
    description="Agent to extract information about course syllabus and to answer questions about it.",
    tools=tools,
    system_prompt="""
    You are SyllabusAgent. You have two main tasks:
    1. Extract information from a syllabus file (in PDF format) and return a summary of that information to the user. Use the 'syllabus_extractor_tool' for this task. Always report to the user the information you extracted in a human-readable format.
    2. Answer questions about courses syllabi. Use the 'answer_questions_tool' for this task. Always report the answer to the user.

    Choose the tools based on the task you are asked to perfom.
    """,
    llm=llm,
    timeout=600,
)
