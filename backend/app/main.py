import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

if getattr(sys, "frozen", False):
    BACKEND_ROOT = Path(sys._MEIPASS) / "backend"
else:
    BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.writing_task_engine import WritingTaskEngine

if getattr(sys, "frozen", False):
    LOCAL_APP_DATA = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    DATA_DIR = LOCAL_APP_DATA / "DocumentWritingAssistant" / "data"
else:
    DATA_DIR = BACKEND_ROOT / "data"
STATIC_DIR = BACKEND_ROOT / "static"
ENGINE = WritingTaskEngine(DATA_DIR)


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "WritingAssistantHTTP/0.1"

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        try:
            if path == "/api/health":
                self._send_json(
                    {
                        "success": True,
                        "service": "document-writing-assistant",
                        "modelRemoteEnabled": ENGINE.model.remote_enabled,
                    }
                )
            elif path == "/api/model/config":
                self._send_json({"success": True, "data": ENGINE.get_model_config()})
            elif path == "/manifest.webmanifest":
                self._send_static("manifest.webmanifest")
            elif path == "/service-worker.js":
                self._send_static("service-worker.js")
            elif path == "/api/tasks":
                self._send_json({"success": True, "data": ENGINE.list_tasks()})
            elif path == "/api/skills":
                self._send_json({"success": True, "data": ENGINE.skills.list_skills()})
            elif path == "/api/task/detail":
                task_id = self._first(query, "taskId")
                self._send_json({"success": True, "data": ENGINE.get_task(task_id)})
            elif path.startswith("/exports/"):
                self._send_file(path.removeprefix("/exports/"))
            elif path == "/" or path == "/index.html":
                self._send_static("index.html")
            elif path.startswith("/static/"):
                self._send_static(path.removeprefix("/static/"))
            else:
                self._send_json({"success": False, "error": "Not found"}, 404)
        except Exception as exc:
            self._send_json({"success": False, "error": str(exc)}, 400)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        body = self._read_json()
        try:
            if parsed.path == "/api/task/create":
                data = ENGINE.create_task(body)
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/model/config":
                data = ENGINE.configure_model(body)
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/model/test":
                data = ENGINE.test_model_connection()
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/model/local-mode":
                data = ENGINE.use_local_model()
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/task/run-full":
                data = ENGINE.run_full(body)
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/requirement/parse":
                data = ENGINE.parse_requirement(body["taskId"])
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/outline/generate":
                data = ENGINE.generate_outline(body["taskId"])
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/draft/generate":
                data = ENGINE.generate_draft(body["taskId"])
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/draft/update":
                data = ENGINE.update_draft(body["taskId"], body.get("content", ""))
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/text/revise":
                data = ENGINE.revise_text(
                    body["taskId"],
                    body.get("revisionType", "polish"),
                    body.get("instruction", ""),
                )
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/text/summary":
                data = ENGINE.summarize(body["taskId"])
                self._send_json({"success": True, "data": data})
            elif parsed.path == "/api/document/export":
                data = ENGINE.export_document(body["taskId"], body.get("format", "docx"))
                self._send_json({"success": True, "data": data})
            else:
                self._send_json({"success": False, "error": "Not found"}, 404)
        except Exception as exc:
            self._send_json({"success": False, "error": str(exc)}, 400)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, relative_name: str) -> None:
        file_name = Path(unquote(relative_name)).name
        path = DATA_DIR / "exports" / file_name
        if not path.exists():
            self._send_json({"success": False, "error": "File not found"}, 404)
            return
        data = path.read_bytes()
        content_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if path.suffix == ".docx"
            else "text/plain; charset=utf-8"
        )
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header(
            "Content-Disposition",
            f"attachment; filename*=UTF-8''{quote(path.name)}",
        )
        self.end_headers()
        self.wfile.write(data)

    def _send_static(self, relative_name: str) -> None:
        safe_name = unquote(relative_name).replace("\\", "/").lstrip("/")
        target = (STATIC_DIR / safe_name).resolve()
        static_root = STATIC_DIR.resolve()
        if static_root not in target.parents and target != static_root:
            self._send_json({"success": False, "error": "Invalid static path"}, 400)
            return
        if not target.exists() or not target.is_file():
            self._send_json({"success": False, "error": "Static file not found"}, 404)
            return
        data = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if target.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        elif target.suffix == ".webmanifest":
            content_type = "application/manifest+json; charset=utf-8"
        elif target.suffix in {".html", ".css"}:
            content_type = f"{content_type}; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _first(self, query: dict[str, list[str]], key: str) -> str:
        values = query.get(key)
        if not values:
            raise ValueError(f"Missing query parameter: {key}")
        return values[0]

    def log_message(self, format: str, *args) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"Writing assistant backend running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
