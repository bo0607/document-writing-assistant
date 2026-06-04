import json
import re
from typing import Any


class ResultAssembler:
    """Normalizes model output into the structures used by the writing kernel."""

    def clean_text(self, content: str) -> str:
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content.strip()

    def parse_json_object(self, content: str) -> dict[str, Any] | None:
        cleaned = self.clean_text(content)
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        try:
            value = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.S)
            if not match:
                return None
            try:
                value = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return value if isinstance(value, dict) else None

    def normalize_paragraphs(self, content: str) -> str:
        lines = [line.strip() for line in self.clean_text(content).splitlines()]
        paragraphs = [line for line in lines if line]
        return "\n\n".join(paragraphs)
