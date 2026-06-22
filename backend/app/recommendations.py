"""Deterministic negative-feedback clustering and prompt recommendations."""

from collections import defaultdict
from copy import deepcopy
import re

from sqlalchemy.orm import Session

from .models import ChatHistory, ChatbotConfig, Feedback


THEMES = (
    {
        "key": "verbosity",
        "title": "Make responses more concise",
        "keywords": (
            "too long", "verbose", "wordy", "rambling", "shorter",
            "concise", "too much detail",
        ),
        "instruction": (
            "Keep responses concise and prioritize the direct answer. "
            "Remove repetition and include only details that materially help the user."
        ),
    },
    {
        "key": "incomplete",
        "title": "Cover missing details",
        "keywords": (
            "missing", "omitted", "incomplete", "not enough", "lacks",
            "left out", "didn't include", "did not include",
        ),
        "instruction": (
            "Check that the response addresses every part of the request. "
            "State assumptions, important tradeoffs, and concrete next steps when relevant."
        ),
    },
    {
        "key": "accuracy",
        "title": "Improve factual accuracy",
        "keywords": (
            "wrong", "incorrect", "inaccurate", "hallucinated", "made up",
            "false", "factual error",
        ),
        "instruction": (
            "Prioritize factual accuracy. Do not invent facts; clearly identify uncertainty "
            "and distinguish verified information from assumptions."
        ),
    },
    {
        "key": "clarity",
        "title": "Improve clarity and structure",
        "keywords": (
            "unclear", "confusing", "vague", "hard to understand",
            "poorly explained", "disorganized",
        ),
        "instruction": (
            "Use plain language and a clear structure. Define necessary terms and make the "
            "reasoning easy to follow without unnecessary jargon."
        ),
    },
    {
        "key": "relevance",
        "title": "Stay focused on the request",
        "keywords": (
            "irrelevant", "off topic", "off-topic", "didn't answer",
            "did not answer", "not relevant", "missed the question",
        ),
        "instruction": (
            "Answer the user's actual request before adding context. Avoid tangents and "
            "explicitly connect each recommendation to the question asked."
        ),
    },
    {
        "key": "sources",
        "title": "Strengthen source use",
        "keywords": (
            "source", "citation", "evidence", "reference", "unsupported",
        ),
        "instruction": (
            "When using supplied knowledge, cite the relevant source and avoid claims that "
            "are not supported by the available context."
        ),
    },
    {
        "key": "tone",
        "title": "Adjust response tone",
        "keywords": (
            "rude", "tone", "unprofessional", "patronizing", "dismissive",
            "too casual", "too formal",
        ),
        "instruction": (
            "Use a respectful, professional tone calibrated to the user's language and level "
            "of expertise. Be direct without sounding dismissive."
        ),
    },
    {
        "key": "latency",
        "title": "Reduce response latency",
        "keywords": (
            "slow", "too long to respond", "latency", "took too long",
        ),
        "instruction": (
            "Prefer an efficient answer structure and avoid unnecessary expansion. Lead with "
            "the useful result so the response can complete quickly."
        ),
    },
)

OTHER_THEME = {
    "key": "other",
    "title": "Review uncategorized failures",
    "instruction": (
        "Before answering, verify that the response is accurate, relevant, clear, and complete. "
        "Address the request directly and avoid unsupported assumptions."
    ),
}


def classify_feedback(text: str) -> dict:
    """Assign one primary, explainable theme using transparent keyword rules."""
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    for theme in THEMES:
        if any(keyword in normalized for keyword in theme["keywords"]):
            return theme
    return OTHER_THEME


def _prompts_for_responses(
    db: Session,
    responses: list[ChatHistory],
) -> dict[int, str | None]:
    session_ids = {response.session_id for response in responses if response.session_id}
    prompts_by_session = defaultdict(list)
    if session_ids:
        messages = (
            db.query(ChatHistory)
            .filter(
                ChatHistory.session_id.in_(session_ids),
                ChatHistory.role == "user",
            )
            .order_by(ChatHistory.session_id, ChatHistory.id.desc())
            .all()
        )
        for message in messages:
            prompts_by_session[message.session_id].append(message)

    return {
        response.id: next(
            (
                message.content
                for message in prompts_by_session.get(response.session_id, [])
                if message.id < response.id
            ),
            None,
        )
        for response in responses
    }


def collect_negative_feedback_clusters(
    db: Session,
    limit: int = 200,
) -> list[dict]:
    """Cluster recent negative feedback by source configuration and failure theme."""
    rows = (
        db.query(Feedback, ChatHistory, ChatbotConfig)
        .outerjoin(ChatHistory, Feedback.response_id == ChatHistory.id)
        .outerjoin(ChatbotConfig, Feedback.config_id == ChatbotConfig.id)
        .filter(Feedback.user_feedback == "thumbs_down")
        .order_by(Feedback.timestamp.desc())
        .limit(limit)
        .all()
    )
    prompts = _prompts_for_responses(
        db,
        [response for _, response, _ in rows if response is not None],
    )
    clusters = {}
    for feedback, response, config in rows:
        classification_text = " ".join(
            value
            for value in (
                feedback.comment,
                prompts.get(response.id) if response else None,
            )
            if value
        )
        theme = classify_feedback(classification_text)
        key = (feedback.config_id, theme["key"])
        cluster = clusters.setdefault(
            key,
            {
                "theme": theme,
                "config_id": feedback.config_id,
                "config_name": config.name if config else "Unattributed",
                "feedback_ids": [],
                "examples": [],
            },
        )
        cluster["feedback_ids"].append(feedback.id)
        if len(cluster["examples"]) < 3:
            cluster["examples"].append(
                {
                    "feedback_id": feedback.id,
                    "prompt": prompts.get(response.id) if response else None,
                    "response": response.content if response else feedback.message,
                    "comment": feedback.comment,
                }
            )
    return sorted(
        clusters.values(),
        key=lambda cluster: (
            len(cluster["feedback_ids"]),
            cluster["theme"]["key"] != "other",
        ),
        reverse=True,
    )


def proposed_configuration(
    source: ChatbotConfig | None,
    theme: dict,
) -> dict:
    """Create a conservative prompt-only proposal from an existing configuration."""
    baseline = deepcopy(source.config_json) if source else {
        "system_prompt": "You are a helpful assistant.",
        "model": "gpt-4o",
        "temperature": 0.7,
    }
    current_prompt = str(baseline.get("system_prompt") or "You are a helpful assistant.").strip()
    instruction = theme["instruction"]
    if instruction not in current_prompt:
        baseline["system_prompt"] = f"{current_prompt}\n\nImprovement instruction: {instruction}"
    return baseline
