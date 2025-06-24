# Agentic Observability Demo

## Your Accurate Flight Assistant

This demo showcases a solution for agent observability and tracing by building on the LlamaIndex x OpenTelemetry integration.

It traces the activity of an agent capable of extracting information from a University course syllabus (with LlamaExtract) and answer questions about it (with a LlamaCloud Index in the backend).

> _The agents tool are served via MCP!_

### Get it up and running!

Get the GitHub repository:

```bash
git clone https://github.com/AstraBert/agents-observability-demo
```

Install dependencies:

```bash
cd agents-observability-demo/
uv sync
```

And then modify the `.env.example` file with your API keys and move it to `.env`.

```bash
mv .env.example .env
```

Now, you will have to execute the following scripts:

```bash
uv run tools/create_llama_extract_agent.py
uv run tools/create_llama_cloud_index.py
```

You're ready to set up the app!

Launch a local Postgres database + a local Jaeger instance to record OpenTelemetry traces:

```bash
docker compose up -d
```

Run the MCP server:

```bash
uv run src/agents_observability_demo/server.py
```

In a separate window, run the websocket:

```bash
uv run src/agents_observability_demo/websocket.py
```

Last, run the Gradio frontend, and start exploring at http://localhost:7860:

```bash
uv run src/agents_observability_demo/main.py
```

### Contributing

Contribute to this project following the [guidelines](./CONTRIBUTING.md).

### License

This project is provided under an [MIT License](LICENSE).
