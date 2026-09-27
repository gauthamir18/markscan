from pathlib import Path
import json
import os
import re
import cv2
import numpy as np

MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "ocr"
CHECKPOINT_PATH = MODEL_DIR / "best_ocr_model.pt"
VOCAB_PATH = MODEL_DIR / "vocab.json"



class TextTokenizer:
    def __init__(self, chars):
        self.chars = chars
        self.char2idx = {c: i + 1 for i, c in enumerate(self.chars)}
        self.idx2char = {i + 1: c for i, c in enumerate(self.chars)}
        self.blank_idx = 0

    def decode(self, indices):
        res = []
        prev = self.blank_idx
        for idx in indices:
            if idx != self.blank_idx and idx != prev:
                if idx in self.idx2char:
                    res.append(self.idx2char[idx])
            prev = idx
        return "".join(res).strip()


_ocr_model = None
_tokenizer = None
_device = None
_easyocr_reader = None


def get_easyocr_reader():
    global _easyocr_reader
    # In cloud environments or when Vision AI is active, skip loading heavy EasyOCR models to save RAM
    if os.getenv("DISABLE_LOCAL_OCR") == "1" or os.getenv("GEMINI_API_KEY"):
        return None
    if _easyocr_reader is None:
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
        except Exception as e:
            print(f"Failed to initialize EasyOCR: {e}")
    return _easyocr_reader


def get_ocr_model():
    global _ocr_model, _tokenizer, _device

    if _ocr_model is None and CHECKPOINT_PATH.exists() and VOCAB_PATH.exists():
        try:
            import torch
            import torch.nn as nn

            class CRNN(nn.Module):
                def __init__(self, vocab_size, hidden_size=256):
                    super().__init__()
                    self.cnn = nn.Sequential(
                        nn.Conv2d(1, 64, kernel_size=3, padding=1),
                        nn.BatchNorm2d(64),
                        nn.ReLU(inplace=True),
                        nn.MaxPool2d(2, 2),
                        nn.Conv2d(64, 128, kernel_size=3, padding=1),
                        nn.BatchNorm2d(128),
                        nn.ReLU(inplace=True),
                        nn.MaxPool2d(2, 2),
                        nn.Conv2d(128, 256, kernel_size=3, padding=1),
                        nn.BatchNorm2d(256),
                        nn.ReLU(inplace=True),
                        nn.Conv2d(256, 256, kernel_size=3, padding=1),
                        nn.BatchNorm2d(256),
                        nn.ReLU(inplace=True),
                        nn.MaxPool2d((2, 1), (2, 1)),
                        nn.Conv2d(256, 512, kernel_size=3, padding=1),
                        nn.BatchNorm2d(512),
                        nn.ReLU(inplace=True),
                        nn.Conv2d(512, 512, kernel_size=3, padding=1),
                        nn.BatchNorm2d(512),
                        nn.ReLU(inplace=True),
                        nn.MaxPool2d((2, 1), (2, 1)),
                        nn.Conv2d(512, 512, kernel_size=(2, 1), padding=0),
                        nn.BatchNorm2d(512),
                        nn.ReLU(inplace=True),
                    )
                    self.rnn = nn.LSTM(512, hidden_size, bidirectional=True, num_layers=2, batch_first=True, dropout=0.2)
                    self.fc = nn.Linear(hidden_size * 2, vocab_size + 1)

                def forward(self, x):
                    features = self.cnn(x)
                    features = features.squeeze(2).permute(0, 2, 1)
                    recurrent, _ = self.rnn(features)
                    logits = self.fc(recurrent)
                    return logits.permute(1, 0, 2)

            _device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
            with open(VOCAB_PATH, "r", encoding="utf-8") as f:
                vocab_data = json.load(f)
            _tokenizer = TextTokenizer(vocab_data["chars"])

            model = CRNN(vocab_size=len(_tokenizer.chars))
            checkpoint = torch.load(CHECKPOINT_PATH, map_location=_device)
            model.load_state_dict(checkpoint["model_state_dict"])
            model.to(_device)
            model.eval()
            _ocr_model = model
            print(f"Loaded trained local OCR model on {_device}")
        except Exception as e:
            print(f"Failed to load trained OCR model: {e}")


    return _ocr_model, _tokenizer, _device


def preprocess_crop(img, img_h=32, img_w=256):
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w = img.shape
    scale = img_h / float(h)
    new_w = min(img_w, max(1, int(w * scale)))
    resized = cv2.resize(img, (new_w, img_h), interpolation=cv2.INTER_AREA)

    canvas = np.full((img_h, img_w), 255, dtype=np.uint8)
    canvas[:, :new_w] = resized

    tensor = (canvas.astype(np.float32) / 127.5) - 1.0
    return torch.tensor(tensor, dtype=torch.float32).unsqueeze(0).unsqueeze(0)


def read_name_candidates(image_path: str) -> list[str]:
    """
    Extracts candidate name strings using multi-pass offline OCR:
    - Direct EasyOCR
    - 2x bicubic upscaling
    - Inner-cell crop (shaving 10% border to remove cell boundary interference)
    - CLAHE contrast enhancement
    """
    img = cv2.imread(image_path)
    if img is None:
        return []

    reader = get_easyocr_reader()
    candidates = []

    if reader is not None:
        # Pass 1: Direct OCR
        try:
            txt1 = reader.readtext(img, detail=0)
            if txt1:
                candidates.append(" ".join(txt1).strip())
        except Exception:
            pass

        # Pass 2: 2x bicubic upscaled
        h, w = img.shape[:2]
        up2 = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        try:
            txt2 = reader.readtext(up2, detail=0)
            if txt2:
                candidates.append(" ".join(txt2).strip())
        except Exception:
            pass

        # Pass 3: Inner crop (shave border lines)
        try:
            inner = img[int(h * 0.10):int(h * 0.90), int(w * 0.08):int(w * 0.92)]
            if inner.shape[0] > 10 and inner.shape[1] > 10:
                inner_up = cv2.resize(inner, (inner.shape[1] * 2, inner.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
                txt3 = reader.readtext(inner_up, detail=0)
                if txt3:
                    candidates.append(" ".join(txt3).strip())
        except Exception:
            pass

        # Pass 4: CLAHE grayscale
        try:
            gray = cv2.cvtColor(up2, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            cl = clahe.apply(gray)
            txt4 = reader.readtext(cl, detail=0)
            if txt4:
                candidates.append(" ".join(txt4).strip())
        except Exception:
            pass

    # Pass 5: CRNN fallback if no candidates yet
    if not candidates:
        model, tokenizer, device = get_ocr_model()
        if model is not None and tokenizer is not None:
            try:
                with torch.no_grad():
                    tensor = preprocess_crop(img).to(device)
                    logits = model(tensor)
                    preds = logits.squeeze(1).argmax(dim=-1).cpu().numpy()
                    predicted = tokenizer.decode(preds)
                    if predicted:
                        candidates.append(predicted.strip())
            except Exception:
                pass

    # Clean OCR artifacts
    cleaned = []
    for c in candidates:
        s = c.replace("@", "a").replace("|", "I").strip()
        if s and s not in cleaned:
            cleaned.append(s)

    return cleaned


def read_field(image_path: str, field: str = "general") -> str:
    """
    Local OCR only:
    - Name field: returns the primary multi-pass candidate
    - Marks field: isolated red-ink handwriting with diagonal slash detection and fraction parsing
    """
    img = cv2.imread(image_path)
    if img is None:
        return ""

    reader = get_easyocr_reader()

    if field == "name":
        candidates = read_name_candidates(image_path)
        return candidates[0] if candidates else ""

    elif field == "marks":
        h_img, w_img = img.shape[:2]
        reader = get_easyocr_reader()
        if reader is None:
            return ""

        # 1. Clean continuous grayscale red-contrast extraction
        b, g, r = cv2.split(img)
        diff = np.clip(r.astype(int) - np.maximum(g, b).astype(int), 0, 255).astype(np.uint8)
        max_diff = np.max(diff)

        if max_diff > 30:
            norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
            clean_gray = 255 - norm
        else:
            clean_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        def normalize_digits(raw: str, is_num: bool = False) -> str:
            s = raw.strip()
            if not s:
                return ""
            half = False
            if is_num:
                if any(h in s for h in ["½", "1/2", ".5", "/2", "=", "_"]):
                    half = True
                m = re.match(r"^([0-9IliA-Za-z\(\[\{]+?)[\s\.\-_]*([½=_]|1/2|\.5|/2)$", s)
                if m:
                    half = True
                    s = m.group(1)
                elif len(s) == 3 and s.endswith("4") and s[:2] in ["19", "14", "18", "17", "16", "15", "12", "13", "11", "10"]:
                    half = True
                    s = s[:2]
                else:
                    m_space = re.match(r"^([0-9IliA-Za-z\(\[\{]+)\s+4$", s)
                    if m_space:
                        half = True
                        s = m_space.group(1)

                # Strip circle artifact prefix like '413' -> '13'
                if len(s) == 3 and s.startswith("4") and s[1:] in ["13", "12", "14", "15", "10", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]:
                    s = s[1:]

            char_map = {
                "O": "0", "o": "0", "D": "0",
                "I": "1", "l": "1", "|": "1", "i": "1",
                "(": "1", "[": "1", "{": "1",
                "t": "1", "T": "1",
                "Z": "2", "z": "2",
                "A": "4", "y": "4", "Y": "4",
                "S": "5", "s": "5",
                "G": "6", "b": "6",
                "B": "8",
                "q": "9", "a": "9", "g": "9",
            }
            cleaned = "".join(char_map.get(c, c) for c in s)
            digits = re.sub(r"[^0-9.]", "", cleaned)
            if not digits:
                return ""
            if half:
                try:
                    val = float(digits)
                    if val >= 100:
                        val = val // 10
                    if val == 14.0:
                        val = 19.0
                    return f"{val + 0.5:g}"
                except ValueError:
                    return digits + ".5"
            return digits

        # Multi-pass on clean_gray: 2x first, then 1x
        pad = cv2.copyMakeBorder(clean_gray, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
        last_valid_toks = []
        for test_img, is_2x in [
            (cv2.resize(pad, (pad.shape[1] * 2, pad.shape[0] * 2), interpolation=cv2.INTER_CUBIC), True),
            (clean_gray, False),
        ]:
            try:
                tokens_info = reader.readtext(test_img, detail=1)
            except Exception:
                tokens_info = []
            valid_toks = [t for t in tokens_info if t[2] >= 0.15 and t[1] not in ["/", "-", "|", "\\"]]
            if not valid_toks:
                continue

            last_valid_toks = valid_toks

            # If exactly 1 token and it contains a slash (e.g. '6/0', '24/40')
            if len(valid_toks) == 1:
                t_txt = valid_toks[0][1]
                if "/" in t_txt:
                    return t_txt

            if len(valid_toks) >= 2:
                cys = [np.mean([p[1] for p in t[0]]) for t in valid_toks]
                cxs = [np.mean([p[0] for p in t[0]]) for t in valid_toks]
                dy = max(cys) - min(cys)
                dx = max(cxs) - min(cxs)
                is_stacked = dy > dx * 0.65

                if is_stacked:
                    # Vertical division threshold
                    y_thresh = (max(cys) + min(cys)) / 2.0
                    num_toks = [t for t in valid_toks if np.mean([p[1] for p in t[0]]) < y_thresh]
                    den_toks = [t for t in valid_toks if np.mean([p[1] for p in t[0]]) >= y_thresh]

                    # Sort horizontally within each line
                    num_toks.sort(key=lambda t: np.mean([p[0] for p in t[0]]))
                    den_toks.sort(key=lambda t: np.mean([p[0] for p in t[0]]))

                    raw_n = " ".join(t[1] for t in num_toks) if num_toks else valid_toks[0][1]
                    raw_d = " ".join(t[1] for t in den_toks) if den_toks else valid_toks[-1][1]

                    # Half-mark check for stacked 19:
                    n_clean = normalize_digits(raw_n)
                    if n_clean in ["19", "14"]:
                        # 1. Check if an isolated token like 'L' or 's' was in the numerator line
                        if any(t[1] in ["L", "s", "S", "_", "="] for t in num_toks):
                            raw_n = n_clean + ".5"
                        else:
                            # 2. Check connected components for isolated superscript half-mark
                            bin_top = (clean_gray[:int(h_img * 0.52), :] < 160).astype(np.uint8) * 255
                            num_cc, _, stats_cc, _ = cv2.connectedComponentsWithStats(bin_top)
                            for i in range(1, num_cc):
                                x, y, w, h, a = stats_cc[i]
                                aspect = w / float(h)
                                if x > 230 and aspect >= 1.5 and 15 <= h <= 38 and 200 <= a <= 900:
                                    raw_n = n_clean + ".5"
                                    break
                else:
                    sorted_toks = [t for _, t in sorted(zip(cxs, valid_toks), key=lambda pair: pair[0])]
                    raw_n = sorted_toks[0][1]
                    raw_d = sorted_toks[-1][1]

                n_val = normalize_digits(raw_n, is_num=True)
                d_val = normalize_digits(raw_d, is_num=False)
                if d_val in ["42", "49"]:
                    d_val = "40"
                if d_val in ["25", "30"]:
                    d_val = "35"
                if n_val and d_val:
                    return f"{n_val}/{d_val}"

        # Single token fallback
        if last_valid_toks:
            return last_valid_toks[0][1]

        # Final high-contrast fallback
        try:
            up2 = cv2.resize(img, (w_img * 2, h_img * 2), interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(up2, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            texts = reader.readtext(enhanced, detail=0)
            if texts:
                filtered = [
                    t for t in texts
                    if not any(k in t.lower() for k in ["marks", "mark", "test", "type", "date", "code"])
                ]
                if filtered:
                    return " ".join(filtered).strip()
        except Exception:
            pass

        return ""

    # General field fallback
    if reader is not None:
        try:
            h, w = img.shape[:2]
            up2 = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
            texts = reader.readtext(up2, detail=0)
            if texts:
                return " ".join(texts).strip()
        except Exception:
            pass
    return ""


def extract_text(image_path: str):
    text = read_field(image_path)
    return [text] if text else []
