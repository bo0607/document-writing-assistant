import json
from pathlib import Path
from typing import Any


class ModelConfigStore:
    """Stores one local model connection configuration outside version control."""

    def __init__(self, data_dir: Path):
        self.path = data_dir / "model_config.json"

    def load(self) -> dict[str, Any]:
        default = {"mode": "environment", "remote": {}}
        if not self.path.exists():
            return default

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

        if not isinstance(data, dict):
            return default

        mode = data.get("mode")
        if mode not in {"environment", "remote", "local"}:
            mode = "environment"
        remote = data.get("remote") if isinstance(data.get("remote"), dict) else {}
        return {
            "mode": mode,
            "remote": {
                "baseUrl": str(remote.get("baseUrl", "")).strip(),
                "apiKey": str(remote.get("apiKey", "")).strip(),
                "model": str(remote.get("model", "")).strip(),
            },
        }

    def save_remote(self, base_url: str, api_key: str, model: str) -> dict[str, Any]:
        config = self.load()
        config["mode"] = "remote"
        config["remote"] = {
            "baseUrl": base_url.strip(),
            "apiKey": api_key.strip(),
            "model": model.strip(),
        }
        self._write(config)
        return config

    def use_local_mode(self) -> dict[str, Any]:
        config = self.load()
        config["mode"] = "local"
        self._write(config)
        return config

    def get_effective_config(self) -> dict[str, str] | None:
        config = self.load()
        if config["mode"] == "environment":
            return None
        if config["mode"] == "local":
            return {"base_url": "", "api_key": "", "model": ""}

        remote = config["remote"]
        return {
            "base_url": remote["baseUrl"],
            "api_key": remote["apiKey"],
            "model": remote["model"],
        }

    def public_config(self, model_adapter: Any) -> dict[str, Any]:
        config = self.load()
        remote = config["remote"]
        if config["mode"] == "environment":
            return {
                "mode": "environment",
                "baseUrl": model_adapter.base_url,
                "model": model_adapter.model,
                "apiKeyConfigured": bool(model_adapter.api_key),
                "remoteEnabled": model_adapter.remote_enabled,
            }
        return {
            "mode": config["mode"],
            "baseUrl": remote["baseUrl"],
            "model": remote["model"],
            "apiKeyConfigured": bool(remote["apiKey"]),
            "remoteEnabled": model_adapter.remote_enabled,
        }

    def _write(self, config: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
