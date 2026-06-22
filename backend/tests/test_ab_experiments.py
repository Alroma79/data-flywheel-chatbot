"""Integration tests for weighted, sticky configuration experiments."""

from sqlalchemy import event

from app.db import engine
from app.db import SessionLocal
from app.experiments import choose_weighted_variant
from app.models import ChatbotConfig, Experiment


def _add_variant(name: str, prompt: str) -> int:
    db = SessionLocal()
    try:
        config = ChatbotConfig(
            name=name,
            config_json={
                "system_prompt": prompt,
                "model": "gpt-4o",
                "temperature": 0.2,
            },
            is_active=True,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config.id
    finally:
        db.close()


def _create_active_experiment(test_client, variants, name="Prompt comparison"):
    created = test_client.post(
        "/api/v1/experiments",
        json={"name": name, "variants": variants},
    )
    assert created.status_code == 201, created.text
    experiment_id = created.json()["id"]
    activated = test_client.post(f"/api/v1/experiments/{experiment_id}/activate")
    assert activated.status_code == 200, activated.text
    return activated.json()


def test_active_experiment_routes_new_session_and_sticks(test_client, mock_llm):
    concise_id = _add_variant("Concise", "Answer concisely.")
    detailed_id = _add_variant("Detailed", "Answer with detail.")
    experiment = _create_active_experiment(
        test_client,
        [
            {"config_id": concise_id, "weight": 50},
            {"config_id": detailed_id, "weight": 50},
        ],
    )

    first = test_client.post(
        "/api/v1/chat",
        json={"message": "First turn"},
    ).json()
    second = test_client.post(
        "/api/v1/chat",
        json={"message": "Second turn", "session_id": first["session_id"]},
    ).json()

    assert first["experiment_id"] == experiment["id"]
    assert first["experiment_name"] == experiment["name"]
    assert first["config_id"] in {concise_id, detailed_id}
    assert second["config_id"] == first["config_id"]
    assert second["experiment_id"] == first["experiment_id"]


def test_weighted_assignment_is_deterministic_and_tracks_target_split():
    experiment = Experiment(
        id=42,
        name="Weighted",
        status="active",
        variants=[
            {"config_id": 10, "weight": 70},
            {"config_id": 20, "weight": 30},
        ],
    )

    first = choose_weighted_variant(experiment, "same-session")
    assert choose_weighted_variant(experiment, "same-session") == first

    assignments = [
        choose_weighted_variant(experiment, f"session-{index}")
        for index in range(1000)
    ]
    first_share = assignments.count(10) / len(assignments)
    assert 0.65 <= first_share <= 0.75


def test_activating_experiment_pauses_previous_experiment(test_client):
    first_id = _add_variant("First A", "First A")
    second_id = _add_variant("First B", "First B")
    third_id = _add_variant("Second A", "Second A")
    fourth_id = _add_variant("Second B", "Second B")

    first = _create_active_experiment(
        test_client,
        [
            {"config_id": first_id, "weight": 50},
            {"config_id": second_id, "weight": 50},
        ],
        name="First experiment",
    )
    second = _create_active_experiment(
        test_client,
        [
            {"config_id": third_id, "weight": 50},
            {"config_id": fourth_id, "weight": 50},
        ],
        name="Second experiment",
    )

    experiments = test_client.get("/api/v1/experiments").json()
    states = {experiment["id"]: experiment["status"] for experiment in experiments}
    assert states[first["id"]] == "paused"
    assert states[second["id"]] == "active"


def test_experiment_analytics_include_attributed_feedback(test_client, mock_llm):
    variant_a = _add_variant("Variant A", "Use approach A.")
    variant_b = _add_variant("Variant B", "Use approach B.")
    experiment = _create_active_experiment(
        test_client,
        [
            {"config_id": variant_a, "weight": 50},
            {"config_id": variant_b, "weight": 50},
        ],
    )
    chat = test_client.post(
        "/api/v1/chat",
        json={"message": "Evaluate this experiment"},
    ).json()
    feedback = test_client.post(
        "/api/v1/feedback",
        json={
            "message": chat["reply"],
            "response_id": chat["assistant_message_id"],
            "user_feedback": "thumbs_up",
        },
    )
    assert feedback.status_code == 201

    analytics = test_client.get("/api/v1/analytics/experiments")
    assert analytics.status_code == 200
    result = analytics.json()[0]
    assert result["experiment_id"] == experiment["id"]
    attributed = next(
        variant
        for variant in result["variants"]
        if variant["config_id"] == chat["config_id"]
    )
    assert attributed["sessions"] == 1
    assert attributed["rated_responses"] == 1
    assert attributed["approval_rate"] == 1.0


def test_experiment_rejects_invalid_or_inactive_variants(test_client):
    active_id = _add_variant("Active variant", "Active")
    response = test_client.post(
        "/api/v1/experiments",
        json={
            "name": "Invalid experiment",
            "variants": [
                {"config_id": active_id, "weight": 50},
                {"config_id": 999999, "weight": 50},
            ],
        },
    )
    assert response.status_code == 400


def test_active_configuration_list_is_json_serializable(test_client):
    response = test_client.get("/api/v1/configs?active_only=true&size=100")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["created_at"]


def test_new_session_skips_sticky_assignment_history_query(test_client, mock_llm):
    sticky_assignment_queries = []

    def capture_select(_conn, _cursor, statement, _parameters, _context, _many):
        normalized = " ".join(statement.lower().split())
        if (
            normalized.startswith("select")
            and "from chat_history" in normalized
            and "chat_history.session_id =" in normalized
            and "chat_history.config_id is not null" in normalized
        ):
            sticky_assignment_queries.append(normalized)

    event.listen(engine, "before_cursor_execute", capture_select)
    try:
        response = test_client.post(
            "/api/v1/chat",
            json={"message": "Start a new routed session"},
        )
    finally:
        event.remove(engine, "before_cursor_execute", capture_select)

    assert response.status_code == 200
    assert sticky_assignment_queries == []


def test_config_creation_rejects_non_numeric_temperature(test_client):
    response = test_client.post(
        "/api/v1/configs",
        json={
            "name": "Invalid temperature",
            "config_json": {
                "system_prompt": "Be helpful.",
                "model": "gpt-4o",
                "temperature": None,
            },
            "is_active": True,
        },
    )

    assert response.status_code == 422
