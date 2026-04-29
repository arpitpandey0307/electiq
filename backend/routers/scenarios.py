"""
Scenarios Router — Serves what-if scenario decision trees.
"""

import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

DATA_PATH = Path(__file__).parent.parent / "data" / "scenarios.json"


@router.get("/api/scenarios")
async def get_scenarios():
    """Return all what-if scenarios."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@router.get("/api/glossary")
async def get_glossary():
    """Return glossary of election terms."""
    glossary_path = Path(__file__).parent.parent / "data" / "glossary.json"
    with open(glossary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
