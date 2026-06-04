from typing import Any

from app.skills.base import WritingSkill


class SummarySkill(WritingSkill):
    name = "summary"
    description = "Generate a concise summary for a draft."

    def execute(
        self, context: dict[str, Any], instruction: str | None = None
    ) -> str:
        draft = context.get("draft", {}).get("content", "")
        prompt = (
            "请为下面的中文正文生成一段 100 字以内摘要。"
            "只输出摘要，不要输出解释。\n\n"
            f"正文：\n{draft}"
        )
        content = self.call_model(
            "You are a Chinese summarization assistant.",
            prompt,
            temperature=0.4,
            max_tokens=400,
        )
        if content:
            return self.assembler.clean_text(content)
        clean = self.assembler.clean_text(draft)
        return clean[:100] + ("..." if len(clean) > 100 else "")
