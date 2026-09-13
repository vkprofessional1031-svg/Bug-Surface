"""FastAPI backend exposing the agent pipeline, eval results, and memory
store over HTTP for the custom frontend to consume."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from orchestrator.graph import run_pipeline
from memory.store import _get_collection

app = FastAPI(title="Autonomous Dev Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    repo_path: str
    issue_text: str
    target_file: str
    test_cmd: str = "pytest -q"


@app.get("/api/results")
def get_results():
    path = Path("eval/results.csv")
    if not path.exists():
        return {"results": [], "success_rate": None, "avg_attempts": None}
    df = pd.read_csv(path)
    success_rate = round(df["success"].mean() * 100)
    avg_attempts = round(df[df["success"]]["attempts"].mean(), 1)
    return {
        "results": df.to_dict(orient="records"),
        "success_rate": success_rate,
        "avg_attempts": avg_attempts,
    }


@app.get("/api/memory")
def get_memory():
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return {"count": 0, "items": []}
    all_items = collection.get()
    items = []
    for doc_id, doc, meta in zip(all_items["ids"], all_items["documents"], all_items["metadatas"]):
        items.append({
            "id": doc_id,
            "issue_text": meta["issue_text"],
            "review_reasoning": meta["review_reasoning"],
            "diff": doc,
            "derived_from": meta.get("derived_from") or None,
        })
    return {"count": count, "items": items}


@app.post("/api/run")
def run_agent(req: RunRequest):
    result = run_pipeline(
        repo_path=req.repo_path,
        issue_text=req.issue_text,
        target_files=[req.target_file],
        issue_name=f"live_run_{hash(req.issue_text) % 10000}",
        test_cmd=req.test_cmd,
    )
    if result["success"]:
        return {
            "success": True,
            "attempts": result["attempts"],
            "diff": result["diff"],
            "plan": result["plan"].model_dump(),
            "review_reasoning": result["review"].reasoning,
            "used_memory": result.get("used_memory", False),
            "memory_source": result.get("memory_source"),
        }
    return {
        "success": False,
        "attempts": result["attempts"],
        "last_feedback": result["last_feedback"],
    }


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/", StaticFiles(directory="dashboard/static", html=True), name="static")
