from __future__ import annotations

import http.client
import socket

import sys
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from werkzeug.serving import make_server


BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 5005
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 5173


def _get_project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


PROJECT_ROOT = _get_project_root()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"


class BackendServer:
    def __init__(self) -> None:
        self._server = None
        self._thread = None

    def start(self) -> None:
        if not BACKEND_DIR.exists():
            raise FileNotFoundError(f"未找到后端目录: {BACKEND_DIR}")

        env_file = BACKEND_DIR / ".env"
        if env_file.exists():
            load_dotenv(env_file)

        sys.path.insert(0, str(BACKEND_DIR))
        from app import create_app  # pylint: disable=import-outside-toplevel

        app = create_app()
        self._server = make_server(BACKEND_HOST, BACKEND_PORT, app)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=3)


class FrontendHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIST_DIR), **kwargs)

    def _is_api_path(self) -> bool:
        path = urlsplit(self.path).path
        return path.startswith("/api") or path.startswith("/auth")

    def _proxy_to_backend(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(content_length) if content_length > 0 else None

        conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=90)
        proxy_headers = {
            k: v
            for k, v in self.headers.items()
            if k.lower() not in {"host", "content-length", "connection"}
        }

        try:
            conn.request(self.command, self.path, body=body, headers=proxy_headers)
            response = conn.getresponse()
            payload = response.read()

            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                lk = key.lower()
                if lk in {"transfer-encoding", "connection"}:
                    continue
                self.send_header(key, value)
            self.end_headers()

            if payload:
                self.wfile.write(payload)
        finally:
            conn.close()

    def do_GET(self) -> None:  # noqa: N802
        if self._is_api_path():
            self._proxy_to_backend()
            return

        requested_path = urlsplit(self.path).path
        if requested_path in {"", "/"}:
            self.path = "/index.html"
            return super().do_GET()

        static_file = FRONTEND_DIST_DIR / requested_path.lstrip("/")
        if static_file.exists() and static_file.is_file():
            return super().do_GET()

        self.path = "/index.html"
        return super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if self._is_api_path():
            self._proxy_to_backend()
            return
        return super().do_HEAD()

    def do_POST(self) -> None:  # noqa: N802
        if self._is_api_path():
            self._proxy_to_backend()
            return
        self.send_error(405, "Method Not Allowed")

    def do_PUT(self) -> None:  # noqa: N802
        if self._is_api_path():
            self._proxy_to_backend()
            return
        self.send_error(405, "Method Not Allowed")

    def do_PATCH(self) -> None:  # noqa: N802
        if self._is_api_path():
            self._proxy_to_backend()
            return
        self.send_error(405, "Method Not Allowed")

    def do_DELETE(self) -> None:  # noqa: N802
        if self._is_api_path():
            self._proxy_to_backend()
            return
        self.send_error(405, "Method Not Allowed")

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self._is_api_path():
            self._proxy_to_backend()
            return
        self.send_response(204)
        self.send_header("Allow", "GET, HEAD, OPTIONS")
        self.end_headers()

    def log_message(self, fmt: str, *args) -> None:
        msg = "%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args)
        sys.stdout.write(msg)


class FrontendServer:
    def __init__(self) -> None:
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if not FRONTEND_DIST_DIR.exists():
            raise FileNotFoundError(
                "未找到前端构建产物 frontend/dist，请先执行 `npm run build`。"
            )

        self._server = ThreadingHTTPServer((FRONTEND_HOST, FRONTEND_PORT), FrontendHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=3)


def _wait_for_port(host: str, port: int, timeout_sec: int = 20) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.2)
    return False


def main() -> int:
    print("=" * 70)
    print("  Automatic Email Responder Launcher")
    print(f"  Project root: {PROJECT_ROOT}")
    print("=" * 70)

    backend = BackendServer()
    frontend = FrontendServer()

    try:
        backend.start()
        if not _wait_for_port(BACKEND_HOST, BACKEND_PORT, 20):
            raise RuntimeError("后端启动超时，请检查 backend/.env 配置。")

        frontend.start()
        if not _wait_for_port(FRONTEND_HOST, FRONTEND_PORT, 10):
            raise RuntimeError("前端代理启动超时。")

        url = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"
        print(f"[OK] 后端: http://{BACKEND_HOST}:{BACKEND_PORT}")
        print(f"[OK] 前端: {url}")
        print("[INFO] 按 Ctrl+C 退出。")
        webbrowser.open(url)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] 正在停止服务...")
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[ERROR] 启动失败: {exc}")
        return 1
    finally:
        frontend.stop()
        backend.stop()


if __name__ == "__main__":
    raise SystemExit(main())
