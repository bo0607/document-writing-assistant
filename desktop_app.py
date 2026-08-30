"""Windows desktop launcher for the document writing assistant."""

import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).resolve().parent

BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import webview

from app.main import ApiHandler


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    window = webview.create_window(
        "文档智能写作助手",
        f"http://127.0.0.1:{port}",
        width=1440,
        height=920,
        min_size=(1024, 680),
    )
    window.events.closed += lambda *_: server.shutdown()
    webview.start()
    server.server_close()


if __name__ == "__main__":
    main()
