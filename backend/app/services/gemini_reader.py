import os
import re
import json
import base64
import warnings
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
# Silence the SDK's automatic function calling (AFC) warning in terminal
warnings.filterwarnings("ignore", message=".*automatic function calling.*")
warnings.filterwarnings("ignore", message=".*Direct use of automatic function calling.*")

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except ImportError:
    pass

DEFAULT_GEMINI_MODELS = [
    "gemini-3.8-flash"
]


def get_gemini_config() -> Dict[str, Any]:
    """Retrieves Gemini configuration from environment."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "").strip()
    timeout = int(os.getenv("GEMINI_TIMEOUT", "30"))
    return {
        "api_key": api_key,
        "model": model,
        "timeout": timeout,
    }


def is_gemini_available() -> bool:
    """Checks if Gemini API key is configured."""
    cfg = get_gemini_config()
    return bool(cfg["api_key"])


def get_genai_client():
    """Initializes Google GenAI client if package is available."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def build_seal_prompt(
    candidate_students: Optional[List[Dict[str, Any]]] = None,
    selected_class: Optional[str] = None,
    default_test_code: Optional[str] = None,
) -> str:
    candidate_names = [c["name"] for c in candidate_students] if candidate_students else []
    candidates_str = json.dumps(candidate_names) if candidate_names else "[]"

    return f"""You are an expert exam evaluation assistant.
Examine this cropped test seal image carefully.
It contains a table with cells for:
- Name (handwritten student name)
- Date
- Class/Board (e.g. SB12, ISC 12)
- Subject (e.g. Physics, Chemistry, Maths)
- QP Code (test question paper code, e.g. S12P35C, S12P40C2, I12M40C7.1)
- Marks (handwritten marks, typically written as obtained/total or fraction like 33 1/2 / 35, 18/40, 23/35)

Registered student candidates from our database for this exam section:
{candidates_str}
Selected Class Context: {selected_class or 'N/A'}
Default Test Code Context: {default_test_code or 'N/A'}

Analyze the visual handwriting, stamp table headers, and layout carefully:
1. Orientation Check: Check the orientation of the printed table headers ('Name', 'Date', 'Class / Board', 'Test Type', 'Subject', 'QP Code', 'Marks', 'Comments').
   Determine whether the printed headers and table are upright (readable normally) or upside-down (180 degrees inverted).
   Set `is_upside_down`: true if the table is upside down (inverted 180 degrees), false if it is already upright.
2. Student Name: Choose the best matching student from the candidate list if one matches the handwriting, OR transcribe the exact handwriting if not in the list. Note that cursive J or S can look similar; examine the stroke flow carefully.
3. Marks: Read the handwritten mark obtained and total marks. Fractional marks like 33 1/2 or 33.5 or 19 1/2 must be parsed accurately as decimal (e.g. 33.5, 19.5). If 23/35 is written, obtained is 23.0 and total is 35.0.
4. QP Code: Transcribe the QP Code accurately.

Return ONLY a valid JSON object with the following structure:
{{
  "is_upside_down": false,
  "student_name": "student name here",
  "marks_obtained": 33.5,
  "marks_total": 35.0,
  "qp_code": "detected QP Code",
  "confidence": 0.95,
  "reasoning": "short explanation of the reading"
}}
Do NOT output markdown backticks (like ```json), commentary, or any text other than the JSON object.
"""


def parse_vlm_json_output(raw_text: str) -> Optional[Dict[str, Any]]:
    """Cleans and extracts JSON object from Gemini raw output."""
    if not raw_text:
        return None

    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

    json_match = re.search(r"(\{.*\})", cleaned, flags=re.DOTALL)
    if json_match:
        cleaned = json_match.group(1)

    try:
        parsed = json.loads(cleaned)
    except Exception as e:
        print(f"Failed to parse Gemini JSON: {e}. Raw was: {raw_text[:200]}")
        return None

    is_upside_down = bool(parsed.get("is_upside_down", False))

    obtained = parsed.get("marks_obtained")
    if obtained is not None:
        try:
            if isinstance(obtained, str):
                m_frac = re.match(r"^(\d+)\s*(?:1/2|½|\.5)$", obtained.strip())
                if m_frac:
                    obtained = float(m_frac.group(1)) + 0.5
                else:
                    obtained = float(re.sub(r"[^0-9.]", "", obtained))
            else:
                obtained = float(obtained)
        except (ValueError, TypeError):
            obtained = None

    total = parsed.get("marks_total")
    if total is not None:
        try:
            if isinstance(total, str):
                total = float(re.sub(r"[^0-9.]", "", total))
            else:
                total = float(total)
        except (ValueError, TypeError):
            total = None

    conf = parsed.get("confidence", 0.95)
    try:
        conf = float(conf)
    except (ValueError, TypeError):
        conf = 0.95

    return {
        "is_upside_down": is_upside_down,
        "student_name": str(parsed.get("student_name", "")).strip(),
        "marks_obtained": obtained,
        "marks_total": total,
        "qp_code": str(parsed.get("qp_code", "")).strip(),
        "confidence": min(1.0, max(0.0, conf)),
        "reasoning": str(parsed.get("reasoning", "")),
    }


def call_gemini_sdk(
    api_key: str,
    model_name: str,
    prompt: str,
    raw_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> Optional[str]:
    """
    Generates content via Google GenAI Python SDK.
    Uses Chat.send_message (as recommended by Google to avoid AFC warning).
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Use Chat interface to comply with Google GenAI recommendation and prevent AFC warning
        try:
            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            response = chat.send_message(
                message=[
                    types.Part.from_bytes(data=raw_bytes, mime_type=mime_type),
                    prompt,
                ]
            )
            if response and response.text:
                return response.text.strip()
        except Exception:
            # Fall back to models.generate_content if chat create is not supported
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=raw_bytes, mime_type=mime_type),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            if response and response.text:
                return response.text.strip()
    except Exception:
        # SDK call failed or not installed, will fall back to REST
        pass
    return None


def call_gemini_rest(
    api_key: str,
    model_name: str,
    prompt: str,
    raw_bytes: bytes,
    mime_type: str = "image/jpeg",
    timeout: int = 30,
) -> Optional[str]:
    """Direct REST fallback to Gemini API (works with zero extra SDK dependencies)."""
    base64_data = base64.b64encode(raw_bytes).decode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64_data,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        else:
            print(f"Gemini REST API error HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Gemini REST request error: {e}")

    return None


def analyze_seal_gemini(
    seal_image_path: str,
    candidate_students: Optional[List[Dict[str, Any]]] = None,
    selected_class: Optional[str] = None,
    default_test_code: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Analyzes an exam seal table using Google Gemini API.
    Fast, highly accurate cloud Vision AI.
    """
    if not seal_image_path or not os.path.exists(seal_image_path):
        return None

    cfg = get_gemini_config()
    api_key = cfg["api_key"]
    if not api_key:
        return None

    try:
        with open(seal_image_path, "rb") as f:
            raw_bytes = f.read()
    except Exception as e:
        print(f"Failed to read image for Gemini: {e}")
        return None

    mime_type = "image/png" if str(seal_image_path).lower().endswith(".png") else "image/jpeg"

    prompt = build_seal_prompt(
        candidate_students=candidate_students,
        selected_class=selected_class,
        default_test_code=default_test_code,
    )

    models_to_try = []
    if cfg["model"]:
        models_to_try.append(cfg["model"])
    for default_m in DEFAULT_GEMINI_MODELS:
        if default_m not in models_to_try:
            models_to_try.append(default_m)

    for model_name in models_to_try:
        raw_output = call_gemini_sdk(
            api_key=api_key,
            model_name=model_name,
            prompt=prompt,
            raw_bytes=raw_bytes,
            mime_type=mime_type,
        )

        if not raw_output:
            raw_output = call_gemini_rest(
                api_key=api_key,
                model_name=model_name,
                prompt=prompt,
                raw_bytes=raw_bytes,
                mime_type=mime_type,
                timeout=cfg["timeout"],
            )

        if raw_output:
            parsed = parse_vlm_json_output(raw_output)
            if parsed is not None:
                parsed["model_used"] = f"gemini ({model_name})"
                return parsed

    return None


def read_handwriting(image_path: str, field: str) -> str:
    """Single-field fallback using Gemini."""
    cfg = get_gemini_config()
    if not cfg["api_key"] or not os.path.exists(image_path):
        return ""

    if field == "name":
        prompt = (
            "This is a cropped image containing a student's handwritten name. "
            "Read the handwriting carefully. Ignore printed labels and borders. "
            "Return ONLY the student's name."
        )
    elif field == "marks":
        prompt = (
            "This is a cropped image containing a student's handwritten exam marks. "
            "Read ONLY the handwritten numeric mark (including fractions/decimals). "
            "Return ONLY what is written with no explanation."
        )
    else:
        prompt = "Read the handwritten text in this image. Return ONLY the text with no explanation."

    try:
        with open(image_path, "rb") as f:
            raw_bytes = f.read()
    except Exception:
        return ""

    mime_type = "image/png" if str(image_path).lower().endswith(".png") else "image/jpeg"
    model = cfg["model"] or DEFAULT_GEMINI_MODELS[0]

    raw_output = call_gemini_sdk(cfg["api_key"], model, prompt, raw_bytes, mime_type)
    if not raw_output:
        raw_output = call_gemini_rest(cfg["api_key"], model, prompt, raw_bytes, mime_type, cfg["timeout"])

    return raw_output.strip() if raw_output else ""
