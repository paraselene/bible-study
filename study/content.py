import json
import re

from django.conf import settings
from django.http import Http404


def load_lesson(lesson_id):
    if not re.fullmatch(r"u\d+-s\d+", lesson_id):
        raise Http404
    path = settings.LESSON_DIR / f"{lesson_id.replace('-', '_')}.json"
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise Http404 from None


def lesson_library():
    # Return only library metadata, never a lesson's full block dictionary.
    result = []
    for path in settings.LESSON_DIR.glob("u*_s*.json"):
        lesson_id = path.stem.replace("_", "-")
        if not re.fullmatch(r"u\d+-s\d+", lesson_id):
            continue
        lesson = load_lesson(lesson_id)
        unit, session = map(int, re.findall(r"\d+", lesson_id))
        result.append({"id": lesson_id, "unit": unit, "session": session, "title": lesson["title"]})
    return sorted(result, key=lambda item: (item["unit"], item["session"]))


def for_guide(value, guide):
    """Project private content before it reaches any browser-facing context."""
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if key == "leader_only" or (guide == "student" and key == "answer"):
                continue
            if guide == "student" and isinstance(child, dict) and child.get("leader_only"):
                continue
            result[key] = for_guide(child, guide)
        return result
    if isinstance(value, list):
        return [for_guide(child, guide) for child in value if not (guide == "student" and isinstance(child, dict) and child.get("leader_only"))]
    return value
