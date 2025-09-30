import os, json
from sqlalchemy import text
from backend.app.db import Base, engine

# 1) Create all tables
Base.metadata.create_all(bind=engine)

# 2) Ensure there is one active chatbot_config
cfg = {"model": "gpt-4o-mini", "temperature": 0.2}
with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO chatbot_config (name, config_json, is_active, tags, created_at)
        SELECT :n, :j, 1, :t, CURRENT_TIMESTAMP
        WHERE NOT EXISTS (SELECT 1 FROM chatbot_config WHERE is_active=1)
    """), {"n": "default", "j": json.dumps(cfg), "t": json.dumps(["default"])})
print("✅ DB ready: tables created and default config ensured.")
