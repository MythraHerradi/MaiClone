from __future__ import annotations

import json
from pathlib import Path


def load_instagram_threads(archive_path: str | Path) -> list[dict]:
    """Load all Instagram message thread JSON files from an archive folder."""
    root = Path(archive_path)
    inbox_path = root / "messages" / "inbox"
    if not inbox_path.exists():
        raise FileNotFoundError(
            f"Could not find Instagram inbox folder at: {inbox_path}"
        )

    threads: list[dict] = []
    for message_file in sorted(inbox_path.rglob("message_*.json")):
        with message_file.open("r", encoding="utf-8") as handle:
            thread = json.load(handle)
            thread["_source_file"] = str(message_file)
            threads.append(thread)

    if not threads:
        raise ValueError("No message_*.json files found in Instagram archive")

    return threads


def build_training_examples(
    threads: list[dict],
    target_name: str,
    min_chars: int = 2,
) -> list[dict[str, str]]:
    """Create chat prompt/response examples where `target_name` is the response."""
    examples: list[dict[str, str]] = []

    for thread in threads:
        messages = thread.get("messages", [])
        ordered = list(reversed(messages))

        for index in range(1, len(ordered)):
            previous_message = ordered[index - 1]
            current_message = ordered[index]

            current_sender = current_message.get("sender_name")
            current_text = (current_message.get("content") or "").strip()
            previous_sender = previous_message.get("sender_name")
            previous_text = (previous_message.get("content") or "").strip()

            if current_sender != target_name:
                continue
            if previous_sender == target_name:
                continue
            if len(current_text) < min_chars or len(previous_text) < min_chars:
                continue

            examples.append(
                {
                    "prompt": previous_text,
                    "response": current_text,
                    "context": thread.get("title", "Instagram chat"),
                }
            )

    if not examples:
        raise ValueError(
            "No training examples found. Check target_name and archive content."
        )

    return examples
