# backend/app/demo_seed.py
"""
Demo seeding utilities.

This is intentionally minimal for CI:
- No DB writes by default.
- Safe to import even if DB isn't configured.
"""

import os
from typing import Any

async def seed_demo(app: Any) -> None:
    """
    Hook to pre-populate demo configs or seed data.
    Called by app startup when DEMO_MODE=1 (or ENV=demo) in your code.
    It's a no-op by default so CI doesn't need a DB.
    """
    # Example (disabled): create default config rows using app.state.db
    # db = getattr(app.state, "db", None)
    # if db:
    #     await db.create_default_config(...)
    if os.getenv("CI") == "true":
        # Keep CI logs tidy
        return
    # You can log that seeding is skipped in non-local runs if you like.
    return
