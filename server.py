from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).parent.resolve()
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "MythraHerradi")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "MaiClone")


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
        path = urlparse(self.path).path
        if path == "/api/run":
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
            return

        if path == "/api/report":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                data = json.loads(body or b"{}")
                issue_number = self.create_github_issue(data)
                self.send_json(
                    200,
                    {
                        "ok": True,
                        "output": "Issue créée avec succès.",
                        "issueNumber": issue_number,
                    },
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                self.send_json(400, {"ok": False, "output": str(error)})
            except RuntimeError as error:
                self.send_json(502, {"ok": False, "output": str(error)})
            return

        self.send_error(404)

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
    def create_github_issue(data: dict[str, object]) -> int:
        title = str(data.get("title", "")).strip()
        details = str(data.get("details", "")).strip()
        issue_type = str(data.get("type", "")).strip() or "other"
        email = str(data.get("email", "")).strip() or "Non fourni"
        context = data.get("context") if isinstance(data.get("context"), dict) else {}
        page = str(context.get("page", "inconnu")).strip() or "inconnu"
        referrer = str(context.get("referrer", "Aucun")).strip() or "Aucun"
        user_agent = str(context.get("userAgent", "inconnu")).strip() or "inconnu"
        language = str(context.get("language", "inconnue")).strip() or "inconnue"
        sent_at = str(context.get("sentAt", "inconnu")).strip() or "inconnu"

        if not title or not details:
            raise ValueError("Le titre et les détails sont obligatoires")

        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if not token:
            raise RuntimeError("Le serveur n'est pas configuré: GITHUB_TOKEN manquant")

        issue_title = f"[Bug] {title}"
        issue_body = "\n".join(
            [
                "## Type",
                issue_type,
                "",
                "## Détails",
                details,
                "",
                "## Contact",
                email,
                "",
                "## Contexte",
                f"- Page: {page}",
                f"- Referrer: {referrer}",
                f"- User agent: {user_agent}",
                f"- Langue: {language}",
                f"- Horodatage: {sent_at}",
            ]
        )
        payload = json.dumps({"title": issue_title, "body": issue_body}).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues",
            data=payload,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
                "User-Agent": "MaiClone-Error-Reporter",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                issue = json.loads(response.read().decode("utf-8"))
                number = issue.get("number")
                if not isinstance(number, int):
                    raise RuntimeError("Réponse GitHub invalide")
                return number
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub a refusé la création d'issue ({error.code}): {details}"
            ) from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"Impossible de joindre GitHub: {error.reason}") from error

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
