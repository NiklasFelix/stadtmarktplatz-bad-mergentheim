"""JSON-basierter Projektspeicher (Stage 1 – kein Datenbankserver nötig)."""

import json
import os
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _project_path(project_id: str) -> Path:
    return DATA_DIR / f"{project_id}.json"


def list_projects() -> list[dict]:
    _ensure_dir()
    projects = []
    for f in sorted(DATA_DIR.glob("*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
            projects.append({
                "id": f.stem,
                "name": data.get("name", f.stem),
                "customer": data.get("customer", ""),
                "updated_at": data.get("updated_at", ""),
            })
        except Exception:
            pass
    return projects


def load_project(project_id: str) -> dict | None:
    path = _project_path(project_id)
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def save_project(project: dict) -> None:
    _ensure_dir()
    project["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path = _project_path(project["id"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)


def delete_project(project_id: str) -> None:
    path = _project_path(project_id)
    if path.exists():
        os.remove(path)


def new_project(name: str, customer: str) -> dict:
    slug = name.lower().replace(" ", "-").replace("/", "-")[:40]
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    project_id = f"{slug}-{ts}"
    return {
        "id": project_id,
        "name": name,
        "customer": customer,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": "",
        "room": {
            "height_m": 4.0,
            "min_aisle_m": 1.0,
            "outline": [
                {"x": 0.0, "y": 0.0},
                {"x": 20.0, "y": 0.0},
                {"x": 20.0, "y": 15.0},
                {"x": 0.0, "y": 15.0},
            ],
            "obstacles": [],
            "openings": [],
        },
        "zones": [],
    }
