import json
from pathlib import Path
from typing import Any


class TaskStore:
    """Small JSON-file task store for the first implementation stage."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, task_id: str) -> Path:
        if not task_id or any(ch in task_id for ch in "\\/:*?\"<>|"):
            raise ValueError("Invalid task id")
        return self.root_dir / f"{task_id}.json"

    def save(self, task_id: str, data: dict[str, Any]) -> None:
        path = self._path_for(task_id)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self, task_id: str) -> dict[str, Any]:
        path = self._path_for(task_id)
        if not path.exists():
            raise FileNotFoundError(f"Task not found: {task_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def exists(self, task_id: str) -> bool:
        return self._path_for(task_id).exists()

    def list_tasks(self) -> list[dict[str, Any]]:
        tasks = []
        for path in sorted(self.root_dir.glob("*.json"), reverse=True):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            tasks.append(
                {
                    "taskId": item.get("taskId"),
                    "status": item.get("status"),
                    "topic": item.get("requirement", {}).get("topic")
                    or item.get("input", {}).get("topic"),
                    "updatedAt": item.get("updatedAt"),
                }
            )
        return tasks

