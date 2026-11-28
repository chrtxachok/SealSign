"""Serve the SealSign demo on the loopback interface."""

import base64
import json
import logging
import os
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from threading import Lock

from sealsign.inference import MAX_BYTES, Detector, ImageInputError, decode_page
from sealsign.paths import RuntimePaths

logger = logging.getLogger(__name__)
ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/demo.css": ("demo.css", "text/css; charset=utf-8"),
    "/demo.js": ("demo.js", "text/javascript; charset=utf-8"),
    "/sample.png": ("sample.png", "image/png"),
}


class DemoHandler(BaseHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(15)
        super().setup()

    def reply(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data: blob:; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def reply_json(self, status, body):
        self.reply(status, "application/json", json.dumps(body, ensure_ascii=False).encode())

    def check_host(self):
        port = self.server.server_port
        if self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}:
            return True
        self.reply_json(HTTPStatus.FORBIDDEN, {"error": "Используйте локальный адрес."})
        return False

    def do_GET(self):
        if not self.check_host():
            return
        if self.path not in self.server.assets:
            self.reply_json(HTTPStatus.NOT_FOUND, {"error": "Страница не найдена."})
            return
        content_type, body = self.server.assets[self.path]
        self.reply(HTTPStatus.OK, content_type, body)

    def do_POST(self):
        if not self.check_host():
            return
        if self.path != "/analyze":
            self.reply_json(HTTPStatus.NOT_FOUND, {"error": "Страница не найдена."})
            return
        try:
            output = self.analyze()
        except ImageInputError as exc:
            self.reply_json(exc.status, {"error": str(exc)})
            return
        except Exception:
            logger.exception("Ошибка обработки страницы")
            self.reply_json(
                HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Не удалось выполнить анализ."}
            )
            return
        self.reply_json(HTTPStatus.OK, output)

    def analyze(self):
        if self.headers.get("Content-Type") != "application/octet-stream":
            raise ImageInputError(415, "Откройте интерфейс и загрузите JPEG или PNG.")
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError as exc:
            raise ImageInputError(411, "Размер файла неизвестен.") from exc
        if length > MAX_BYTES:
            raise ImageInputError(413, "Файл больше 20 МиБ.")
        if length <= 0:
            raise ImageInputError(422, "Файл пуст.")
        if not self.server.analysis_lock.acquire(blocking=False):
            raise ImageInputError(503, "Идёт анализ другой страницы. Попробуйте ещё раз.")
        try:
            try:
                payload = self.rfile.read(length)
            except TimeoutError as exc:
                raise ImageInputError(408, "Не удалось получить файл вовремя.") from exc
            if len(payload) != length:
                raise ImageInputError(422, "Файл загружен не полностью.")
            page = decode_page(payload)
            prediction = self.server.detector.predict(page)
            with BytesIO() as preview:
                page.save(preview, format="PNG")
                encoded = base64.b64encode(preview.getvalue()).decode("ascii")
            return {"prediction": prediction, "preview_png": encoded}
        finally:
            self.server.analysis_lock.release()


def serve(bundle: Path, port: int, open_browser: bool):
    cache = RuntimePaths.from_env().artifacts / "demo" / "settings"
    if not os.environ.get("YOLO_CONFIG_DIR"):
        cache.mkdir(parents=True, exist_ok=True)
        os.environ["YOLO_CONFIG_DIR"] = str(cache)
    folder = Path(__file__).with_name("demo_assets")
    assets = {
        route: (content_type, (folder / name).read_bytes())
        for route, (name, content_type) in ASSETS.items()
    }
    with ThreadingHTTPServer(("127.0.0.1", port), DemoHandler) as server:
        server.assets = assets
        server.analysis_lock = Lock()
        server.detector = Detector(bundle, device="cpu")
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"SealSign: {url}", flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
