from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from maiclone.instagram import build_training_examples, load_instagram_threads


class InstagramParsingTests(unittest.TestCase):
    def _write_thread(self, base: Path) -> None:
        thread_dir = base / "messages" / "inbox" / "testthread_123"
        thread_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "title": "Friend",
            "messages": [
                {"sender_name": "Me", "content": "I am doing great!"},
                {"sender_name": "Friend", "content": "How are you?"},
                {"sender_name": "Me", "content": "Hey!"},
                {"sender_name": "Friend", "content": "Hi"},
            ],
        }
        (thread_dir / "message_1.json").write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )

    def test_load_threads_and_build_examples(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            self._write_thread(tmp_path)

            threads = load_instagram_threads(tmp_path)
            examples = build_training_examples(threads, target_name="Me")

            self.assertEqual(len(threads), 1)
            self.assertEqual(
                examples,
                [
                    {
                        "prompt": "Hi",
                        "response": "Hey!",
                        "context": "Friend",
                    },
                    {
                        "prompt": "How are you?",
                        "response": "I am doing great!",
                        "context": "Friend",
                    },
                ],
            )


if __name__ == "__main__":
    unittest.main()
