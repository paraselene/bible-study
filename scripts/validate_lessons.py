"""Validate lesson JSONs against the user-approved u23_s1.json format."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def normalize(text):
    return re.sub(r"[\W_]", "", unicodedata.normalize("NFKC", text).casefold())


def walk(value, path=()):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, (*path, index))


def validate(lesson, validator, fields):
    errors = [f"{'.'.join(map(str, error.absolute_path))}: {error.message}" for error in validator.iter_errors(lesson)]
    if errors:
        return errors
    if list(lesson) != fields:
        errors.append("Top-level sections must follow the approved names and order.")
    questions = [node for _, node in walk(lesson) if "question" in node]
    ids = [node.get("id") for node in questions]
    if len(ids) != len(set(ids)):
        errors.append("Question IDs must be unique within a lesson.")
    wording = [normalize(node["question"].get("en", "")) for node in questions if isinstance(node["question"], dict)]
    if any(count > 1 for count in Counter(wording).values()):
        errors.append("A shared question is duplicated instead of being stored once.")
    for path, node in walk(lesson):
        if "en" in node and not node["en"].strip():
            errors.append(f"{path}: English text is empty.")
        if "reference" in node and not re.search(r"\d", node["reference"]):
            errors.append(f"{path}: Scripture reference has no chapter number.")
        if "en" in node and re.search(r"\bsession\s+\d+\s*\||\bOCR confidence\b|\bcheck source page\b", node["en"], re.I):
            errors.append(f"{path}: Printed footer or OCR metadata remains.")
    for index, devotion in enumerate(lesson.get("devotions", [])):
        content = normalize(devotion.get("content", {}).get("en", ""))
        prayer = normalize(devotion.get("prayer", {}).get("en", ""))
        if len(content) > 100 and content in prayer:
            errors.append(f"devotions.{index}.prayer: The reading was copied into the prayer.")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args()
    schema = json.loads((ROOT / "lesson.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    fields = schema["required"]
    files = args.files or sorted((ROOT / "lessons").glob("u*_s*.json"))
    if not files:
        parser.error("No lesson JSONs found.")
    failed = False
    for path in files:
        try:
            lesson = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            print(f"FAIL {path.name}: {exc}")
            failed = True
            continue
        errors = validate(lesson, validator, fields)
        if errors:
            failed = True
            print(f"FAIL {path.name}")
            for error in errors:
                print(f"  {error}")
        else:
            print(f"OK   {path.name}")
    print(f"{len(files)} lessons checked.")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
