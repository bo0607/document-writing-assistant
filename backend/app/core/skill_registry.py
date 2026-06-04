from typing import Any

from app.core.model_adapter import ModelAdapter
from app.core.result_assembler import ResultAssembler
from app.skills.base import WritingSkill
from app.skills.draft_skill import DraftSkill
from app.skills.outline_skill import OutlineSkill
from app.skills.requirement_parse_skill import RequirementParseSkill
from app.skills.revision_skill import RevisionSkill
from app.skills.summary_skill import SummarySkill


class SkillRegistry:
    """Registers and resolves document-writing skills."""

    def __init__(self, model: ModelAdapter, assembler: ResultAssembler):
        self.model = model
        self.assembler = assembler
        self._skills: dict[str, WritingSkill] = {}
        self.register(RequirementParseSkill(model, assembler))
        self.register(OutlineSkill(model, assembler))
        self.register(DraftSkill(model, assembler))
        self.register(RevisionSkill(model, assembler))
        self.register(SummarySkill(model, assembler))

    def register(self, skill: WritingSkill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> WritingSkill:
        try:
            return self._skills[name]
        except KeyError as exc:
            raise KeyError(f"Skill not registered: {name}") from exc

    def list_skills(self) -> list[dict[str, Any]]:
        return [
            {"name": skill.name, "description": skill.description}
            for skill in self._skills.values()
        ]

