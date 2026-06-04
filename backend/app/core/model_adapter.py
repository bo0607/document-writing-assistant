import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class ModelResponse:
    success: bool
    content: str
    usage: dict[str, Any] | None = None
    error: str | None = None


class ModelAdapter:
    """OpenAI-compatible model adapter with an offline demo fallback."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 60,
    ):
        self.base_url = (
            base_url
            or os.getenv("WRITING_ASSISTANT_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or ""
        ).strip()
        self.api_key = (
            api_key
            or os.getenv("WRITING_ASSISTANT_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        ).strip()
        self.model = (
            model
            or os.getenv("WRITING_ASSISTANT_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-4o-mini"
        )
        self.timeout = timeout

    @property
    def remote_enabled(self) -> bool:
        return bool(self.base_url and self.api_key)

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> ModelResponse:
        if not self.remote_enabled:
            return ModelResponse(
                success=False,
                content="",
                error="Remote model is not configured; using local demo mode.",
            )

        endpoint = self.base_url.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint = f"{endpoint}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            return ModelResponse(False, "", error=f"HTTP {exc.code}: {detail}")
        except Exception as exc:
            return ModelResponse(False, "", error=str(exc))

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return ModelResponse(False, "", error="Unexpected model response shape")

        return ModelResponse(
            success=True,
            content=content.strip(),
            usage=body.get("usage"),
            error=None,
        )

