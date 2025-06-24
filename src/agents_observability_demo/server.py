from utils import answer_question_about_course, extract_syllabus
from fastmcp import FastMCP
from typing import Union, Literal

mcp: FastMCP = FastMCP("Syllabus Extraction MCP")

SYLLABUS_EXTRACTOR_TOOL_DESCRIPTION = """
Tool to extract information from a syllabus PDF file.

Args:
    file_path (str): The path to the file containing the syllabus.

Returns:
    str: the extracted information from the syllabus in JSON-like format, if any.
"""

ANSWER_QUESTIONS_TOOL_DESCRIPTION = """
Tool to answer question about a course syllabus.

Args:
    question (str): The question about the syllabus.

Returns:
    str: The answer to the question, if any.
"""


@mcp.tool(
    name="syllabus_extractor_tool", description=SYLLABUS_EXTRACTOR_TOOL_DESCRIPTION
)
async def syllabus_extractor_tool(
    file_path: str,
) -> Union[str, Literal["Sorry, no information could be extracted from the syllabus."]]:
    extraction_info = await extract_syllabus(filename=file_path)
    if not extraction_info:
        return "Sorry, no information could be extracted from the syllabus."
    return extraction_info


@mcp.tool(name="answer_questions_tool", description=ANSWER_QUESTIONS_TOOL_DESCRIPTION)
async def answer_questions_tool(question: str):
    response = await answer_question_about_course(question=question)
    if not response:
        return "Sorry, no answer could be found for this question."
    return response


if __name__ == "__main__":
    mcp.run("streamable-http")
