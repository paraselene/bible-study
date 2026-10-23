from opencc import OpenCC

LANGUAGES = {"en": "English", "zh-Hant": "繁體中文", "zh-Hans": "简体中文"}
SIMPLIFIED = OpenCC("t2s")
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


def labels(lang):
    return {key: pair[0] if lang == "en" else SIMPLIFIED.convert(pair[1]) if lang == "zh-Hans" else pair[1] for key, pair in LABELS.items()}


def context(request):
    lang = getattr(request, "study_language", "zh-Hant")
    return {"lang": lang, "languages": LANGUAGES, "ui": labels(lang)}
