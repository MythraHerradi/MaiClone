from __future__ import annotations

import argparse

from .instagram import build_training_examples, load_instagram_threads
from .train import fine_tune_lora, save_examples_jsonl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maiclone",
        description="Create an AI chat clone from an Instagram archive",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="extract training examples")
    prepare.add_argument("--archive", required=True, help="Path to Instagram archive root")
    prepare.add_argument("--target-name", required=True, help="Your exact sender_name")
    prepare.add_argument("--output", default="data/training.jsonl", help="JSONL output path")

    train = subparsers.add_parser("train", help="prepare data and run LoRA fine-tuning")
    train.add_argument("--archive", required=True, help="Path to Instagram archive root")
    train.add_argument("--target-name", required=True, help="Your exact sender_name")
    train.add_argument("--base-model", required=True, help="Hugging Face model id")
    train.add_argument("--output-dir", default="models/maiclone", help="Model output directory")
    train.add_argument("--epochs", type=int, default=1)
    train.add_argument("--batch-size", type=int, default=1)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    threads = load_instagram_threads(args.archive)
    examples = build_training_examples(threads=threads, target_name=args.target_name)

    if args.command == "prepare":
        destination = save_examples_jsonl(examples, args.output)
        print(f"Saved {len(examples)} examples to {destination}")
        return

    adapter_dir = fine_tune_lora(
        examples=examples,
        base_model=args.base_model,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
    print(f"Finished fine-tuning. Adapter saved in: {adapter_dir}")


if __name__ == "__main__":
    main()
