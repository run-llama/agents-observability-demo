import socket
import pytest
import pandas as pd
import os

from src.agents_observability.utils import OtelTracesSqlEngine
from sqlalchemy import text
from dotenv import load_dotenv

ENV = load_dotenv()


def is_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is open on a given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        return result == 0


@pytest.fixture()
def otel_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trace_id": ["abc123", "abc123", "def456"],
            "span_id": ["span1", "span2", "span3"],
            "parent_span_id": [None, "span1", "span2"],
            "operation_name": [
                "ServiceA.handle_request",
                "ServiceA.query_db",
                "ServiceB.send_email",
            ],
            "start_time": [1750618321000000, 1750618321000100, 1750618321000200],
            "duration": [150, 300, 500],
            "status_code": ["OK", "OK", "ERROR"],
            "service_name": ["service-a", "service-a", "service-b"],
        }
    )


@pytest.mark.skipif(
    condition=not is_port_open(host="localhost", port=5432) or not ENV,
    reason="Either Postgres is currently unavailable or you did not set any env variables in a .env file",
)
def test_engine(otel_data: pd.DataFrame) -> None:
    engine_url = f"postgresql+psycopg2://{os.getenv('pgql_user')}:{os.getenv('pgql_psw')}@localhost:5432/{os.getenv('pgql_db')}"
    sql_engine = OtelTracesSqlEngine(engine_url=engine_url, table_name="test")
    res = sql_engine.execute(text("DROP TABLE IF EXISTS test;"))
    res.close()
    sql_engine._to_sql(dataframe=otel_data)
    res1 = sql_engine.execute(
        text(
            "SELECT span_id, operation_name, duration FROM test WHERE status_code = 'ERROR'"
        )
    )
    res2 = sql_engine.execute(
        text(
            "SELECT service_name, AVG(duration) AS avg_duration FROM test GROUP BY service_name;"
        )
    )
    res1_data = res1.fetchall()
    res2_data = res2.fetchall()

    # Compare just the values
    assert len(res1_data) == 1
    assert res1_data[0].span_id == "span3"
    assert res1_data[0].operation_name == "ServiceB.send_email"
    assert res1_data[0].duration == 500

    assert len(res2_data) == 2
    # Sort by service_name for consistent comparison
    res2_sorted = sorted(res2_data, key=lambda x: x.service_name)
    assert res2_sorted[0].service_name == "service-a"
    assert res2_sorted[0].avg_duration == 225.0
    assert res2_sorted[1].service_name == "service-b"
    assert res2_sorted[1].avg_duration == 500.0
