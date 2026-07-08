#!/usr/bin/env python3
"""Fine-tune Whisper with LoRA on TechSpeechBench train metadata.

This script trains on the explicit train metadata only. It does not read the
heldout splits. Use a separate transcription + scoring pass to evaluate the
adapter on the full benchmark.

Examples:
  uv run --group train python scripts/train_whisper_lora.py --dry-run
  uv run --group train python scripts/train_whisper_lora.py
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_TRAIN_METADATA = Path("data/v1-small/train/metadata.jsonl")
DEFAULT_OUTPUT_DIR = Path("results/finetunes/whisper-base-en-lora-v1-small")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a Whisper LoRA adapter.")
    parser.add_argument("--train-metadata", type=Path, default=DEFAULT_TRAIN_METADATA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--base-model", default="openai/whisper-base.en")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--dev-size", type=int, default=8)
    parser.add_argument("--num-train-epochs", type=float, default=20)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=2)
    parser.add_argument("--warmup-steps", type=int, default=10)
    parser.add_argument("--logging-steps", type=int, default=5)
    parser.add_argument("--eval-steps", type=int, default=20)
    parser.add_argument("--save-steps", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--gradient-checkpointing", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned train/dev split and exit before loading the model.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def split_records(
    records: list[dict[str, Any]], dev_size: int, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    if dev_size <= 0:
        return shuffled, []
    if dev_size >= len(shuffled):
        raise ValueError("dev-size must be smaller than the number of train records")
    return shuffled[:-dev_size], shuffled[-dev_size:]


def print_plan(
    records: list[dict[str, Any]],
    train_records: list[dict[str, Any]],
    dev_records: list[dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    print(f"base model: {args.base_model}")
    print(f"metadata: {args.train_metadata}")
    print(f"output dir: {args.output_dir}")
    print(f"records: {len(records)}")
    print(f"train records: {len(train_records)}")
    print(f"dev records: {len(dev_records)}")
    print()
    print("train ids:")
    print(", ".join(record["clip_id"] for record in train_records))
    if dev_records:
        print()
        print("dev ids:")
        print(", ".join(record["clip_id"] for record in dev_records))


def main() -> None:
    args = parse_args()
    records = read_jsonl(args.train_metadata)
    train_records, dev_records = split_records(records, args.dev_size, args.seed)
    print_plan(records, train_records, dev_records, args)

    if args.dry_run:
        print()
        print("dry run only. remove --dry-run to train the adapter.")
        return

    import librosa
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        WhisperForConditionalGeneration,
        WhisperProcessor,
    )

    processor = WhisperProcessor.from_pretrained(
        args.base_model,
        language="english",
        task="transcribe",
    )
    model = WhisperForConditionalGeneration.from_pretrained(args.base_model)
    model.config.forced_decoder_ids = None
    model.config.suppress_tokens = []
    model.config.use_cache = False

    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        target_modules=["q_proj", "v_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    def prepare_record(record: dict[str, Any]) -> dict[str, Any]:
        audio, _ = librosa.load(record["audio"], sr=16000, mono=True)
        features = processor.feature_extractor(
            audio,
            sampling_rate=16000,
            return_tensors="pt",
        ).input_features[0]
        labels = processor.tokenizer(record["text"]).input_ids
        return {
            "input_features": features,
            "labels": labels,
            "clip_id": record["clip_id"],
        }

    train_dataset = Dataset.from_list(train_records).map(
        prepare_record,
        remove_columns=list(train_records[0].keys()),
    )
    eval_dataset = None
    if dev_records:
        eval_dataset = Dataset.from_list(dev_records).map(
            prepare_record,
            remove_columns=list(dev_records[0].keys()),
        )

    @dataclass
    class DataCollatorSpeechSeq2SeqWithPadding:
        processor: Any

        def __call__(self, features: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
            input_features = [
                {"input_features": feature["input_features"]} for feature in features
            ]
            batch = self.processor.feature_extractor.pad(
                input_features,
                return_tensors="pt",
            )
            label_features = [{"input_ids": feature["labels"]} for feature in features]
            labels_batch = self.processor.tokenizer.pad(
                label_features,
                return_tensors="pt",
            )
            labels = labels_batch["input_ids"].masked_fill(
                labels_batch.attention_mask.ne(1),
                -100,
            )
            if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().item():
                labels = labels[:, 1:]
            batch["labels"] = labels
            return batch

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(args.output_dir),
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps,
        num_train_epochs=args.num_train_epochs,
        max_steps=args.max_steps,
        fp16=args.fp16,
        bf16=args.bf16,
        logging_steps=args.logging_steps,
        eval_strategy="steps" if eval_dataset is not None else "no",
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        save_total_limit=3,
        remove_unused_columns=False,
        label_names=["labels"],
        report_to=[],
        seed=args.seed,
    )

    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=DataCollatorSpeechSeq2SeqWithPadding(processor=processor),
        processing_class=processor.feature_extractor,
    )
    trainer.train()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(args.output_dir)
    processor.save_pretrained(args.output_dir)
    (args.output_dir / "train_config.json").write_text(
        json.dumps(vars(args), indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"saved LoRA adapter to {args.output_dir}")


if __name__ == "__main__":
    main()
