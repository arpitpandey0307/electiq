"""
Timeline Router — Serves election timeline milestone data.
"""

import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

DATA_PATH = Path(__file__).parent.parent / "data" / "timeline.json"


@router.get("/api/timeline")
async def get_timeline():
    """Return election timeline milestones."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
