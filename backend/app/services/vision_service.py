import os
from pathlib import Path
from typing import Optional, List, Dict, Any
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except ImportError:
    pass

from app.services.gemini_reader import analyze_seal_gemini, is_gemini_available, get_gemini_config
from app.services.qwen_reader import analyze_seal_qwen, is_qwen_available, get_qwen_config


def get_active_vision_provider() -> Dict[str, Any]:
    """
    Returns current active vision AI provider status.
    Hierarchy:
    1. Gemini API (cloud, fast)
    2. Qwen 2.5-VL (local VLM)
    3. Local Trained Model (offline CRNN/EasyOCR + DB fuzzy match)
    """
    gemini_up = is_gemini_available()
    qwen_up = is_qwen_available()

    if gemini_up:
        active = "gemini"
    elif qwen_up:
        active = "qwen"
    else:
        active = "local_model"

    return {
        "active": active,
        "gemini_available": gemini_up,
        "gemini_model": get_gemini_config()["model"] or "gemini-3.8-flash",
        "qwen_available": qwen_up,
        "qwen_model": get_qwen_config()["model"] or "auto",
    }


def is_vision_available() -> bool:
    """Returns True if either Gemini or Qwen is available."""
    return is_gemini_available() or is_qwen_available()


def analyze_seal_vision(
    seal_image_path: str,
    candidate_students: Optional[List[Dict[str, Any]]] = None,
    selected_class: Optional[str] = None,
    default_test_code: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Master entrypoint for Vision AI seal analysis with hierarchical fallback:
    1. Tier 1: Google Gemini API (fast cloud vision)
    2. Tier 2: Qwen 2.5-VL (local VLM via Ollama/OpenAI-compatible server)
    3. Tier 3: Returns None -> caller falls back to Local Trained Model (OCR + DB fuzzy match)
    """
    # 1. Attempt Gemini API first
    if is_gemini_available():
        try:
            res = analyze_seal_gemini(
                seal_image_path=seal_image_path,
                candidate_students=candidate_students,
                selected_class=selected_class,
                default_test_code=default_test_code,
            )
            if res is not None:
                return res
            print("[Vision AI] Gemini returned no result, attempting Qwen fallback...")
        except Exception as e:
            print(f"[Vision AI] Gemini API error: {e}. Falling back to Qwen...")

    # 2. Fall back to local Qwen 2.5-VL
    if is_qwen_available():
        try:
            res = analyze_seal_qwen(
                seal_image_path=seal_image_path,
                candidate_students=candidate_students,
                selected_class=selected_class,
                default_test_code=default_test_code,
            )
            if res is not None:
                return res
            print("[Vision AI] Qwen returned no result, falling back to local trained model...")
        except Exception as e:
            print(f"[Vision AI] Qwen fallback error: {e}. Falling back to local trained model...")

    # 3. Both Vision models unavailable or failed -> caller falls back to local trained model
    return None
