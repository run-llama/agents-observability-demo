import requests
import time
import csv
import pandas as pd
import tempfile as temp
import os

from sqlalchemy import Engine, create_engine, Connection, Result
from typing import Optional, Dict, Any, List, Literal, Union


class OtelTracesSqlEngine:
    def __init__(
        self,
        engine: Optional[Engine] = None,
        engine_url: Optional[Dict[str, Any]] = None,
        table_name: Optional[str] = None,
        service_name: Optional[str] = None,
    ):
        self.service_name: str = service_name or "service"
        self.table_name: str = table_name or "otel_traces"
        self._connection: Optional[Connection] = None
        if engine:
            self._engine: Engine = engine
        elif engine_url:
            self._engine = create_engine(url=engine_url)
        else:
            raise ValueError("One of engine or engine_setup_kwargs must be set")

    def _connect(self) -> None:
        self._connection = self._engine.connect()

    def _export(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        url = "http://localhost:16686/api/traces"
        params = {
            "service": self.service_name,
            "start": start_time
            or int(time.time() * 1000000) - (24 * 60 * 60 * 1000000),
            "end": end_time or int(time.time() * 1000000),
            "limit": limit or 1000,
        }
        response = requests.get(url, params=params)
        return response.json()

    def _to_pandas(self, data: Dict[str, Any]) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        # Loop over each trace
        for trace in data.get("data", []):
            trace_id = trace.get("traceID")
            service_map = {
                pid: proc.get("serviceName")
                for pid, proc in trace.get("processes", {}).items()
            }

            for span in trace.get("spans", []):
                span_id = span.get("spanID")
                operation = span.get("operationName")
                start = span.get("startTime")
                duration = span.get("duration")
                process_id = span.get("processID")
                service = service_map.get(process_id, "")
                status = next(
                    (
                        tag.get("value")
                        for tag in span.get("tags", [])
                        if tag.get("key") == "otel.status_code"
                    ),
                    "",
                )
                parent_span_id = None
                if span.get("references"):
                    parent_span_id = span["references"][0].get("spanID")

                rows.append(
                    {
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "parent_span_id": parent_span_id,
                        "operation_name": operation,
                        "start_time": start,
                        "duration": duration,
                        "status_code": status,
                        "service_name": service,
                    }
                )

        # Define the CSV header
        fieldnames = [
            "trace_id",
            "span_id",
            "parent_span_id",
            "operation_name",
            "start_time",
            "duration",
            "status_code",
            "service_name",
        ]

        fl = temp.NamedTemporaryFile(suffix=".csv", delete=False, delete_on_close=False)
        # Write to CSV
        with open(fl.name, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        df = pd.read_csv(fl)
        os.remove(fl.name)
        return df

    def _to_sql(
        self,
        dataframe: pd.DataFrame,
        if_exists_policy: Optional[Literal["fail", "replace", "append"]] = None,
    ) -> None:
        if not self._connection:
            self._connect()
        dataframe.to_sql(
            name=self.table_name,
            con=self._connection,
            if_exists=if_exists_policy or "append",
        )

    def to_sql_database(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
        if_exists_policy: Optional[Literal["fail", "replace", "append"]] = None,
    ) -> None:
        data = self._export(start_time=start_time, end_time=end_time, limit=limit)
        df = self._to_pandas(data=data)
        self._to_sql(dataframe=df, if_exists_policy=if_exists_policy)

    def execute(
        self,
        statement: str,
        parameters: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        execution_options: Optional[Dict[str, Any]] = None,
    ) -> Result:
        if not self._connection:
            self._connect()
        return self._connection.execute(
            statement=statement,
            parameters=parameters,
            execution_options=execution_options,
        )

    def disconnect(self) -> None:
        if not self._connection:
            raise ValueError("Engine was never connected!")
        self._engine.dispose(close=True)
