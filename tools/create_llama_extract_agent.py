import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llama_cloud_services import LlamaExtract
from src.agents_observability_demo.models import Syllabus
from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    conn = LlamaExtract(api_key=os.getenv("LLAMACLOUD_API_KEY"))
    agent = conn.create_agent(name="syllabus_extract_agent", data_schema=Syllabus)
    _id = agent.id
    with open(".env", "a") as f:
        f.write(f'\nEXTRACT_AGENT_ID="{_id}"')
    return 0


if __name__ == "__main__":
    main()
