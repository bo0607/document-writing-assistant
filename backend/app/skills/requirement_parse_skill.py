import json
import re
from typing import Any

from app.skills.base import WritingSkill


class RequirementParseSkill(WritingSkill):
    name = "requirement_parse"
    description = "Parse raw writing input into structured requirement fields."

    def execute(
        self, context: dict[str, Any], instruction: str | None = None
    ) -> dict[str, Any]:
        raw_input = context.get("input", {})
        prompt = self._build_prompt(raw_input)
        content = self.call_model(
            "You are a Chinese writing requirement parser. Return valid JSON only.",
            prompt,
            temperature=0.2,
            max_tokens=800,
        )
        if content:
            parsed = self.assembler.parse_json_object(content)
            if parsed:
                return self._normalize(parsed, raw_input)
        return self._fallback(raw_input)

    def _build_prompt(self, raw_input: dict[str, Any]) -> str:
        return (
            "Please extract the writing requirement from this user input and "
            "return JSON with keys: topic, genre, wordCount, style, audience, "
            "extraInstruction, inferredFields.\n\n"
            f"Input:\n{json.dumps(raw_input, ensure_ascii=False, indent=2)}"
        )

    def _fallback(self, raw_input: dict[str, Any]) -> dict[str, Any]:
        text = str(raw_input.get("prompt") or raw_input.get("topic") or "").strip()
        word_count = raw_input.get("wordCount") or raw_input.get("word_count")
        if not word_count:
            match = re.search(r"(\d{2,5})\s*字", text)
            word_count = int(match.group(1)) if match else 800
        genre = raw_input.get("genre") or self._guess_genre(text)
        topic = raw_input.get("topic") or self._guess_topic(text) or "自拟主题"
        style = raw_input.get("style") or "正式、自然、结构清晰"
        audience = raw_input.get("audience") or "普通读者"
        extra = raw_input.get("extraInstruction") or raw_input.get("extra") or text
        return {
            "topic": topic,
            "genre": genre,
            "wordCount": int(word_count),
            "style": style,
            "audience": audience,
            "extraInstruction": extra,
            "inferredFields": [
                key
                for key, value in {
                    "genre": raw_input.get("genre"),
                    "wordCount": raw_input.get("wordCount"),
                    "style": raw_input.get("style"),
                    "audience": raw_input.get("audience"),
                }.items()
                if not value
            ],
        }

    def _normalize(
        self, parsed: dict[str, Any], raw_input: dict[str, Any]
    ) -> dict[str, Any]:
        fallback = self._fallback(raw_input)
        merged = {**fallback, **{k: v for k, v in parsed.items() if v not in (None, "")}}
        try:
            merged["wordCount"] = int(merged.get("wordCount") or fallback["wordCount"])
        except (TypeError, ValueError):
            merged["wordCount"] = fallback["wordCount"]
        merged.setdefault("inferredFields", fallback["inferredFields"])
        return merged

    def _guess_genre(self, text: str) -> str:
        genres = ["议论文", "说明文", "记叙文", "应用文", "报告", "总结", "通知"]
        for genre in genres:
            if genre in text:
                return genre
        return "议论文"

    def _guess_topic(self, text: str) -> str:
        patterns = [
            r"以[《\"]?(.+?)[》\"]?为题",
            r"主题[是为：: ]+(.+)",
            r"题目[是为：: ]+(.+)",
            r"写一篇(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip(" 。.，,")
        return text[:40].strip(" 。.，,") if text else ""

