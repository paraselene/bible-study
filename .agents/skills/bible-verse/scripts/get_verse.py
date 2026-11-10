#!/usr/bin/env python3
"""Fetch Bible verses (any version, Chinese or English) for a reference and
print them paste-ready: a citation line, then one line per verse, each line
beginning with the verse number (e.g. "16 神愛世人…"). 和合本 verses that share one
block of text (e.g. 路加福音 2:34-35) are folded into a single range-labelled line
rather than emitting a blank line for the empty member.

Everything comes live from the bolls.life API, which carries the same versions
in one consistent shape — 和合本 (CUNP / 新標點和合本), simplified, 思高本, plus ESV,
NIV, KJV, NASB, NLT, NET and many more. No API key, stdlib only.

References may use Chinese OR English book names, single verses, ranges, or a
whole chapter:
    約翰福音 3:16        John 3:16
    詩篇 23             Psalm 23            (whole chapter)
    羅馬書 8:1-4         Romans 8:1-4        (verse range)
    約翰一書 4:9-10      1 John 4:9-10
    John 3:16-4:2                            (cross-chapter range)

Usage:
    get_verse.py "<reference>" [--versions CUNP,ESV] [--json]

Default versions are 和合本 (CUNP) then ESV — the pair the translation workflow
uses. Pass --versions with any bolls codes / friendly names to change them,
e.g. --versions ESV,NIV,和合本 or --versions KJV.
"""
import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request

API = "https://bolls.life/get-text/{version}/{book}/{chapter}/"

# --------------------------------------------------------------------------- #
# Canon: (number, English name, Traditional-Chinese name, single-chapter?)
# Number is the standard 1–66 Protestant ordering bolls.life uses.
# --------------------------------------------------------------------------- #
BOOKS = [
    (1, "Genesis", "創世記", False), (2, "Exodus", "出埃及記", False),
    (3, "Leviticus", "利未記", False), (4, "Numbers", "民數記", False),
    (5, "Deuteronomy", "申命記", False), (6, "Joshua", "約書亞記", False),
    (7, "Judges", "士師記", False), (8, "Ruth", "路得記", False),
    (9, "1 Samuel", "撒母耳記上", False), (10, "2 Samuel", "撒母耳記下", False),
    (11, "1 Kings", "列王紀上", False), (12, "2 Kings", "列王紀下", False),
    (13, "1 Chronicles", "歷代志上", False), (14, "2 Chronicles", "歷代志下", False),
    (15, "Ezra", "以斯拉記", False), (16, "Nehemiah", "尼希米記", False),
    (17, "Esther", "以斯帖記", False), (18, "Job", "約伯記", False),
    (19, "Psalms", "詩篇", False), (20, "Proverbs", "箴言", False),
    (21, "Ecclesiastes", "傳道書", False), (22, "Song of Solomon", "雅歌", False),
    (23, "Isaiah", "以賽亞書", False), (24, "Jeremiah", "耶利米書", False),
    (25, "Lamentations", "耶利米哀歌", False), (26, "Ezekiel", "以西結書", False),
    (27, "Daniel", "但以理書", False), (28, "Hosea", "何西阿書", False),
    (29, "Joel", "約珥書", False), (30, "Amos", "阿摩司書", False),
    (31, "Obadiah", "俄巴底亞書", True), (32, "Jonah", "約拿書", False),
    (33, "Micah", "彌迦書", False), (34, "Nahum", "那鴻書", False),
    (35, "Habakkuk", "哈巴谷書", False), (36, "Zephaniah", "西番雅書", False),
    (37, "Haggai", "哈該書", False), (38, "Zechariah", "撒迦利亞書", False),
    (39, "Malachi", "瑪拉基書", False), (40, "Matthew", "馬太福音", False),
    (41, "Mark", "馬可福音", False), (42, "Luke", "路加福音", False),
    (43, "John", "約翰福音", False), (44, "Acts", "使徒行傳", False),
    (45, "Romans", "羅馬書", False), (46, "1 Corinthians", "哥林多前書", False),
    (47, "2 Corinthians", "哥林多後書", False), (48, "Galatians", "加拉太書", False),
    (49, "Ephesians", "以弗所書", False), (50, "Philippians", "腓立比書", False),
    (51, "Colossians", "歌羅西書", False),
    (52, "1 Thessalonians", "帖撒羅尼迦前書", False),
    (53, "2 Thessalonians", "帖撒羅尼迦後書", False),
    (54, "1 Timothy", "提摩太前書", False), (55, "2 Timothy", "提摩太後書", False),
    (56, "Titus", "提多書", False), (57, "Philemon", "腓利門書", True),
    (58, "Hebrews", "希伯來書", False), (59, "James", "雅各書", False),
    (60, "1 Peter", "彼得前書", False), (61, "2 Peter", "彼得後書", False),
    (62, "1 John", "約翰一書", False), (63, "2 John", "約翰二書", True),
    (64, "3 John", "約翰三書", True), (65, "Jude", "猶大書", True),
    (66, "Revelation", "啟示錄", False),
]

# Extra aliases (abbreviations / alternates) → book number. Full English and
# Chinese names are registered automatically below.
ALIASES = {
    "gen": 1, "ge": 1, "exod": 2, "exo": 2, "ex": 2, "lev": 3, "lv": 3,
    "num": 4, "nu": 4, "nm": 4, "deut": 5, "dt": 5, "josh": 6, "jos": 6,
    "judg": 7, "jdg": 7, "rth": 8, "ru": 8, "1sam": 9, "1sa": 9, "2sam": 10,
    "2sa": 10, "1kgs": 11, "1ki": 11, "2kgs": 12, "2ki": 12, "1chr": 13,
    "1ch": 13, "2chr": 14, "2ch": 14, "neh": 16, "esth": 17, "est": 17,
    "ps": 19, "psa": 19, "psalm": 19, "prov": 20, "pr": 20, "eccl": 21,
    "ecc": 21, "song": 22, "sos": 22, "songofsongs": 22, "isa": 23, "is": 23,
    "jer": 24, "lam": 25, "ezek": 26, "eze": 26, "dan": 27, "da": 27,
    "hos": 28, "obad": 31, "ob": 31, "jon": 32, "mic": 33, "nah": 34,
    "hab": 35, "zeph": 36, "zep": 36, "hag": 37, "zech": 38, "zec": 38,
    "mal": 39, "matt": 40, "mt": 40, "mk": 41, "mar": 41, "lk": 42, "luk": 42,
    "jn": 43, "joh": 43, "rom": 45, "ro": 45, "1cor": 46, "1co": 46,
    "2cor": 47, "2co": 47, "gal": 48, "ga": 48, "eph": 49, "phil": 50,
    "php": 50, "col": 51, "1thess": 52, "1th": 52, "2thess": 53, "2th": 53,
    "1tim": 54, "1ti": 54, "2tim": 55, "2ti": 55, "tit": 56, "phlm": 57,
    "phm": 57, "heb": 58, "jas": 59, "jms": 59, "1pet": 60, "1pe": 60,
    "2pet": 61, "2pe": 61, "1jn": 62, "1jo": 62, "2jn": 63, "2jo": 63,
    "3jn": 64, "3jo": 64, "rev": 66, "rv": 66,
    # Common Chinese single/double-char abbreviations (和合本 style).
    "創": 1, "出": 2, "利": 3, "民": 4, "申": 5, "書": 6, "士": 7, "得": 8,
    "撒上": 9, "撒下": 10, "王上": 11, "王下": 12, "代上": 13, "代下": 14,
    "拉": 15, "尼": 16, "斯": 17, "伯": 18, "詩": 19, "箴": 20, "傳": 21,
    "歌": 22, "賽": 23, "耶": 24, "哀": 25, "結": 26, "但": 27, "何": 28,
    "珥": 29, "摩": 30, "俄": 31, "拿": 32, "彌": 33, "鴻": 34, "哈": 35,
    "番": 36, "該": 37, "亞": 38, "瑪": 39, "太": 40, "可": 41, "路": 42,
    "約": 43, "徒": 44, "羅": 45, "林前": 46, "林後": 47, "加": 48, "弗": 49,
    "腓": 50, "西": 51, "帖前": 52, "帖後": 53, "提前": 54, "提後": 55,
    "多": 56, "門": 57, "來": 58, "雅": 59, "彼前": 60, "彼後": 61,
    "約一": 62, "約二": 63, "約三": 64, "猶": 65, "啟": 66,
}

# Friendly / Chinese version names → bolls.life translation code.
VERSION_ALIASES = {
    "和合本": "CUNP", "cuv": "CUNP", "cunp": "CUNP", "新標點和合本": "CUNP",
    "新标点和合本": "CUNPS", "和合本简体": "CUNPS", "和合本簡體": "CUNPS",
    "简体": "CUNPS", "cunps": "CUNPS", "和合本(舊)": "CUV", "cuv-spaced": "CUV",
    "思高": "ChiSB", "思高本": "ChiSB", "chisb": "ChiSB",
}
# bolls codes whose text is Chinese — drives which book name the citation uses.
CHINESE_VERSIONS = {"CUNP", "CUNPS", "CUV", "ChiSB", "PCB", "PCBS", "CUNP23"}
# Pretty label for the citation parenthetical.
VERSION_LABEL = {
    "CUNP": "和合本", "CUNPS": "和合本简体", "CUV": "和合本", "ChiSB": "思高本",
}

NUM_TO_BOOK = {b[0]: b for b in BOOKS}


def build_lookup():
    """Map every normalized name/alias → book number."""
    lut = {}

    def norm(s):
        return re.sub(r"[\s.]", "", s).lower()

    for num, en, zh, _ in BOOKS:
        lut[norm(en)] = num          # full English
        lut[norm(zh)] = num          # full Chinese
        lut[norm(en.replace(" ", ""))] = num
    for alias, num in ALIASES.items():
        lut[norm(alias)] = num
    return lut


LOOKUP = build_lookup()


# --------------------------------------------------------------------------- #
# Reference parsing
# --------------------------------------------------------------------------- #
FULLWIDTH = {ord("："): ":", ord("．"): ".", ord("－"): "-", ord("–"): "-",
             ord("—"): "-", ord("　"): " "}
for i in range(10):  # full-width digits → ASCII
    FULLWIDTH[ord("０") + i] = str(i)


def parse_reference(ref):
    """Parse 'Book C[:V[-V2]]' (EN or ZH) → (book_num, start, end).

    start/end are (chapter, verse) tuples; verse is None for a whole chapter.
    Raises ValueError with a helpful message on anything unrecognized.
    """
    ref = ref.translate(FULLWIDTH).strip()

    # Trailing numeric locator: C, C:V, C:V-V2, or C1:V1-C2:V2.
    m = re.search(
        r"(\d+)\s*(?::\s*(\d+))?\s*(?:-\s*(\d+)\s*(?::\s*(\d+))?)?\s*$", ref)
    if not m:
        raise ValueError(f"No chapter/verse found in {ref!r} "
                         "(try e.g. 'John 3:16' or '約翰福音 3:16').")
    book_str = ref[:m.start()].strip()
    if not book_str:
        raise ValueError(f"No book name found in {ref!r}.")

    num = resolve_book(book_str)
    a, b, c, d = m.groups()
    single = NUM_TO_BOOK[num][3]

    if b is None and c is None:
        # One bare number. For multi-chapter books it's a chapter; for
        # single-chapter books (Jude, Philemon…) it's a verse in chapter 1.
        return (num, (1, int(a)), (1, int(a))) if single else \
               (num, (int(a), None), (int(a), None))
    if c is not None and d is not None:        # C1:V1 - C2:V2
        return num, (int(a), int(b)), (int(c), int(d))
    if b is not None and c is not None:        # C:V1 - V2
        return num, (int(a), int(b)), (int(a), int(c))
    return num, (int(a), int(b)), (int(a), int(b))   # C:V


def resolve_book(s):
    key = re.sub(r"[\s.]", "", s).lower()
    if key in LOOKUP:
        return LOOKUP[key]
    # Tolerate a trailing 書/福音 etc. already in the full names; try a loose
    # prefix match against Chinese names for things like '約翰' → 約翰福音.
    for num, _, zh, _ in BOOKS:
        if zh.startswith(s) or s.startswith(zh):
            return num
    raise ValueError(f"Unknown book {s!r}. Use a full name like 'John' / "
                     "'約翰福音', or a standard abbreviation.")


def resolve_version(v):
    v = v.strip()
    return VERSION_ALIASES.get(v, VERSION_ALIASES.get(v.lower(), v.upper()))


# --------------------------------------------------------------------------- #
# Fetch + clean
# --------------------------------------------------------------------------- #
_chapter_cache = {}


def fetch_chapter(version, book, chapter):
    key = (version, book, chapter)
    if key in _chapter_cache:
        return _chapter_cache[key]
    url = API.format(version=version, book=book, chapter=chapter)
    req = urllib.request.Request(url, headers={"User-Agent": "bible-verse-skill"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ValueError(f"{version} {book}/{chapter}: HTTP {e.code} "
                         f"(unknown version code {version!r}?)")
    except urllib.error.URLError as e:
        raise ValueError(f"Network error reaching bolls.life: {e.reason}")
    verses = {v["verse"]: clean(v.get("text", "")) for v in data}
    _chapter_cache[key] = verses
    return verses


_CJK = r"㐀-鿿豈-﫿"


def clean(text):
    """Strip bolls markup → readable plain text."""
    text = re.sub(r"<S>.*?</S>", "", text)        # Strong's numbers
    text = re.sub(r"<sup>.*?</sup>", "", text)     # footnote markers
    text = re.sub(r"<[^>]+>", "", text)            # any remaining tags (<i>,<e>,<a>)
    text = html.unescape(text)
    text = re.sub(rf"(?<=[{_CJK}])\s+(?=[{_CJK}])", "", text)  # de-space CJK (old CUV)
    return re.sub(r"\s+", " ", text).strip()


def collect_verses(version, start, end):
    """Return ordered list of (chapter, verse, text) from start..end inclusive.

    Whole-chapter requests (verse is None) pull every verse in the chapter.
    """
    (c1, v1), (c2, v2) = start, end
    out = []
    for ch in range(c1, c2 + 1):
        verses = fetch_chapter(version, _book_num, ch)
        nums = sorted(verses)
        lo = v1 if (ch == c1 and v1 is not None) else (nums[0] if nums else 1)
        hi = v2 if (ch == c2 and v2 is not None) else (nums[-1] if nums else 0)
        for n in nums:
            if lo <= n <= hi:
                out.append((ch, n, verses[n]))
    return out


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def citation(book_num, version, start, end):
    en, zh, single = NUM_TO_BOOK[book_num][1], NUM_TO_BOOK[book_num][2], NUM_TO_BOOK[book_num][3]
    name = zh if version in CHINESE_VERSIONS else en
    (c1, v1), (c2, v2) = start, end
    if v1 is None:                       # whole chapter
        loc = f"{c1}" if c1 == c2 else f"{c1}-{c2}"
    elif single:                         # single-chapter book: verse only (Jude 3)
        loc = f"{v1}" if v1 == v2 else f"{v1}-{v2}"
    elif c1 == c2:
        loc = f"{c1}:{v1}" if v1 == v2 else f"{c1}:{v1}-{v2}"
    else:
        loc = f"{c1}:{v1}-{c2}:{v2}"
    label = VERSION_LABEL.get(version, version)
    return f"{name} {loc}（{label}）" if version in CHINESE_VERSIONS \
        else f"{name} {loc} ({label})"


def group_verses(verses):
    """Fold verses that share one block of text into a single display group.

    和合本 frequently merges adjacent verses (e.g. 路加福音 2:34-35) into one
    inseparable block; bolls puts the whole text on one verse number and leaves
    its neighbour(s) empty. Emitting the empty one as its own blank line is wrong —
    the verses can't be split — so each empty verse is absorbed into the verse that
    carries the text and the pair is labelled as a range ('34-35 …').

    Returns a list of [start, end, text]; start/end are (chapter, verse) tuples,
    equal when the group is a lone verse.
    """
    groups = []      # each: [start, end, text]
    pending = []     # leading empty verses awaiting the next verse with text
    for ch, n, t in verses:
        if t:
            start = pending[0] if pending else (ch, n)
            groups.append([start, (ch, n), t])
            pending = []
        elif groups:
            groups[-1][1] = (ch, n)        # absorb into the preceding text block
        else:
            pending.append((ch, n))         # text must be in a verse still to come
    if pending:                             # nothing but empty verses to show
        groups.append([pending[0], pending[-1], ""])
    return groups


def verse_label(start, end, multi_chapter):
    """Prefix for a display group: a single number, or a range when verses merged.
    Cross-chapter requests use 'chapter:verse' so verse 1 of two chapters can't
    collide; same-chapter ranges read as plain '34-35'."""
    (c1, v1), (c2, v2) = start, end
    def point(c, v):
        return f"{c}:{v}" if multi_chapter else str(v)
    if start == end:
        return point(c1, v1)
    if multi_chapter and c1 != c2:
        return f"{c1}:{v1}-{c2}:{v2}"
    if multi_chapter:
        return f"{c1}:{v1}-{v2}"
    return f"{v1}-{v2}"


def format_lines(groups, multi_chapter):
    """One line per display group, prefixed with its verse number/range — e.g.
    '16 神愛世人…' or, for 和合本's merged verses, '34-35 …'."""
    return "\n".join(
        f"{verse_label(start, end, multi_chapter)} {t}".rstrip()
        for start, end, t in groups
    )


def verse_record(start, end, text):
    """JSON form of a display group. A merged group carries verse_end (and
    chapter_end when the merge crosses a chapter) alongside its start verse."""
    rec = {"chapter": start[0], "verse": start[1], "text": text}
    if end != start:
        if end[0] != start[0]:
            rec["chapter_end"] = end[0]
        rec["verse_end"] = end[1]
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference", help="e.g. 'John 3:16' or '約翰福音 3:16-18'")
    ap.add_argument("--versions", default="CUNP,ESV",
                    help="comma-separated versions/aliases (default 和合本,ESV)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    try:
        book_num, start, end = parse_reference(args.reference)
    except ValueError as e:
        sys.exit(f"Error: {e}")

    global _book_num
    _book_num = book_num
    versions = [resolve_version(v) for v in args.versions.split(",") if v.strip()]

    multi_chapter = start[0] != end[0]
    results = []
    for ver in versions:
        try:
            verses = collect_verses(ver, start, end)
        except ValueError as e:
            sys.exit(f"Error: {e}")
        if not verses:
            sys.exit(f"Error: no verses found for that reference in {ver} "
                     "(check the chapter/verse exists in this version).")
        groups = group_verses(verses)
        results.append({
            "version": ver,
            "citation": citation(book_num, ver, start, end),
            "text": format_lines(groups, multi_chapter),
            "verses": [verse_record(s, e, t) for s, e, t in groups],
        })

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    for r in results:
        print(r["citation"])
        print(r["text"])
        print()


if __name__ == "__main__":
    main()
