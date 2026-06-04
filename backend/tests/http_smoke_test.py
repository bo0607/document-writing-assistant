import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import ApiHandler


def request_json(base_url: str, method: str, path: str, payload: dict | None = None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        method=method,
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def request_text(base_url: str, path: str) -> str:
    with urllib.request.urlopen(f"{base_url}{path}", timeout=20) as response:
        return response.read().decode("utf-8")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"

    try:
        page = request_text(base_url, "/")
        assert "文档智能写作助手" in page
        script = request_text(base_url, "/static/app.js")
        assert "/api/task/run-full" in script

        health = request_json(base_url, "GET", "/api/health")
        assert health["success"] is True

        task = request_json(
            base_url,
            "POST",
            "/api/task/run-full",
            {
                "topic": "人工智能对学习方式的影响",
                "genre": "议论文",
                "wordCount": 800,
                "style": "正式、逻辑清晰",
                "extraInstruction": "观点积极，结合现实例子",
            },
        )
        assert task["success"] is True
        task_id = task["data"]["taskId"]
        assert task["data"]["status"] == "draft_generated"
        assert task["data"]["draft"]["content"]

        saved = request_json(
            base_url,
            "POST",
            "/api/draft/update",
            {
                "taskId": task_id,
                "content": task["data"]["draft"]["content"] + "\n\n这是一次手动保存验证。",
            },
        )
        assert saved["success"] is True
        assert saved["data"]["status"] == "revised"

        revised = request_json(
            base_url,
            "POST",
            "/api/text/revise",
            {
                "taskId": task_id,
                "revisionType": "polish",
                "instruction": "语言更自然",
            },
        )
        assert revised["success"] is True
        assert revised["data"]["status"] == "revised"

        exported = request_json(
            base_url,
            "POST",
            "/api/document/export",
            {
                "taskId": task_id,
                "format": "docx",
            },
        )
        assert exported["success"] is True
        export_path = Path(exported["data"]["file"]["path"])
        assert export_path.exists()

        print(
            json.dumps(
                {
                    "success": True,
                    "taskId": task_id,
                    "exportPath": str(export_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
