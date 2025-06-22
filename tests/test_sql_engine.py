import socket
import pytest
import pandas as pd

from src.agents_observability.utils import OtelTracesSqlEngine
from sqlalchemy import Row


def is_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is open on a given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        return result == 0

@pytest.fixture()
def otel_data() -> pd.DataFrame:
    pd.DataFrame(
        {
            "trace_id": ["abc123", "abc123", "def456"],
            "span_id": ["span1", "span2", "span3"],
            "parent_span_id": [None, "span1", "span2"],
            "operation_name": [
                "ServiceA.handle_request",
                "ServiceA.query_db",
                "ServiceB.send_email"
            ],
            "start_time": [1750618321000000, 1750618321000100, 1750618321000200],
            "duration": [150, 300, 500],
            "status_code": ["OK", "OK", "ERROR"],
            "service_name": ["service-a", "service-a", "service-b"]
        }
    )

@pytest.mark.skipif(
    condition=not is_port_open(host="localhost", port=16686) and not is_port_open(host="localhost", port=5432),
    reason="Either Jaeger or Postgres (or both) are currently unavailable"
)
def test_engine(otel_data: pd.DataFrame) -> None:
    engine_url = "postgresql+psycopg2://localhost:admin@localhost:5432/postgres"
    sql_engine = OtelTracesSqlEngine(engine_url=engine_url, table_name="test")
    sql_engine._to_sql(dataframe=otel_data)
    res1 = sql_engine.execute("SELECT span_id, operation_name, duration FROM traces WHERE status_code = 'ERROR'")
    res2 = sql_engine.execute("SELECT service_name, AVG(duration) AS avg_duration FROM traces GROUP BY service_name;")
    assert res1.fetchall() == [Row(span_id='span3', operation_name='ServiceB.send_email', duration=500)]
    assert res2.fetchall() == [
        Row(service_name='service-a', avg_duration=225.0),
        Row(service_name='service-b', avg_duration=500.0)
    ]
        
    
    