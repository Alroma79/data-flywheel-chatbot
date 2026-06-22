"""Integration tests for response attribution and flywheel analytics."""

from sqlalchemy import create_engine, inspect, text

from app.migrations.add_flywheel_attribution import run_migration


def test_feedback_is_attributed_to_response_and_config(test_client, mock_llm):
    chat_response = test_client.post(
        "/api/v1/chat",
        json={"message": "How should this response be evaluated?"},
    )

    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    assert chat_data["assistant_message_id"] > 0
    assert chat_data["config_id"] > 0
    assert chat_data["model"] == "gpt-4o"

    feedback_response = test_client.post(
        "/api/v1/feedback",
        json={
            "message": chat_data["reply"],
            "response_id": chat_data["assistant_message_id"],
            "user_feedback": "thumbs_up",
            "comment": "Relevant and clear",
        },
    )

    assert feedback_response.status_code == 201

    feedback_entries = test_client.get("/api/v1/feedback").json()
    assert feedback_entries[0]["response_id"] == chat_data["assistant_message_id"]
    assert feedback_entries[0]["config_id"] == chat_data["config_id"]


def test_configuration_analytics_and_negative_examples(test_client, mock_llm):
    positive_chat = test_client.post(
        "/api/v1/chat",
        json={"message": "Give me a concise answer"},
    ).json()
    negative_chat = test_client.post(
        "/api/v1/chat",
        json={"message": "Explain the deployment tradeoffs"},
    ).json()

    test_client.post(
        "/api/v1/feedback",
        json={
            "message": positive_chat["reply"],
            "response_id": positive_chat["assistant_message_id"],
            "user_feedback": "thumbs_up",
        },
    )
    test_client.post(
        "/api/v1/feedback",
        json={
            "message": negative_chat["reply"],
            "response_id": negative_chat["assistant_message_id"],
            "user_feedback": "thumbs_down",
            "comment": "It omitted the operational risks",
        },
    )

    analytics_response = test_client.get("/api/v1/analytics/configurations")
    assert analytics_response.status_code == 200
    metrics = analytics_response.json()[0]
    assert metrics["total_responses"] == 2
    assert metrics["rated_responses"] == 2
    assert metrics["positive_feedback"] == 1
    assert metrics["negative_feedback"] == 1
    assert metrics["approval_rate"] == 0.5
    assert metrics["feedback_coverage"] == 1.0

    negative_response = test_client.get("/api/v1/analytics/negative-feedback")
    assert negative_response.status_code == 200
    example = negative_response.json()[0]
    assert example["response_id"] == negative_chat["assistant_message_id"]
    assert example["prompt"] == "Explain the deployment tradeoffs"
    assert example["comment"] == "It omitted the operational risks"
    assert example["config_id"] == negative_chat["config_id"]


def test_feedback_rejects_unknown_assistant_response(test_client):
    response = test_client.post(
        "/api/v1/feedback",
        json={
            "message": "Unknown response",
            "response_id": 999999,
            "user_feedback": "thumbs_down",
        },
    )

    assert response.status_code == 404


def test_attribution_migration_upgrades_existing_database(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE chatbot_config "
                "(id INTEGER PRIMARY KEY, name VARCHAR(100))"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE chat_history "
                "(id INTEGER PRIMARY KEY, role VARCHAR(20), content TEXT)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE feedback "
                "(id INTEGER PRIMARY KEY, message TEXT, user_feedback VARCHAR(50))"
            )
        )

    applied = run_migration(engine)

    assert "chat_history.config_id" in applied
    assert "feedback.response_id" in applied
    assert {
        "config_id",
        "model_name",
        "latency_ms",
    }.issubset(
        {column["name"] for column in inspect(engine).get_columns("chat_history")}
    )
    assert {"response_id", "config_id"}.issubset(
        {column["name"] for column in inspect(engine).get_columns("feedback")}
    )
