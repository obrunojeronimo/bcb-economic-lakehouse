"""Validate read-only SQL and deploy Brazil Economic Monitor with profile DEFAULT."""

import argparse
import json
import time
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import Dashboard


ROOT = Path(__file__).resolve().parents[1]
DEFINITION = Path(__file__).with_name("brazil_economic_monitor.lvdash.json")
NAME = "Brazil Economic Monitor"


def warehouse(client):
    """Seleciona um warehouse serverless 2X-Small disponível."""
    candidates = [
        item for item in client.warehouses.list()
        if item.cluster_size == "2X-Small" and item.enable_serverless_compute is True
    ]
    if not candidates:
        raise RuntimeError("Nenhum SQL Warehouse 2X-Small disponível no perfil DEFAULT")
    return candidates[0]


def file_queries(path):
    """Lê as consultas SQL de um arquivo, sem comentários de linha."""
    lines = [line for line in path.read_text(encoding="utf-8").splitlines()
             if not line.lstrip().startswith("--")]
    return [statement.strip() for statement in "\n".join(lines).split(";")
            if statement.strip()]


def execute(client, warehouse_id, label, statement):
    """Executa uma consulta de validação e verifica seu resultado."""
    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id, statement=statement, wait_timeout="50s", row_limit=10,
        catalog="workspace", schema="bcb_gold"
    )
    while response.status.state.value in {"PENDING", "RUNNING"}:
        time.sleep(2)
        response = client.statement_execution.get_statement(response.statement_id)
    if response.status.state.value != "SUCCEEDED":
        detail = (
            response.status.error.message
            if response.status.error
            else response.status.state.value
        )
        raise RuntimeError(f"{label}: {detail}")
    print(f"OK {label}")


def validate(client, warehouse_id, definition):
    """Valida as consultas SQL e os datasets do dashboard."""
    for filename in ("economic_indicators.sql", "data_quality.sql"):
        for number, statement in enumerate(file_queries(ROOT / "sql" / filename), start=1):
            execute(client, warehouse_id, f"{filename} #{number}", statement)
    for dataset in definition["datasets"]:
        execute(client, warehouse_id, dataset["name"], "".join(dataset["queryLines"]))


def deploy(client, warehouse_id, definition):
    """Cria ou atualiza o rascunho do dashboard."""
    serialized = json.dumps(definition, ensure_ascii=False)
    existing = next((item for item in client.lakeview.list() if item.display_name == NAME), None)
    dashboard = Dashboard(display_name=NAME, warehouse_id=warehouse_id,
                          serialized_dashboard=serialized)
    if existing:
        result = client.lakeview.update(existing.dashboard_id, dashboard,
                                        dataset_catalog="workspace", dataset_schema="bcb_gold")
        action = "Atualizado"
    else:
        result = client.lakeview.create(dashboard, dataset_catalog="workspace",
                                        dataset_schema="bcb_gold")
        action = "Criado"
    host = client.config.host.rstrip("/")
    print(f"{action}: {host}/sql/dashboardsv3/{result.dashboard_id}")


def main():
    """Processa argumentos e executa validação ou implantação."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    definition = json.loads(DEFINITION.read_text(encoding="utf-8"))
    client = WorkspaceClient(profile="DEFAULT")
    selected = warehouse(client)
    validate(client, selected.id, definition)
    if not args.validate_only:
        deploy(client, selected.id, definition)


if __name__ == "__main__":
    main()
