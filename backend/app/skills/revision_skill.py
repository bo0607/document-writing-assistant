from typing import Any

from app.skills.base import WritingSkill


class RevisionSkill(WritingSkill):
    name = "revision"
    description = "Revise, polish, rewrite, expand, or shorten a draft."

    TYPE_NAMES = {
        "polish": "润色",
        "rewrite": "改写",
        "expand": "扩写",
        "shorten": "缩写",
        "correct": "纠错",
        "custom": "按要求修改",
    }

    def execute(
        self, context: dict[str, Any], instruction: str | None = None
    ) -> str:
        instruction = instruction or ""
        revision_type = context.get("revisionType") or "polish"
        draft = context.get("draft", {}).get("content", "")
        prompt = self._build_prompt(draft, revision_type, instruction)
        content = self.call_model(
            "You are a Chinese text revision assistant. Output only revised text.",
            prompt,
            temperature=0.55,
            max_tokens=2600,
        )
        if content:
            return self.assembler.normalize_paragraphs(content)
        return self._fallback(draft, revision_type, instruction)

    def _build_prompt(self, draft: str, revision_type: str, instruction: str) -> str:
        action = self.TYPE_NAMES.get(revision_type, "修改")
        return (
            f"请对下面的中文正文进行{action}。\n\n"
            f"用户要求：{instruction or '保持原意，提升表达质量'}\n\n"
            "要求：保留核心观点，保持段落完整，不输出解释说明。\n\n"
            f"原文：\n{draft}"
        )

    def _fallback(self, draft: str, revision_type: str, instruction: str) -> str:
        text = self.assembler.normalize_paragraphs(draft)
        if revision_type == "expand":
            return (
                text
                + "\n\n进一步来看，这一主题还需要联系具体情境进行理解。"
                "当写作者能够把观点、材料和个人思考结合起来时，文章就不只是简单陈述，"
                "而能够呈现出更清晰的逻辑层次和更真实的表达力量。"
            )
        if revision_type == "shorten":
            paragraphs = [p for p in text.split("\n\n") if p.strip()]
            return "\n\n".join(paragraphs[: max(1, len(paragraphs) // 2)])
        if revision_type == "rewrite":
            return (
                "换一种表达方式来看，"
                + text.replace("总的来说，", "归根结底，").replace("可以", "能够")
            )
        if revision_type == "correct":
            return text.replace("  ", " ").replace("，，", "，").replace("。。", "。")
        return text.replace("。", "。\n\n", 1).strip()

