"""Add response/configuration attribution columns for the data flywheel."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _add_column(engine: Engine, table: str, name: str, definition: str) -> bool:
    columns = {column["name"] for column in inspect(engine).get_columns(table)}
    if name in columns:
        return False

    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
    return True


def run_migration(engine: Engine) -> list[str]:
    """Apply additive, backward-compatible attribution columns."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    applied: list[str] = []

    if "chat_history" in tables:
        chat_columns = {
            "config_id": "INTEGER",
            "model_name": "VARCHAR(100)",
            "latency_ms": "INTEGER",
        }
        for name, definition in chat_columns.items():
            if _add_column(engine, "chat_history", name, definition):
                applied.append(f"chat_history.{name}")

    if "feedback" in tables:
        feedback_columns = {
            "response_id": "INTEGER",
            "config_id": "INTEGER",
        }
        for name, definition in feedback_columns.items():
            if _add_column(engine, "feedback", name, definition):
                applied.append(f"feedback.{name}")

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_chat_history_config_id ON chat_history (config_id)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_feedback_response_id ON feedback (response_id)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_feedback_config_id ON feedback (config_id)"
            )
        )

    return applied
