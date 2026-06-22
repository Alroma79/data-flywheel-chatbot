"""Integration tests for feedback clustering and human-approved prompt drafts."""

from app.db import SessionLocal
from app.models import ChatbotConfig
from app.recommendations import classify_feedback


def _negative_feedback(test_client, mock_llm, prompt: str, comment: str):
    chat = test_client.post(
        "/api/v1/chat",
        json={"message": prompt},
    ).json()
    response = test_client.post(
        "/api/v1/feedback",
        json={
            "message": chat["reply"],
            "response_id": chat["assistant_message_id"],
            "user_feedback": "thumbs_down",
            "comment": comment,
        },
    )
    assert response.status_code == 201
    return chat


def test_feedback_classifier_uses_explainable_themes():
    assert classify_feedback("This answer is too long and wordy")["key"] == "verbosity"
    assert classify_feedback("It omitted the operational risks")["key"] == "incomplete"
    assert classify_feedback("The factual claim is incorrect")["key"] == "accuracy"
    assert classify_feedback("I simply disliked it")["key"] == "other"


def test_generate_clusters_recurring_negative_feedback(test_client, mock_llm):
    first = _negative_feedback(
        test_client,
        mock_llm,
        "Summarize the deployment plan",
        "This was too long and verbose",
    )
    _negative_feedback(
        test_client,
        mock_llm,
        "Explain the rollback process",
        "The answer was wordy; make it shorter",
    )

    response = test_client.post("/api/v1/recommendations/generate?min_count=2")
    assert response.status_code == 200
    recommendations = response.json()
    assert len(recommendations) == 1
    recommendation = recommendations[0]
    assert recommendation["theme_key"] == "verbosity"
    assert recommendation["status"] == "pending"
    assert recommendation["source_config_id"] == first["config_id"]
    assert len(recommendation["source_feedback_ids"]) == 2
    assert len(recommendation["evidence_examples"]) == 2
    assert "Keep responses concise" in (
        recommendation["proposed_config_json"]["system_prompt"]
    )


def test_generation_is_idempotent_for_pending_theme(test_client, mock_llm):
    for index in range(2):
        _negative_feedback(
            test_client,
            mock_llm,
            f"Prompt {index}",
            "This response is unclear and confusing",
        )

    first = test_client.post("/api/v1/recommendations/generate?min_count=2").json()
    second = test_client.post("/api/v1/recommendations/generate?min_count=2").json()

    assert len(first) == 1
    assert len(second) == 1
    assert first[0]["id"] == second[0]["id"]
    assert len(test_client.get("/api/v1/recommendations").json()) == 1


def test_approval_creates_inactive_configuration_draft(test_client, mock_llm):
    for index in range(2):
        _negative_feedback(
            test_client,
            mock_llm,
            f"Accuracy prompt {index}",
            "This answer is incorrect and contains a factual error",
        )
    recommendation = test_client.post(
        "/api/v1/recommendations/generate?min_count=2"
    ).json()[0]

    approved = test_client.post(
        f"/api/v1/recommendations/{recommendation['id']}/approve",
        json={"configuration_name": "Accuracy improvement draft"},
    )
    assert approved.status_code == 200
    result = approved.json()
    assert result["status"] == "approved"
    assert result["resulting_config_id"] > 0

    db = SessionLocal()
    try:
        draft = (
            db.query(ChatbotConfig)
            .filter(ChatbotConfig.id == result["resulting_config_id"])
            .one()
        )
        assert draft.name == "Accuracy improvement draft"
        assert draft.is_active is False
        assert "recommendation-draft" in draft.tags
        assert "Prioritize factual accuracy" in draft.config_json["system_prompt"]
    finally:
        db.close()

    regenerated = test_client.post("/api/v1/recommendations/generate?min_count=2")
    assert regenerated.status_code == 200
    assert regenerated.json() == []
    assert len(test_client.get("/api/v1/recommendations").json()) == 1


def test_dismissal_preserves_evidence_without_creating_config(test_client, mock_llm):
    for index in range(2):
        _negative_feedback(
            test_client,
            mock_llm,
            f"Relevance prompt {index}",
            "This was irrelevant and off topic",
        )
    recommendation = test_client.post(
        "/api/v1/recommendations/generate?min_count=2"
    ).json()[0]

    dismissed = test_client.post(
        f"/api/v1/recommendations/{recommendation['id']}/dismiss"
    )
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"
    assert dismissed.json()["resulting_config_id"] is None


def test_single_negative_item_does_not_generate_by_default(test_client, mock_llm):
    _negative_feedback(
        test_client,
        mock_llm,
        "One-off prompt",
        "This response is too long",
    )

    response = test_client.post("/api/v1/recommendations/generate")
    assert response.status_code == 200
    assert response.json() == []
