"""Create legacy OCR staging data, never canonical website lesson JSON.

Use the repo-local bible-study-pdf-to-json skill to visually correct the drafts
and prepare the approved named-section format. Existing outputs are not replaced.
"""
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from statistics import median

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def lesson_pages(unit, session, guide):
    start = (8 if guide == "leader" else 6) if (unit, session) == (25, 1) else 1
    return list(range(start, start + 8))


def normalize(text):
    text = unicodedata.normalize("NFKC", text).translate(str.maketrans("’‘“”", "''\"\""))
    return re.sub(r"\s+", " ", text).strip().casefold()


def clean(text):
    text = re.sub(r"(?<=\w)-\s*\n(?=[a-z])", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"^[•*+@®&<>|=©™\s]+(?=[A-Za-z])", "", text)


QUESTION = re.compile(r"^(?:\d+[.)]\s*)?(?:what|why|how|when|where|who|which|would|do|did|can|have|has|is|are|will|should|in what|if you)\b", re.I)
REFERENCE = re.compile(r"\b(?:[123] )?(?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalm[s]?|Proverbs|Ecclesiastes|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|Jude|Revelation)\s+\d+(?::[\d–—,:; -]+)?", re.I)


def ocr_page(task):
    filename, guide, page, index, lesson_id = task
    cache = ROOT / "tmp/ocr-300" / Path(filename).stem
    cache.mkdir(parents=True, exist_ok=True)
    image_path = ROOT / "lessons/assets" / lesson_id / f"{guide}-{page:02}.jpg"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(ROOT / "source" / filename) as doc:
        pg = doc[page - 1]
        pix = pg.get_pixmap(matrix=fitz.Matrix(300/72, 300/72), alpha=False)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    if not image_path.exists():
        preview = im.copy()
        preview.thumbnail((1500, 2000))
        preview.save(image_path, quality=86, optimize=True)
    if index == 0:
        regions = [(0.04, .80, .96, .94, 6)] if guide == "student" else [(.08, .43, .65, .73, 6)]
    elif index == 2 and guide == "student":
        regions = [(.08, .05, .345, .94, 6), (.395, .11, .94, .94, 6)]
    elif index == 4 and guide == "leader":
        regions = [(.05, .81, .96, .945, 6)]
    elif index == 7 and guide == "leader":
        regions = [(.065, .04, .715, .94, 6), (.75, .035, .965, .94, 6)]
    else:
        regions = [(.065, .055, .95, .94, 3)]
    paragraphs = []
    for region_no, (x0, y0, x1, y1, psm) in enumerate(regions):
        crop = im.crop((int(x0*im.width), int(y0*im.height), int(x1*im.width), int(y1*im.height)))
        tsv_path = cache / f"{page:02}-{region_no}.tsv"
        if not tsv_path.exists():
            png = tsv_path.with_suffix('.png')
            crop.save(png)
            output = subprocess.run(["tesseract", str(png), "stdout", "--psm", str(psm), "tsv"], check=True, capture_output=True, env={**os.environ, "OMP_THREAD_LIMIT": "1"})
            tsv_path.write_bytes(output.stdout)
            png.unlink()
        words = [r for r in csv.DictReader(io.StringIO(tsv_path.read_text()), delimiter="\t", quoting=csv.QUOTE_NONE) if r["level"] == "5" and r["text"].strip()]
        lines = {}
        for r in words:
            key = (r['block_num'], r['par_num'], r['line_num'])
            lines.setdefault(key, []).append(r)
        previous = None
        for rows in lines.values():
            raw = ' '.join(r['text'] for r in rows)
            text = re.sub(r'^[^A-Za-z0-9“"‘]+', '', raw).strip()
            if not re.search(r'[A-Za-z]{2}', text): continue
            box = [min(int(r['left']) for r in rows), min(int(r['top']) for r in rows), max(int(r['left'])+int(r['width']) for r in rows), max(int(r['top'])+int(r['height']) for r in rows)]
            height = median(int(r['height']) for r in rows)
            caps = sum(c.isupper() for c in text)/max(1, sum(c.isalpha() for c in text)) > .87
            ref = bool(REFERENCE.fullmatch(text.rstrip('.')))
            style = 'reference' if ref else 'caps' if caps else 'body'
            bullet = bool(re.match(r'^[•*+¢«®©@&-]|^\S{1,2}\s+[•*+·-]', raw))
            join = previous and previous['style'] == style and style != 'reference' and not bullet and 0 <= box[1]-previous['last_box'][3] < height*1.1
            if join:
                previous['text'] = clean(previous['text']+'\n'+text)
                previous['scores'].extend(float(r['conf']) for r in rows)
                previous['bbox'] = [min(previous['bbox'][0], box[0]), min(previous['bbox'][1], box[1]), max(previous['bbox'][2], box[2]), max(previous['bbox'][3], box[3])]
                previous['last_box'] = box
            else:
                previous = {'text': text, 'scores': [float(r['conf']) for r in rows], 'bbox': box, 'style': style, 'last_box': box}
                paragraphs.append(previous)
        for para in paragraphs:
            if 'scores' in para:
                para['confidence'] = round(sum(max(0, s) for s in para.pop('scores'))/max(1,len(para['text'].split())),1)
                para['confidence'] = min(100, para['confidence'])
                para.pop('style', None); para.pop('last_box', None)
    # These display-font headings are visually transcribed, not guessed by OCR.
    fixed = {(0, 'student'): 'Christ Connection', (0, 'leader'): 'Main Point', (2, 'leader'): 'Before You Teach', (3,'leader'): 'Context', (4,'leader'): 'Kick Starter'}
    if (index, guide) in fixed:
        paragraphs.insert(0, {'text':fixed[index,guide], 'confidence':100, 'bbox':[0,0,0,0]})
    return {"guide": guide, "page": page, "index": index, "paragraphs": paragraphs, "asset": str(image_path.relative_to(ROOT / "lessons")), "size": [im.width, im.height]}


def classify(text, index, guide, reference):
    if REFERENCE.fullmatch(text.rstrip(".")):
        return "heading"
    if (index == 2 and guide == "student") or (index in (6, 7) and guide == "leader") or (guide == "student" and index >= 3):
        if "?" in text and QUESTION.match(text) and (text.upper() == text or len(text)<280):
            return "question"
    if len(text) < 160 and text.upper() == text and re.search(r"[A-Z]", text) and not text.startswith(('FATHER','LORD','JESUS,','GOD,')):
        return "heading"
    if index == 1 and re.match(r"^\d+\s+[A-Z]", text) and reference:
        return "scripture"
    if re.match(r"^[•*+] ", text):
        return "list"
    return "paragraph"


def build_lesson(unit, session, files, pages):
    lesson_id = f"u{unit}-s{session}"
    blocks, guides, shared = {}, {"leader": [], "student": []}, {}
    titles = {
        (23, 1): '“Your Sins Are Forgiven”', (23, 2): 'Send Them Out',
        (23, 3): '“The Lord of the Sabbath”', (23, 4): '“Kingdom of God”',
        (24, 1): '“The One”', (24, 2): '“God Has Visited His People!”',
        (24, 3): '“The Larger Debt”', (24, 4): '“Teach Us to Pray”',
        (24, 5): 'How the Lilies Grow', (25, 1): 'Secrets of the Kingdom',
        (25, 2): 'The Kingdom of Heaven', (25, 3): 'The Wind and the Sea Obey',
        (25, 4): '“Your Faith Has Saved You”',
    }
    for page_data in sorted(pages, key=lambda p: (p["guide"] != "student", p["index"])):
        guide, page, index = page_data["guide"], page_data["page"], page_data["index"]
        reference = ""
        for n, para in enumerate(page_data["paragraphs"], 1):
            text = para["text"]
            kind = classify(text, index, guide, reference)
            if REFERENCE.fullmatch(text.rstrip(".")):
                reference = text
            # Case and layout whitespace do not create duplicate content.
            key = normalize(text)
            source = {"guide": guide, "page": page, "region": f"b{n:03}", "bbox": para["bbox"]}
            if key in shared:
                block_id = shared[key]
                blocks[block_id]["sources"].append(source)
                if kind == "question":
                    blocks[block_id]["type"] = kind
            else:
                block_id = f"{guide}-p{page:02}-b{n:03}"
                block = {"type": kind, "text": {"en": text, "zh-Hant": None}, "sources": [source]}
                if kind == "heading": block["level"] = 2
                if kind == "scripture": block["reference"] = reference
                if kind == "list": block["items"] = [{"en": text, "zh-Hant": None}]
                if para["confidence"] < 88:
                    block["review"] = f"OCR confidence {para['confidence']}%; check source page."
                blocks[block_id] = block
                shared[key] = block_id
            if block_id not in guides[guide]:
                guides[guide].append(block_id)
        block_id = f"{guide}-p{page:02}-image"
        blocks[block_id] = {"type": "image", "text": {"en": f"Source page {page}", "zh-Hant": None}, "asset": page_data["asset"], "sources": [{"guide": guide, "page": page}], "page_image": True}
        guides[guide].append(block_id)
    return {"schema_version": 1, "id": lesson_id, "unit": unit, "session": session, "title": {"en": titles.get((unit, session), ""), "zh-Hant": None}, "sources": files, "source_pages": {g: lesson_pages(unit, session, g) for g in files}, "blocks": blocks, "guides": guides}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "tmp/extracted")
    parser.add_argument("--unit", type=int, action="append")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    lessons = {}
    for pdf in sorted((ROOT / "source").glob("*.pdf")):
        m = re.match(r"U(\d+)_S(\d+)_(LG|DDG)_", pdf.name)
        if not m: continue
        unit, session = map(int, m.group(1, 2))
        if args.unit and unit not in args.unit:
            continue
        guide = "leader" if m[3] == "LG" else "student"
        lessons.setdefault((unit, session), {})[guide] = pdf.name
    for (unit, session), files in lessons.items():
        tasks = [(filename, guide, page, index, f"u{unit}-s{session}") for guide, filename in files.items() for index, page in enumerate(lesson_pages(unit, session, guide))]
        with ThreadPoolExecutor(max_workers=4) as pool:
            pages = list(pool.map(ocr_page, tasks))
        lesson = build_lesson(unit, session, files, pages)
        out = args.output / f"{lesson['id']}.json"
        if out.exists():
            raise SystemExit(f"Refusing to overwrite {out}; select a fresh output directory.")
        out.write_text(json.dumps(lesson, ensure_ascii=False, indent=2)+"\n")
        print(lesson["id"], len(lesson["blocks"]), "blocks", flush=True)


if __name__ == "__main__":
    main()
