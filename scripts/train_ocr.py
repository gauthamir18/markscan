import os
import csv
import json
import math
import random
import numpy as np
import cv2
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "dataset_ocr" / "annotations.csv"
MODEL_DIR = BASE_DIR / "backend" / "models" / "ocr"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Vocabulary: 0 is reserved for CTC blank
DEFAULT_VOCAB = list(" 0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/.-,")

class TextTokenizer:
    def __init__(self, chars=None):
        self.chars = chars or DEFAULT_VOCAB
        self.char2idx = {c: i + 1 for i, c in enumerate(self.chars)}
        self.idx2char = {i + 1: c for i, c in enumerate(self.chars)}
        self.blank_idx = 0

    def encode(self, text):
        return [self.char2idx[c] for c in text if c in self.char2idx]

    def decode(self, indices):
        # Greedy CTC decoding
        res = []
        prev = self.blank_idx
        for idx in indices:
            if idx != self.blank_idx and idx != prev:
                if idx in self.idx2char:
                    res.append(self.idx2char[idx])
            prev = idx
        return "".join(res)

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"chars": self.chars}, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data["chars"])


class OCRDataset(Dataset):
    def __init__(self, records, tokenizer, img_h=32, img_w=256, is_train=True):
        self.records = records
        self.tokenizer = tokenizer
        self.img_h = img_h
        self.img_w = img_w
        self.is_train = is_train

    def __len__(self):
        return len(self.records)

    def preprocess(self, img):
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        h, w = img.shape
        scale = self.img_h / float(h)
        new_w = min(self.img_w, max(1, int(w * scale)))
        resized = cv2.resize(img, (new_w, self.img_h), interpolation=cv2.INTER_AREA)

        canvas = np.full((self.img_h, self.img_w), 255, dtype=np.uint8)
        canvas[:, :new_w] = resized

        # Normalize to [-1, 1]
        tensor = (canvas.astype(np.float32) / 127.5) - 1.0
        return torch.tensor(tensor, dtype=torch.float32).unsqueeze(0)

    def __getitem__(self, idx):
        item = self.records[idx]
        img_p = str(BASE_DIR / item["image_path"])
        img = cv2.imread(img_p)
        if img is None:
            img = np.zeros((self.img_h, self.img_w, 3), dtype=np.uint8)

        tensor = self.preprocess(img)
        text = item["text"].strip()
        encoded = self.tokenizer.encode(text)
        return tensor, torch.tensor(encoded, dtype=torch.long), text


def collate_fn(batch):
    tensors, targets, texts = zip(*batch)
    tensors = torch.stack(tensors, dim=0)

    target_lengths = torch.tensor([len(t) for t in targets], dtype=torch.long)
    flat_targets = torch.cat(targets, dim=0) if sum(target_lengths) > 0 else torch.zeros(0, dtype=torch.long)

    return tensors, flat_targets, target_lengths, texts


class CRNN(nn.Module):
    def __init__(self, vocab_size, hidden_size=256):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2), # 16 x 128

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2), # 8 x 64

            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),

            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1), (2, 1)), # 4 x 64

            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),

            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d((2, 1), (2, 1)), # 2 x 64

            nn.Conv2d(512, 512, kernel_size=(2, 1), padding=0),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True), # 1 x 64
        )
        self.rnn = nn.LSTM(512, hidden_size, bidirectional=True, num_layers=2, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size * 2, vocab_size + 1)

    def forward(self, x):
        features = self.cnn(x) # [B, 512, 1, W]
        features = features.squeeze(2).permute(0, 2, 1) # [B, W, 512]
        recurrent, _ = self.rnn(features) # [B, W, hidden*2]
        logits = self.fc(recurrent) # [B, W, vocab+1]
        return logits.permute(1, 0, 2) # [W, B, vocab+1] for CTC loss


def train(epochs=30, batch_size=16, lr=1e-3):
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Training on device: {device}")

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        all_records = list(csv.DictReader(f))

    # Keep records with valid text
    records = [r for r in all_records if r.get("text", "").strip()]
    if not records:
        print("Warning: No labeled records found in annotations.csv!")
        print("Running with sample placeholder to verify model architecture...")
        records = [
            {"image_path": all_records[0]["image_path"], "split": "train", "field": "name", "text": "Student Name"},
            {"image_path": all_records[1]["image_path"], "split": "val", "field": "marks", "text": "45/50"},
        ]

    # Build vocabulary from records
    all_chars = set()
    for r in records:
        all_chars.update(r["text"])
    chars = sorted(list(set(DEFAULT_VOCAB).union(all_chars)))
    tokenizer = TextTokenizer(chars)
    tokenizer.save(MODEL_DIR / "vocab.json")
    print(f"Vocabulary size: {len(tokenizer.chars)} characters. Saved to {MODEL_DIR / 'vocab.json'}")

    train_recs = [r for r in records if r.get("split") == "train"]
    val_recs = [r for r in records if r.get("split") == "val"]
    if not val_recs:
        val_recs = train_recs[:max(1, len(train_recs) // 5)]

    train_ds = OCRDataset(train_recs, tokenizer, is_train=True)
    val_ds = OCRDataset(val_recs, tokenizer, is_train=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

    model = CRNN(vocab_size=len(tokenizer.chars)).to(device)
    criterion = nn.CTCLoss(blank=tokenizer.blank_idx, zero_infinity=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_loss = float("inf")
    print(f"Starting training for {epochs} epochs ({len(train_recs)} train, {len(val_recs)} val)...")

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0

        for tensors, flat_targets, target_lengths, _ in train_loader:
            tensors = tensors.to(device)
            flat_targets = flat_targets.to(device)

            optimizer.zero_grad()
            logits = model(tensors) # [W, B, vocab+1]
            log_probs = logits.log_softmax(2)

            input_lengths = torch.full((tensors.size(0),), logits.size(0), dtype=torch.long)
            loss = criterion(log_probs, flat_targets, input_lengths, target_lengths)

            if not math.isnan(loss.item()) and not math.isinf(loss.item()):
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
                optimizer.step()
                train_loss += loss.item()

        scheduler.step()
        avg_train_loss = train_loss / max(1, len(train_loader))

        # Evaluation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for tensors, flat_targets, target_lengths, _ in val_loader:
                tensors = tensors.to(device)
                flat_targets = flat_targets.to(device)
                logits = model(tensors)
                log_probs = logits.log_softmax(2)
                input_lengths = torch.full((tensors.size(0),), logits.size(0), dtype=torch.long)
                loss = criterion(log_probs, flat_targets, input_lengths, target_lengths)
                if not math.isnan(loss.item()) and not math.isinf(loss.item()):
                    val_loss += loss.item()

        avg_val_loss = val_loss / max(1, len(val_loader))

        if epoch % 5 == 0 or epoch == 1 or avg_val_loss < best_val_loss:
            print(f"Epoch {epoch:02d}/{epochs} - Train Loss: {avg_train_loss:.4f} - Val Loss: {avg_val_loss:.4f}")

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "vocab": tokenizer.chars,
                "val_loss": best_val_loss
            }, MODEL_DIR / "best_ocr_model.pt")

    print(f"\nTraining complete! Best model checkpoint saved to: {MODEL_DIR / 'best_ocr_model.pt'}")


if __name__ == "__main__":
    train()
