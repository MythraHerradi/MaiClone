# MaiClone

MaiClone helps you build a personal chat clone from your Instagram archive.

The repository contains:
- a Python CLI to extract training examples and run LoRA fine-tuning;
- a lightweight frontend (`index.html`) to prepare parameters locally.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

From `/home/runner/work/MaiClone/MaiClone`:

```bash
uv sync
```

If you want model training support, install training extras:

```bash
uv sync --extra train
```

## Instagram archive format

MaiClone expects your extracted Instagram archive to contain thread files under:

`messages/inbox/**/message_*.json`

Example:

```text
instagram_export/
└── messages/
    └── inbox/
        └── some_thread_id/
            └── message_1.json
```

## CLI usage

The project exposes a `maiclone` command with two subcommands:
- `prepare`: build JSONL training examples from your archive
- `train`: prepare data and run LoRA fine-tuning

### 1) Prepare training examples

```bash
maiclone prepare \
  --archive /absolute/path/to/instagram_export \
  --target-name "Your Instagram Name" \
  --output data/training.jsonl
```

What it does:
- reads all `message_*.json` files from your archive;
- extracts prompt/response pairs where `target-name` is the response author;
- writes JSONL rows with `prompt`, `response`, and `context`.

### 2) Train a LoRA adapter

```bash
maiclone train \
  --archive /absolute/path/to/instagram_export \
  --target-name "Your Instagram Name" \
  --base-model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --output-dir models/maiclone \
  --epochs 1 \
  --batch-size 1
```

Output:
- adapter files are saved in `models/maiclone/adapter` (or your selected output directory).

## Frontend usage

This frontend is static and does not require a backend server.

- Open `/home/runner/work/MaiClone/MaiClone/index.html` in your browser.
- `index.html`: configure prepare/train parameters locally.
- `index1.html`: generate a local `.json` report file.

## Run tests

From `/home/runner/work/MaiClone/MaiClone`:

```bash
python -m unittest discover -s tests
```

## Project structure

```text
src/maiclone/cli.py         # CLI entrypoint (prepare/train)
src/maiclone/instagram.py   # Archive loading and example building
src/maiclone/train.py       # JSONL export and LoRA training logic
tests/test_instagram.py     # Core parsing/example tests
index.html                  # Main frontend page
index1.html                 # Local report page
v0/, v1/                    # Frontend assets
```

## Troubleshooting

- `Could not find Instagram inbox folder...`  
  Check that `--archive` points to the root of your extracted Instagram export.

- `No message_*.json files found...`  
  Confirm your export includes message threads and that files are not nested in an unexpected directory.

- `Training dependencies are missing...`  
  Install extras with `uv sync --extra train`.
