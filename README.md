# MaiClone

créer un clone de sois meme avec des archives de ses conversation sur les resaux sociaux

A UV-ready Python project that turns your Instagram archive into training data and fine-tunes a chat model to mirror your tone, expressions, and language mix.

## Quick start

```bash
uv venv
uv sync
```

## Build dataset from your Instagram archive

```bash
uv run maiclone prepare \
  --archive /path/to/instagram-archive \
  --target-name "Your Instagram Name" \
  --output data/training.jsonl
```

## Fine-tune with LoRA

Install training deps once:

```bash
uv sync --extra train
```

Then train:

```bash
uv run maiclone train \
  --archive /path/to/instagram-archive \
  --target-name "Your Instagram Name" \
  --base-model "microsoft/Phi-3-mini-4k-instruct" \
  --output-dir models/maiclone
```

This keeps your archive format unchanged and extracts conversational examples where your messages become the target style for the model.
