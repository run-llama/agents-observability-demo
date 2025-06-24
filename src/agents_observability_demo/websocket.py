import json
import asyncio
import websockets
import time
import os

from dotenv import load_dotenv
from agent import agent
from utils import OtelTracesSqlEngine
from llama_index.observability.otel import LlamaIndexOpenTelemetry
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from llama_index.core.agent.workflow.workflow_events import ToolCall, ToolCallResult

load_dotenv()

# define a custom span exporter
span_exporter = OTLPSpanExporter("http://0.0.0.0:4318/v1/traces")

# initialize the instrumentation object
instrumentor = LlamaIndexOpenTelemetry(
    service_name_or_resource="agent.traces",
    span_exporter=span_exporter,
    debug=True,
)
sql_engine = OtelTracesSqlEngine(
    engine_url=f"postgresql+psycopg2://{os.getenv('pgql_user')}:{os.getenv('pgql_psw')}@localhost:5432/{os.getenv('pgql_db')}",
    table_name="agent_traces",
    service_name="agent.traces",
)


async def run_agent(websocket):
    async for prompt in websocket:
        handler = agent.run(user_msg=prompt)
        start_time = int(time.time() * 1000000)
        async for event in handler.stream_events():
            if isinstance(event, ToolCallResult):
                await websocket.send(
                    f"**Result from `{event.tool_name}`**:\n\n{event.tool_output.content}\n\n"
                )
            elif isinstance(event, ToolCall):
                await websocket.send(
                    f"### Calling tool: `{event.tool_name}`\n\n```json\n{json.dumps(event.tool_kwargs, indent=4)}\n```\n\n"
                )
        response = await handler
        response = str(response)
        end_time = int(time.time() * 1000000)
        await websocket.send("### Final output\n\n" + response)
        await websocket.send("[END]")
        sql_engine.to_sql_database(start_time=start_time, end_time=end_time)


async def main():
    instrumentor.start_registering()
    print("Starting server on ws://localhost:8765")
    async with websockets.serve(run_agent, "localhost", 8765):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
