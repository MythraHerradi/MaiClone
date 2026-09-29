from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).parent.resolve()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/health":
            self.send_json(200, {"ok": True})
            return

        file_path = ROOT / (urlparse(self.path).path.lstrip("/") or "index.html")
        if file_path.is_file() and ROOT in file_path.parents:
            content_type = "text/html; charset=utf-8"
            if file_path.suffix == ".css":
                content_type = "text/css; charset=utf-8"
            elif file_path.suffix == ".js":
                content_type = "text/javascript; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(file_path.read_bytes())
            return

        self.send_error(404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/run":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            if self.headers.get_content_type() == "multipart/form-data":
                data, archive = self.parse_upload(body)
                with tempfile.TemporaryDirectory(prefix="maiclone-") as directory:
                    archive_root = self.extract_archive(archive, Path(directory))
                    self.run_command(data, archive_root)
            else:
                self.run_command(json.loads(body), None)
        except (KeyError, TypeError, ValueError, zipfile.BadZipFile) as error:
            self.send_json(400, {"ok": False, "output": str(error)})

    def parse_upload(self, body: bytes) -> tuple[dict[str, str], bytes]:
        content_type = self.headers.get("Content-Type", "")
        message = BytesParser(policy=policy.default).parsebytes(
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + body
        )
        fields: dict[str, str] = {}
        archive = b""
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if name == "archive":
                archive = part.get_payload(decode=True) or b""
            elif name:
                fields[name] = part.get_content()
        if not archive:
            raise ValueError("Sélectionne un fichier ZIP Instagram")
        return fields, archive

    @staticmethod
    def extract_archive(archive: bytes, directory: Path) -> Path:
        zip_path = directory / "instagram.zip"
        zip_path.write_bytes(archive)
        with zipfile.ZipFile(zip_path) as zip_file:
            root = directory.resolve()
            for member in zip_file.infolist():
                destination = (directory / member.filename).resolve()
                if not destination.is_relative_to(root):
                    raise ValueError("Le ZIP contient un chemin non sécurisé")
            zip_file.extractall(directory)

        candidates = [
            directory,
            *[path for path in directory.iterdir() if path.is_dir()],
        ]
        for candidate in candidates:
            if (candidate / "messages" / "inbox").is_dir():
                return candidate
        raise ValueError("Le ZIP ne contient pas messages/inbox")

    def run_command(self, data: dict[str, object], archive: Path | None) -> None:
        command = self.build_command(data, archive)
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )
        self.send_json(
            200,
            {
                "ok": result.returncode == 0,
                "output": (result.stdout + result.stderr).strip(),
                "command": " ".join(command),
            },
        )

    @staticmethod
    def build_command(
        data: dict[str, object], archive: Path | None = None
    ) -> list[str]:
        action = data.get("action")
        archive_value = (
            str(data.get("archive", "")).strip() if archive is None else str(archive)
        )
        target_name = str(data.get("targetName", "")).strip()
        if action not in {"prepare", "train"}:
            raise ValueError("Action inconnue")
        if not archive_value or not target_name:
            raise ValueError("L'archive ZIP et le nom cible sont obligatoires")

        command = [
            sys.executable,
            "-m",
            "maiclone.cli",
            str(action),
            "--archive",
            archive_value,
            "--target-name",
            target_name,
        ]
        if action == "prepare":
            command.extend(["--output", str(data.get("output", "data/training.jsonl"))])
        else:
            command.extend(
                [
                    "--base-model",
                    str(data.get("baseModel", "")).strip(),
                    "--output-dir",
                    str(data.get("outputDir", "models/maiclone")),
                    "--epochs",
                    str(data.get("epochs", 1)),
                    "--batch-size",
                    str(data.get("batchSize", 1)),
                ]
            )
        return command

    def send_json(self, status: int, data: dict[str, object]) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(format % args)


if __name__ == "__main__":
    print("MaiClone: http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
