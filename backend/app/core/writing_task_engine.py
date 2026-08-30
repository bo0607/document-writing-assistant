from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.core.context_binder import ContextBinder
from app.core.model_adapter import ModelAdapter
from app.core.result_assembler import ResultAssembler
from app.core.skill_registry import SkillRegistry
from app.core.task_state import TaskStatus, ensure_transition
from app.exporter.document_exporter import DocumentExporter
from app.storage.task_store import TaskStore
from app.storage.model_config_store import ModelConfigStore


class WritingTaskEngine:
    """Lightweight document-writing task kernel."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.store = TaskStore(data_dir / "tasks")
        self.context = ContextBinder(self.store)
        self.assembler = ResultAssembler()
        self.model_config = ModelConfigStore(data_dir)
        self._reload_model()
        self.exporter = DocumentExporter(data_dir / "exports")

    def get_model_config(self) -> dict[str, Any]:
        return self.model_config.public_config(self.model)

    def configure_model(self, data: dict[str, Any]) -> dict[str, Any]:
        current = self.model_config.load()["remote"]
        base_url = str(data.get("baseUrl", "")).strip()
        model = str(data.get("model", "")).strip()
        api_key = str(data.get("apiKey", "")).strip() or current["apiKey"]

        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("请输入有效的模型接口地址")
        if not model:
            raise ValueError("请输入模型名称")
        if not api_key:
            raise ValueError("请输入 API Key")

        self.model_config.save_remote(base_url, api_key, model)
        self._reload_model()
        return self.get_model_config()

    def use_local_model(self) -> dict[str, Any]:
        self.model_config.use_local_mode()
        self._reload_model()
        return self.get_model_config()

    def test_model_connection(self) -> dict[str, Any]:
        if not self.model.remote_enabled:
            raise ValueError("请先保存完整的远程模型配置")
        result = self.model.complete(
            [{"role": "user", "content": "请只回复：连接成功"}],
            temperature=0,
            max_tokens=32,
        )
        if not result.success:
            detail = (result.error or "未知错误").replace("\n", " ")[:300]
            raise ValueError(f"模型连接失败：{detail}")
        return {
            "message": "模型连接成功",
            "preview": result.content[:120],
            "model": self.model.model,
        }

    def create_task(self, input_data: dict[str, Any]) -> dict[str, Any]:
        context = self.context.create_context(input_data)
        return self._public_context(context)

    def parse_requirement(self, task_id: str) -> dict[str, Any]:
        context = self.context.get_context(task_id)
        ensure_transition(context["status"], TaskStatus.REQUIREMENT_PARSED.value)
        requirement = self.skills.get("requirement_parse").execute(context)
        context = self.context.update_requirement(
            task_id,
            requirement,
            TaskStatus.REQUIREMENT_PARSED.value,
        )
        return self._public_context(context)

    def generate_outline(self, task_id: str) -> dict[str, Any]:
        context = self._ensure_requirement(task_id)
        ensure_transition(context["status"], TaskStatus.OUTLINE_GENERATED.value)
        outline = self.skills.get("outline").execute(context)
        context = self.context.update_outline(
            task_id,
            outline,
            TaskStatus.OUTLINE_GENERATED.value,
        )
        return self._public_context(context)

    def generate_draft(self, task_id: str) -> dict[str, Any]:
        context = self._ensure_outline(task_id)
        ensure_transition(context["status"], TaskStatus.DRAFT_GENERATED.value)
        draft = self.skills.get("draft").execute(context)
        context = self.context.update_draft(
            task_id,
            draft,
            TaskStatus.DRAFT_GENERATED.value,
        )
        return self._public_context(context)

    def revise_text(
        self,
        task_id: str,
        revision_type: str = "polish",
        instruction: str = "",
    ) -> dict[str, Any]:
        context = self.context.get_context(task_id)
        if context["status"] not in {
            TaskStatus.DRAFT_GENERATED.value,
            TaskStatus.REVISED.value,
        }:
            raise ValueError("Draft must be generated before revision")
        ensure_transition(context["status"], TaskStatus.REVISING.value)
        context["revisionType"] = revision_type
        self.context.update_status(task_id, TaskStatus.REVISING.value)
        before = context.get("draft", {}).get("content", "")
        revised = self.skills.get("revision").execute(context, instruction)
        context = self.context.add_revision(
            task_id,
            revision_type,
            instruction,
            before,
            revised,
        )
        return self._public_context(context)

    def update_draft(self, task_id: str, content: str) -> dict[str, Any]:
        context = self.context.get_context(task_id)
        if context["status"] not in {
            TaskStatus.DRAFT_GENERATED.value,
            TaskStatus.REVISED.value,
            TaskStatus.EXPORTED.value,
        }:
            raise ValueError("Draft must be generated before manual update")
        context = self.context.update_draft(
            task_id,
            content,
            TaskStatus.REVISED.value,
        )
        return self._public_context(context)

    def summarize(self, task_id: str) -> dict[str, Any]:
        context = self.context.get_context(task_id)
        summary = self.skills.get("summary").execute(context)
        context = self.context.update_summary(task_id, summary)
        return self._public_context(context)

    def export_document(self, task_id: str, file_format: str = "docx") -> dict[str, Any]:
        context = self.context.get_context(task_id)
        if context["status"] not in {
            TaskStatus.DRAFT_GENERATED.value,
            TaskStatus.REVISED.value,
            TaskStatus.EXPORTED.value,
        }:
            raise ValueError("Draft must be generated before export")
        file_info = self.exporter.export(context, file_format)
        context = self.context.add_export(task_id, file_info)
        return {"task": self._public_context(context), "file": file_info}

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self._public_context(self.context.get_context(task_id))

    def list_tasks(self) -> list[dict[str, Any]]:
        return self.store.list_tasks()

    def run_full(self, input_data: dict[str, Any]) -> dict[str, Any]:
        task = self.create_task(input_data)
        task_id = task["taskId"]
        self.parse_requirement(task_id)
        self.generate_outline(task_id)
        return self.generate_draft(task_id)

    def _ensure_requirement(self, task_id: str) -> dict[str, Any]:
        context = self.context.get_context(task_id)
        if context["status"] == TaskStatus.CREATED.value:
            self.parse_requirement(task_id)
            context = self.context.get_context(task_id)
        return context

    def _ensure_outline(self, task_id: str) -> dict[str, Any]:
        context = self._ensure_requirement(task_id)
        if context["status"] == TaskStatus.REQUIREMENT_PARSED.value:
            self.generate_outline(task_id)
            context = self.context.get_context(task_id)
        return context

    def _public_context(self, context: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in context.items() if key != "revisionType"}

    def _reload_model(self) -> None:
        config = self.model_config.get_effective_config()
        self.model = ModelAdapter(**config) if config is not None else ModelAdapter()
        self.skills = SkillRegistry(self.model, self.assembler)
