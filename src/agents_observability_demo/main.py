"""Main script"""

import websockets
import gradio as gr
import os
import pandas as pd

from dotenv import load_dotenv
from typing import Optional
from utils import OtelTracesSqlEngine
from sqlalchemy import text

load_dotenv()

sql_engine = OtelTracesSqlEngine(
    engine_url=f"postgresql+psycopg2://{os.getenv('pgql_user')}:{os.getenv('pgql_psw')}@localhost:5432/{os.getenv('pgql_db')}",
    table_name="agent_traces",
    service_name="agent.traces",
)


async def websocket_chat(question: str, file: Optional[str]):
    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as websocket:
            if file:
                prompt = file
            else:
                prompt = question
            await websocket.send(prompt)
            full_response = ""

            while True:
                message = await websocket.recv()
                if message == "[END]":
                    break
                full_response += message
                yield full_response
            yield full_response

    except Exception as e:
        yield f"Error: {e}"


def display_sql() -> pd.DataFrame:
    query = """CREATE TABLE IF NOT EXISTS agent_traces (
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span_id TEXT NULL,
    operation_name TEXT NOT NULL,
    start_time BIGINT NOT NULL,
    duration INTEGER NOT NULL,
    status_code TEXT NOT NULL,
    service_name TEXT NOT NULL
    );"""
    sql_engine.execute(text(query))
    return sql_engine.to_pandas()


def filter_traces(sql_query: str):
    df = sql_engine.execute(text(sql_query), return_pandas=True)
    print(df)
    return df


def launch_interface():
    with gr.Blocks(
        theme=gr.themes.Citrus(primary_hue="indigo", secondary_hue="teal")
    ) as frontend:
        gr.HTML("<h1 align='center'>Syllabus Extraction Agent</h1>")
        gr.HTML(
            "<h2 align='center'>Extract information and ask questions about your Uni courses!</h2>"
        )
        with gr.Row():
            with gr.Column():
                file_upload = gr.File(
                    value=None, label="Uplod Syllabus File", file_types=[".pdf", ".PDF"]
                )
                usr_txt = gr.Textbox(label="Prompt", placeholder="Ask a question...")
        with gr.Row():
            resp = gr.Markdown(
                label="Agent Output",
                container=True,
                show_label=True,
                show_copy_button=True,
            )
        with gr.Row():
            gr.Button("Submit!").click(
                fn=websocket_chat, inputs=[usr_txt, file_upload], outputs=[resp]
            )

    with gr.Blocks(
        theme=gr.themes.Citrus(primary_hue="indigo", secondary_hue="teal")
    ) as traces:
        gr.HTML("<h1 align='center'>Agent Traces</h1>")
        gr.HTML("<h2 align='center'>Monitor information about your agent</h2>")
        with gr.Row():
            with gr.Column():
                sql_query = gr.Textbox(label="Query SQL database")
                btn = gr.Button("Query")
                df_display = gr.DataFrame(value=display_sql(), label="Traces")
            btn.click(fn=filter_traces, inputs=[sql_query], outputs=[df_display])

    iface = gr.TabbedInterface(
        interface_list=[frontend, traces], tab_names=["Agent", "Traces"]
    )
    iface.launch()


if __name__ == "__main__":
    launch_interface()
