from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.task_state import TaskStatus
from app.storage.task_store import TaskStore


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ContextBinder:
    """Manages the current document-writing task context."""

    def __init__(self, store: TaskStore):
        self.store = store

    def create_context(self, input_data: dict[str, Any]) -> dict[str, Any]:
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
        timestamp = now_text()
        context = {
            "taskId": task_id,
            "status": TaskStatus.CREATED.value,
            "input": input_data,
            "requirement": {},
            "outline": {},
            "draft": {"content": "", "version": 0},
            "summary": "",
            "revisions": [],
            "exports": [],
            "createdAt": timestamp,
            "updatedAt": timestamp,
        }
        self.store.save(task_id, context)
        return context

    def get_context(self, task_id: str) -> dict[str, Any]:
        return self.store.load(task_id)

    def save_context(self, context: dict[str, Any]) -> dict[str, Any]:
        context["updatedAt"] = now_text()
        self.store.save(context["taskId"], context)
        return context

    def update_status(self, task_id: str, status: str) -> dict[str, Any]:
        context = self.get_context(task_id)
        context["status"] = status
        return self.save_context(context)

    def update_requirement(
        self, task_id: str, requirement: dict[str, Any], status: str
    ) -> dict[str, Any]:
        context = self.get_context(task_id)
        context["requirement"] = requirement
        context["status"] = status
        return self.save_context(context)

    def update_outline(
        self, task_id: str, outline: dict[str, Any], status: str
    ) -> dict[str, Any]:
        context = self.get_context(task_id)
        context["outline"] = outline
        context["status"] = status
        return self.save_context(context)

    def update_draft(self, task_id: str, content: str, status: str) -> dict[str, Any]:
        context = self.get_context(task_id)
        current_version = int(context.get("draft", {}).get("version", 0))
        context["draft"] = {
            "content": content,
            "version": current_version + 1,
        }
        context["status"] = status
        return self.save_context(context)

    def update_summary(self, task_id: str, summary: str) -> dict[str, Any]:
        context = self.get_context(task_id)
        context["summary"] = summary
        return self.save_context(context)

    def add_revision(
        self,
        task_id: str,
        revision_type: str,
        instruction: str,
        before_content: str,
        after_content: str,
    ) -> dict[str, Any]:
        context = self.get_context(task_id)
        before_version = int(context.get("draft", {}).get("version", 0))
        context.setdefault("revisions", []).append(
            {
                "revisionType": revision_type,
                "instruction": instruction,
                "beforeVersion": before_version,
                "afterVersion": before_version + 1,
                "beforePreview": before_content[:120],
                "afterPreview": after_content[:120],
                "createdAt": now_text(),
            }
        )
        context["draft"] = {
            "content": after_content,
            "version": before_version + 1,
        }
        context["status"] = TaskStatus.REVISED.value
        return self.save_context(context)

    def add_export(self, task_id: str, file_info: dict[str, Any]) -> dict[str, Any]:
        context = self.get_context(task_id)
        context.setdefault("exports", []).append(file_info)
        context["status"] = TaskStatus.EXPORTED.value
        return self.save_context(context)
