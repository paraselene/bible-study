import re

from opencc import OpenCC

LANGUAGES = {
    "en": "English", "zh-Hant": "繁體中文", "zh-Hans": "简体中文",
    "en-zh-Hant": "English / 繁體中文", "en-zh-Hans": "English / 简体中文",
}
SIMPLIFIED = OpenCC("t2s")
BIBLE_BOOKS = {
    "Genesis": "創世記",
    "Exodus": "出埃及記",
    "Leviticus": "利未記",
    "Numbers": "民數記",
    "Deuteronomy": "申命記",
    "Joshua": "約書亞記",
    "Judges": "士師記",
    "Ruth": "路得記",
    "1 Samuel": "撒母耳記上",
    "2 Samuel": "撒母耳記下",
    "1 Kings": "列王紀上",
    "2 Kings": "列王紀下",
    "1 Chronicles": "歷代志上",
    "2 Chronicles": "歷代志下",
    "Ezra": "以斯拉記",
    "Nehemiah": "尼希米記",
    "Esther": "以斯帖記",
    "Job": "約伯記",
    "Psalms": "詩篇",
    "Proverbs": "箴言",
    "Ecclesiastes": "傳道書",
    "Song of Solomon": "雅歌",
    "Isaiah": "以賽亞書",
    "Jeremiah": "耶利米書",
    "Lamentations": "耶利米哀歌",
    "Ezekiel": "以西結書",
    "Daniel": "但以理書",
    "Hosea": "何西阿書",
    "Joel": "約珥書",
    "Amos": "阿摩司書",
    "Obadiah": "俄巴底亞書",
    "Jonah": "約拿書",
    "Micah": "彌迦書",
    "Nahum": "那鴻書",
    "Habakkuk": "哈巴谷書",
    "Zephaniah": "西番雅書",
    "Haggai": "哈該書",
    "Zechariah": "撒迦利亞書",
    "Malachi": "瑪拉基書",
    "Matthew": "馬太福音",
    "Mark": "馬可福音",
    "Luke": "路加福音",
    "John": "約翰福音",
    "Acts": "使徒行傳",
    "Romans": "羅馬書",
    "1 Corinthians": "哥林多前書",
    "2 Corinthians": "哥林多後書",
    "Galatians": "加拉太書",
    "Ephesians": "以弗所書",
    "Philippians": "腓立比書",
    "Colossians": "歌羅西書",
    "1 Thessalonians": "帖撒羅尼迦前書",
    "2 Thessalonians": "帖撒羅尼迦後書",
    "1 Timothy": "提摩太前書",
    "2 Timothy": "提摩太後書",
    "Titus": "提多書",
    "Philemon": "腓利門書",
    "Hebrews": "希伯來書",
    "James": "雅各書",
    "1 Peter": "彼得前書",
    "2 Peter": "彼得後書",
    "1 John": "約翰一書",
    "2 John": "約翰二書",
    "3 John": "約翰三書",
    "Jude": "猶大書",
    "Revelation": "啟示錄",
}
BOOK_NAMES = {name.casefold(): chinese for name, chinese in BIBLE_BOOKS.items()}
BOOK_NAMES.update({"psalm": "詩篇", "song of songs": "雅歌"})
BOOK_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(name) for name in sorted(BOOK_NAMES, key=len, reverse=True)) + r")\b(?=\s+\d)",
    re.IGNORECASE,
)


def translate_reference(reference, lang):
    if lang == "en":
        return reference
    text = BOOK_PATTERN.sub(lambda match: BOOK_NAMES[match[0].casefold()], reference)
    return SIMPLIFIED.convert(text) if lang == "zh-Hans" else text


LABELS = {
    "brand": ("The Gospel Project", "福音研經"),
    "library": ("Lesson library", "課程目錄"),
    "library_intro": ("Read, reflect, and grow together.", "一同研讀、反思，在真道中成長。"),
    "password": ("Password", "密碼"),
    "login": ("Enter", "進入課程"),
    "login_intro": ("Enter your group’s shared password to begin.", "請輸入小組共用密碼，開始研讀。"),
    "invalid": ("Incorrect password. Please try again.", "密碼不正確，請再試一次。"),
    "logout": ("Log out", "登出"),
    "student": ("Disciple guide", "門徒研習手冊"),
    "leader": ("Leader guide", "組長帶領手冊"),
    "unit": ("Unit", "單元"),
    "session": ("Session", "課"),
    "language": ("Language", "語言"),
    "contents": ("Sections", "章節導覽"),
    "fallback": ("Chinese lesson translations are not available yet. Missing translations are shown in English.", "本課中文翻譯尚未提供，未翻譯的內容會顯示英文。"),
    "answer": ("Your reflection", "我的回應"),
    "saved": ("Saved in this browser", "已儲存在此瀏覽器"),
    "saving": ("Saving…", "儲存中⋯"),
    "save_error": ("Unable to save. Keep this page open and copy your answers before leaving.", "無法儲存。請保持頁面開啟，離開前先複製你的回應。"),
    "cleared": ("This lesson’s answers have been cleared.", "已清除此課的回應。"),
    "clear": ("Clear lesson answers", "清除此課回應"),
    "confirm_clear": ("Clear all answers for this lesson in both guides? This cannot be undone.", "要清除此課在兩本手冊中的所有回應嗎？此操作無法還原。"),
    "cancel": ("Cancel", "取消"),
    "confirm": ("Clear answers", "確定清除"),
    "privacy": ("Answers stay in this browser, including after logout. Others using this browser can read them. Clearing browser storage removes them.", "回應只儲存在此瀏覽器，登出後仍會保留。使用同一瀏覽器的人可以讀取；清除瀏覽器資料會刪除回應。"),
    "review": ("OCR text needs checking against the source page.", "此處文字辨識有疑問，請對照原頁。"),
    "source": ("View source page", "查看原頁"),
    "page": ("Source page", "原檔頁碼"),
    "skip": ("Skip to content", "跳至內容"),
    "top": ("Back to top", "回到頁首"),
    "denied": ("This guide is available to leaders only.", "此手冊僅供組長使用。"),
    "apply": ("Apply", "切換"),
    "leader_answer": ("Leader’s notes", "組長參考答案"),
    "main_point": ("Main point", "本課重點"),
    "christ_connection": ("Christ connection", "與基督的連結"),
    "scripture": ("Scripture", "研讀經文"),
    "before_you_teach": ("Before you teach", "帶領前的預備"),
    "context": ("Context", "經文背景"),
    "theology_connection": ("Theology connection", "神學連結"),
    "kick_starter": ("Kick starter", "暖身活動"),
    "intro_activity": ("Intro activity", "引入活動"),
    "cultural_connection": ("Cultural connection", "文化連結"),
    "discussion": ("Discussion", "討論"),
    "wrap_up": ("Wrap-up", "總結與回應"),
    "devotions": ("Daily devotions", "每日靈修"),
    "commentary": ("Biblical commentary", "經文釋義"),
    "prayer": ("Prayer", "禱告"),
    "supplies": ("Supplies", "所需物品"),
    "lessons_count": ("Lessons", "課程"),
}


def translate(value, lang):
    if lang == "en":
        return value.get("en", ""), False
    text = value.get("zh-Hant")
    if not text:
        return value["en"], True
    return (SIMPLIFIED.convert(text) if lang == "zh-Hans" else text), False


def display_text(value, lang):
    bilingual = lang.startswith("en-zh-")
    chinese = lang.removeprefix("en-")
    text, missing = translate(value, chinese if bilingual else lang)
    return {
        "text": value["en"] if bilingual else text,
        "text_lang": "en" if bilingual or missing else lang,
        "secondary": text if bilingual and not missing else "",
        "secondary_lang": chinese,
        "fallback": missing,
    }


def labels(lang):
    if lang.startswith("en-zh-"):
        chinese = labels(lang.removeprefix("en-"))
        return {key: f"{pair[0]} / {chinese[key]}" for key, pair in LABELS.items()}
    return {key: pair[0] if lang == "en" else SIMPLIFIED.convert(pair[1]) if lang == "zh-Hans" else pair[1] for key, pair in LABELS.items()}


def context(request):
    lang = getattr(request, "study_language", "zh-Hant")
    return {"lang": lang, "html_lang": "en" if lang.startswith("en-") else lang, "languages": LANGUAGES, "ui": labels(lang)}
