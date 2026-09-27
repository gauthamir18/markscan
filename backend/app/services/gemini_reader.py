import os
import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

PREFERRED_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]


def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize GenAI Client: {e}")
        return None


def analyze_seal_vision(
    seal_image_path: str,
    candidate_students: List[Dict[str, Any]] = None,
    selected_class: Optional[str] = None,
    default_test_code: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Vision AI analysis of the entire seal image.
    Inspects handwriting, compares against candidate student list, and extracts:
    - student_name (selected from candidate list or exact transcription)
    - marks_obtained (float)
    - marks_total (float)
    - qp_code (str)
    - confidence (0.0 to 1.0)
    """
    client = get_genai_client()
    if client is None:
        return None

    if not os.path.exists(seal_image_path):
        return None

    try:
        with open(seal_image_path, "rb") as f:
            image_data = f.read()

        candidate_names = [c["name"] for c in candidate_students] if candidate_students else []
        candidates_str = json.dumps(candidate_names) if candidate_names else "[]"

        prompt = f"""You are an expert exam evaluation assistant.
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
  "is_upside_down": <true or false>,
  "student_name": "<best matching student name from candidate list or transcription>",
  "marks_obtained": <numeric float or null, e.g. 33.5>,
  "marks_total": <numeric float or null, e.g. 35.0>,
  "qp_code": "<detected QP Code string or empty>",
  "confidence": <float from 0.0 to 1.0>,
  "reasoning": "<short 1-line reason explaining the reading and orientation>"
}}
Do NOT include markdown formatting outside the JSON object.
"""

        from google.genai import types

        mime_type = "image/png" if str(seal_image_path).lower().endswith(".png") else "image/jpeg"
        for model_name in PREFERRED_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=image_data, mime_type=mime_type),
                        prompt,
                    ],
                )
                if not response or not response.text:
                    continue

                raw_text = response.text.strip()
                # Clean code blocks if present
                clean_json_str = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
                clean_json_str = re.sub(r"\s*```$", "", clean_json_str, flags=re.MULTILINE).strip()

                parsed = json.loads(clean_json_str)

                # Validate types
                is_upside_down = bool(parsed.get("is_upside_down", False))

                obtained = parsed.get("marks_obtained")
                if obtained is not None:
                    try:
                        obtained = float(obtained)
                    except (ValueError, TypeError):
                        obtained = None

                total = parsed.get("marks_total")
                if total is not None:
                    try:
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
                    "student_name": parsed.get("student_name", "").strip(),
                    "marks_obtained": obtained,
                    "marks_total": total,
                    "qp_code": parsed.get("qp_code", "").strip(),
                    "confidence": min(1.0, max(0.0, conf)),
                    "reasoning": parsed.get("reasoning", ""),
                    "model_used": model_name,
                }
            except Exception as err:
                print(f"Gemini model {model_name} error: {err}")
                continue

        return None
    except Exception as e:
        print(f"Vision AI analyze_seal_vision error: {e}")
        return None


def read_handwriting(image_path: str, field: str) -> str:
    """Legacy single-field fallback."""
    client = get_genai_client()
    if client is None or not os.path.exists(image_path):
        return ""

    try:
        from google.genai import types

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

        with open(image_path, "rb") as f:
            image_data = f.read()

        for model_name in PREFERRED_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
                        prompt,
                    ],
                )
                text = response.text.strip() if response and response.text else ""
                if text:
                    return text
            except Exception:
                continue

        return ""
    except Exception as e:
        print(f"Gemini reader error: {e}")
        return ""
