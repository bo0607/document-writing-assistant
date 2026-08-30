import json
from typing import Any

from app.skills.base import WritingSkill


class OutlineSkill(WritingSkill):
    name = "outline"
    description = "Generate a structured writing outline."

    def execute(
        self, context: dict[str, Any], instruction: str | None = None
    ) -> dict[str, Any]:
        requirement = context.get("requirement", {})
        prompt = self._build_prompt(requirement)
        content = self.call_model(
            "You are a Chinese document outline planner. Return valid JSON only.",
            prompt,
            temperature=0.6,
            max_tokens=1200,
        )
        if content:
            parsed = self.assembler.parse_json_object(content)
            if parsed:
                return self._normalize(parsed, requirement)
        return self._fallback(requirement)

    def _build_prompt(self, requirement: dict[str, Any]) -> str:
        return (
            "Generate an outline for the following Chinese writing task. "
            "Return JSON with keys: title, thesis, sections. sections must be "
            "an array of objects with heading and points.\n\n"
            f"Requirement:\n{json.dumps(requirement, ensure_ascii=False, indent=2)}"
        )

    def _normalize(
        self, parsed: dict[str, Any], requirement: dict[str, Any]
    ) -> dict[str, Any]:
        fallback = self._fallback(requirement)
        title = parsed.get("title") or fallback["title"]
        thesis = parsed.get("thesis") or parsed.get("centralIdea") or fallback["thesis"]
        sections = parsed.get("sections") or fallback["sections"]
        if not isinstance(sections, list):
            sections = fallback["sections"]
        normalized_sections = []
        for index, section in enumerate(sections, start=1):
            if isinstance(section, dict):
                heading = section.get("heading") or section.get("title") or f"第{index}段"
                points = section.get("points") or section.get("items") or []
            else:
                heading = f"第{index}段"
                points = [str(section)]
            if isinstance(points, str):
                points = [points]
            normalized_sections.append({"heading": heading, "points": points})
        return {"title": title, "thesis": thesis, "sections": normalized_sections}

    def _fallback(self, requirement: dict[str, Any]) -> dict[str, Any]:
        topic = requirement.get("topic") or "自拟主题"
        genre = requirement.get("genre") or "议论文"
        if "说明" in genre:
            sections = [
                {"heading": "从身边现象切入", "points": ["交代说明对象", "建立具体场景"]},
                {"heading": "说清关键特点", "points": ["说明主要特征", "列举典型表现"]},
                {"heading": "联系实际影响", "points": ["分析现实价值", "说明影响意义"]},
                {"heading": "留下清晰认识", "points": ["回应主题", "补充理性判断"]},
            ]
            thesis = f"围绕{topic}进行清晰说明，帮助读者形成准确理解。"
        elif "记叙" in genre:
            sections = [
                {"heading": "事情如何开始", "points": ["交代时间、地点和人物", "引出事件"]},
                {"heading": "经历中的细节", "points": ["描写事件经过", "突出细节"]},
                {"heading": "真正的转折", "points": ["呈现关键冲突或转折", "表达真实感受"]},
                {"heading": "留下的感受", "points": ["点明收获", "回到主题"]},
            ]
            thesis = f"通过与{topic}相关的具体经历表达感悟。"
        else:
            sections = [
                {"heading": "从真实变化谈起", "points": ["引出话题", "提出中心判断"]},
                {"heading": "看见实际价值", "points": ["分析积极意义", "结合现实例子"]},
                {"heading": "把问题想得更完整", "points": ["指出需要注意的问题", "体现辩证思考"]},
                {"heading": "回到可做的事", "points": ["回应观点", "提出行动建议"]},
            ]
            thesis = f"{topic}具有重要现实意义，但也需要理性认识和正确运用。"
        return {
            "title": topic,
            "thesis": thesis,
            "sections": sections,
        }
