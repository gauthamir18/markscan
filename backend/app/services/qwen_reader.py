import os
import re
import json
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
import cv2
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

DEFAULT_QWEN_MODELS = [
    "qwen2.5vl:3b",
    "qwen2.5vl:7b",
    "qwen2.5vl",
    "qwen2.5-vl:3b",
    "qwen2.5-vl:7b",
    "qwen2.5-vl",
    "qwen2-vl:7b",
    "qwen2-vl:2b",
]


def get_qwen_config() -> Dict[str, Any]:
    """Retrieves Qwen server configuration from environment."""
    base_url = os.getenv("QWEN_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("QWEN_MODEL", "").strip()
    api_key = os.getenv("QWEN_API_KEY", "").strip()
    timeout = int(os.getenv("QWEN_TIMEOUT", "90"))
    return {
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
        "timeout": timeout,
    }


def is_qwen_available() -> bool:
    """Checks if a local or remote Qwen-capable server is reachable."""
    cfg = get_qwen_config()
    headers = {"Authorization": f"Bearer {cfg['api_key']}"} if cfg["api_key"] else {}
    try:
        # Check Ollama tags first
        resp = requests.get(f"{cfg['base_url']}/api/tags", headers=headers, timeout=3)
        if resp.status_code == 200:
            return True
    except Exception:
        pass

    try:
        # Check OpenAI-compatible /v1/models (vLLM / LM Studio / LocalAI)
        resp = requests.get(f"{cfg['base_url']}/v1/models", headers=headers, timeout=3)
        if resp.status_code == 200:
            return True
    except Exception:
        pass

    return False


def get_installed_ollama_models(base_url: str) -> List[str]:
    """Queries Ollama for list of installed model names."""
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        pass
    return []


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
    """Cleans and extracts JSON object from VLM raw string output."""
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
        print(f"Failed to parse Qwen JSON: {e}. Raw was: {raw_text[:200]}")
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


def call_ollama_api(
    base_url: str,
    model_name: str,
    prompt: str,
    base64_img: str,
    timeout: int = 90
) -> Optional[str]:
    """Calls Ollama's native multimodal chat API (/api/chat)."""
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [base64_img],
            }
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_predict": 256,
        },
    }

    try:
        resp = requests.post(f"{base_url}/api/chat", json=payload, timeout=timeout)
        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", "")
        else:
            print(f"Ollama chat error HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Ollama API request failed: {e}")
    return None


def call_openai_compatible_api(
    base_url: str,
    model_name: str,
    prompt: str,
    base64_img: str,
    mime_type: str = "image/jpeg",
    api_key: str = "",
    timeout: int = 90,
) -> Optional[str]:
    """Calls standard OpenAI-compatible /v1/chat/completions (vLLM, LM Studio, etc.)."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    endpoint = base_url if base_url.endswith("/v1") else f"{base_url}/v1"
    endpoint = f"{endpoint}/chat/completions"

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_img}"},
                    },
                ],
            }
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 200:
            choices = resp.json().get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
        else:
            print(f"OpenAI-compatible Qwen API error HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"OpenAI-compatible API request failed: {e}")
    return None


def analyze_seal_qwen(
    seal_image_path: str,
    candidate_students: Optional[List[Dict[str, Any]]] = None,
    selected_class: Optional[str] = None,
    default_test_code: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Analyzes an exam seal table using open-source Qwen Vision-Language Model.
    Compatible with local Ollama, vLLM, LM Studio, or remote Qwen endpoints.
    """
    if not seal_image_path or not os.path.exists(seal_image_path):
        return None

    cfg = get_qwen_config()
    base_url = cfg["base_url"]

    # Preprocess image: scale to max dimension ~800px to ensure fast local VLM inference
    try:
        img = cv2.imread(seal_image_path)
        if img is None:
            return None
        h, w = img.shape[:2]
        max_dim = 800
        if max(h, w) > max_dim:
            scale = max_dim / float(max(h, w))
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        success, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            with open(seal_image_path, "rb") as f:
                raw_bytes = f.read()
        else:
            raw_bytes = buffer.tobytes()

        base64_img = base64.b64encode(raw_bytes).decode("utf-8")
    except Exception as e:
        print(f"Failed to read/encode image for Qwen: {e}")
        return None

    prompt = build_seal_prompt(
        candidate_students=candidate_students,
        selected_class=selected_class,
        default_test_code=default_test_code,
    )

    # Determine model to use
    models_to_try = []
    if cfg["model"]:
        models_to_try.append(cfg["model"])

    installed_models = get_installed_ollama_models(base_url)
    for default_m in DEFAULT_QWEN_MODELS:
        if default_m in installed_models and default_m not in models_to_try:
            models_to_try.append(default_m)

    if not models_to_try:
        models_to_try.extend(DEFAULT_QWEN_MODELS)

    # Execute inference
    for model_name in models_to_try:
        # Try native Ollama chat API
        raw_output = call_ollama_api(
            base_url=base_url,
            model_name=model_name,
            prompt=prompt,
            base64_img=base64_img,
            timeout=cfg["timeout"],
        )

        # Fallback to OpenAI-compatible API
        if not raw_output:
            raw_output = call_openai_compatible_api(
                base_url=base_url,
                model_name=model_name,
                prompt=prompt,
                base64_img=base64_img,
                mime_type="image/jpeg",
                api_key=cfg["api_key"],
                timeout=cfg["timeout"],
            )

        if raw_output:
            parsed = parse_vlm_json_output(raw_output)
            if parsed is not None:
                parsed["model_used"] = f"qwen ({model_name})"
                return parsed

    return None
