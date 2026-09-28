from __future__ import annotations

import json
from pathlib import Path


def save_examples_jsonl(examples: list[dict[str, str]], output_file: str | Path) -> Path:
    destination = Path(output_file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for row in examples:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return destination


def fine_tune_lora(
    examples: list[dict[str, str]],
    base_model: str,
    output_dir: str | Path,
    epochs: int = 1,
    batch_size: int = 1,
    learning_rate: float = 2e-4,
) -> Path:
    """Fine-tune a conversational model using LoRA on personal chat examples."""
    try:
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
    except ImportError as error:
        raise RuntimeError(
            "Training dependencies are missing. Install with: uv sync --extra train"
        ) from error

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(base_model)
    lora = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)

    rows = [
        {
            "text": f"User: {item['prompt']}\nMe: {item['response']}\n",
        }
        for item in examples
    ]
    dataset = Dataset.from_list(rows)

    def tokenize(batch: dict) -> dict:
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=512,
            padding="max_length",
        )

    tokenized = dataset.map(tokenize, batched=True)
    args = TrainingArguments(
        output_dir=str(out_path),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        learning_rate=learning_rate,
        fp16=False,
        logging_steps=10,
        save_strategy="epoch",
        report_to=[],
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()

    model.save_pretrained(str(out_path / "adapter"))
    tokenizer.save_pretrained(str(out_path / "adapter"))
    return out_path / "adapter"
