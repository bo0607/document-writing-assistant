import json
from typing import Any

from app.skills.base import WritingSkill


class DraftSkill(WritingSkill):
    name = "draft"
    description = "Compose a full draft from requirement and outline."

    def execute(
        self, context: dict[str, Any], instruction: str | None = None
    ) -> str:
        requirement = context.get("requirement", {})
        outline = context.get("outline", {})
        prompt = self._build_prompt(requirement, outline)
        content = self.call_model(
            "You are a Chinese document drafting assistant. Output only the draft.",
            prompt,
            temperature=0.75,
            max_tokens=2600,
        )
        if content:
            return self.assembler.normalize_paragraphs(content)
        return self._fallback(requirement, outline)

    def _build_prompt(
        self, requirement: dict[str, Any], outline: dict[str, Any]
    ) -> str:
        return (
            "Write a complete Chinese draft according to the requirement and "
            "outline. Keep paragraphs coherent and close to target length.\n\n"
            f"Requirement:\n{json.dumps(requirement, ensure_ascii=False, indent=2)}\n\n"
            f"Outline:\n{json.dumps(outline, ensure_ascii=False, indent=2)}"
        )

    def _fallback(self, requirement: dict[str, Any], outline: dict[str, Any]) -> str:
        topic = requirement.get("topic") or "自拟主题"
        style = requirement.get("style") or "正式、自然、结构清晰"
        title = outline.get("title") or f"{topic}之我见"
        thesis = outline.get("thesis") or f"{topic}值得我们认真思考。"
        sections = outline.get("sections") or []
        paragraphs = [title, thesis]
        for section in sections:
            heading = section.get("heading", "正文")
            points = section.get("points", [])
            point_text = "，".join(str(point) for point in points) or "展开具体分析"
            paragraphs.append(
                f"{heading}方面，围绕{topic}，可以从{point_text}等角度展开。"
                f"在实际写作中，需要保持{style}的表达，使观点与材料相互支撑。"
                f"这一部分既要说明现象，也要联系现实，让文章内容更加充实。"
            )
        paragraphs.append(
            f"总的来说，{topic}并不是一个孤立的话题，而是与现实生活和个人成长密切相关。"
            "只有在理解其价值的同时保持理性判断，才能真正把文章观点落到实处。"
        )
        return "\n\n".join(paragraphs)

