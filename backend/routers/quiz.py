"""
Quiz Router — Serves quiz questions by topic.
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()

DATA_PATH = Path(__file__).parent.parent / "data" / "quiz.json"


@router.get("/api/quiz/{topic}")
async def get_quiz(topic: str):
    """Return quiz questions for a given topic."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if topic not in data:
        raise HTTPException(
            status_code=404,
            detail=f"Topic '{topic}' not found. Available: {', '.join(data.keys())}"
        )
    
    return data[topic]


@router.get("/api/quiz")
async def list_quiz_topics():
    """List all available quiz topics."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    topics = []
    for key, value in data.items():
        topics.append({
            "id": key,
            "title": value["title"],
            "icon": value["icon"],
            "question_count": len(value["questions"])
        })
    
    return {"topics": topics}
