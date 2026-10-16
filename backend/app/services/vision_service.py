import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from app.services.qwen_reader import analyze_seal_qwen, is_qwen_available, get_qwen_config

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def get_active_vision_provider() -> Dict[str, Any]:
    """Returns current active vision AI provider status."""
    qwen_up = is_qwen_available()
    return {
        "active": "qwen" if qwen_up else "none",
        "qwen_available": qwen_up,
        "qwen_model": get_qwen_config()["model"] or "auto",
    }


def is_vision_available() -> bool:
    """Returns True if Qwen is available."""
    return is_qwen_available()


def analyze_seal_vision(
    seal_image_path: str,
    candidate_students: Optional[List[Dict[str, Any]]] = None,
    selected_class: Optional[str] = None,
    default_test_code: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Master entrypoint for Vision AI seal analysis.
    Uses open-source Qwen 2.5-VL for 100% free, local, unlimited document and mark recognition.
    """
    if is_qwen_available():
        try:
            return analyze_seal_qwen(
                seal_image_path=seal_image_path,
                candidate_students=candidate_students,
                selected_class=selected_class,
                default_test_code=default_test_code,
            )
        except Exception as e:
            print(f"Qwen Vision error: {e}")

    return None
