from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.utils.html import escape
from jsonschema import Draft202012Validator

from scripts.validate_lessons import validate
from .content import for_guide, lesson_library, load_lesson
from .i18n import BIBLE_BOOKS, SIMPLIFIED, translate_reference
from .presentation import present_sections


class ReferenceTests(SimpleTestCase):
    def test_all_66_books_in_each_language(self):
        self.assertEqual(len(BIBLE_BOOKS), 66)
        for english, chinese in BIBLE_BOOKS.items():
            for name in (english, english.upper()):
                with self.subTest(book=name):
                    self.assertEqual(translate_reference(f"{name} 1:1-3", "en"), f"{name} 1:1-3")
                    self.assertEqual(translate_reference(f"{name} 1:1-3", "zh-Hant"), f"{chinese} 1:1-3")
                    self.assertEqual(translate_reference(f"{name} 1:1-3", "zh-Hans"), f"{SIMPLIFIED.convert(chinese)} 1:1-3")

    def test_combined_references_aliases_and_boundaries(self):
        for reference, expected in (
            ("Matthew 3:13-17; John 1:29-34", "馬太福音 3:13-17; 約翰福音 1:29-34"),
            ("1 JOHN 3:1-3; 2 John 1:1; 3 John 1:2", "約翰一書 3:1-3; 約翰二書 1:1; 約翰三書 1:2"),
            ("ISAIAH 1:11-15; 6:1-8", "以賽亞書 1:11-15; 6:1-8"),
            ("Mark 1; Luke 4–5", "馬可福音 1; 路加福音 4–5"),
            ("Luke 6:21a; Philippians 4:5b", "路加福音 6:21a; 腓立比書 4:5b"),
            ("PSALM 96; Song of Songs 2:1", "詩篇 96; 雅歌 2:1"),
            ("Unknown 1:2; Bookmark 1; John explains", "Unknown 1:2; Bookmark 1; John explains"),
            ("約翰福音 3:16", "約翰福音 3:16"),
        ):
            with self.subTest(reference=reference):
                self.assertEqual(translate_reference(reference, "zh-Hant"), expected)

    def test_every_lesson_reference_is_translated_for_both_guides(self):
        for item in lesson_library():
            for guide in ("student", "leader"):
                sections, _ = present_sections(for_guide(load_lesson(item["id"]), guide), "zh-Hant")
                for section in sections:
                    for block in section["blocks"]:
                        if block["type"] == "reference":
                            with self.subTest(lesson=item["id"], guide=guide, reference=block["text"]):
                                self.assertNotRegex(block["text"], r"\b[A-Za-z]")


class ContentTests(SimpleTestCase):
    def test_all_25_lessons_follow_approved_format(self):
        schema = json.loads((settings.BASE_DIR / "lesson.schema.json").read_text())
        validator = Draft202012Validator(schema)
        library = lesson_library()
        self.assertEqual(len(library), 25)
        for item in library:
            with self.subTest(lesson=item["id"]):
                self.assertEqual(validate(load_lesson(item["id"]), validator, schema["required"]), [])

    def test_projection_preserves_shared_content_and_translation_slots(self):
        data = load_lesson("u23-s1")
        original = deepcopy(data)
        student = for_guide(data, "student")
        self.assertNotIn("before_you_teach", student)
        self.assertNotIn("prayer", student["theology_connection"])
        self.assertNotIn("answer", student["wrap_up"])
        self.assertEqual(student["discussion"][0]["questions"][0]["id"], "discussion-1")
        self.assertEqual(student["title"]["zh-Hant"], None)
        self.assertEqual(data, original)


class AccessTests(TestCase):
    def login(self, role="student"):
        return self.client.post("/login/", {"password": role})

    def test_anonymous_access_requires_login(self):
        for path in ("/", "/lessons/u23-s1/student/", "/lessons/u23-s1/leader/"):
            self.assertRedirects(self.client.get(path), "/login/")

    def test_both_passwords_and_rotation(self):
        session = self.client.session
        session["old"] = "discard"
        session.save()
        old_key = session.session_key
        self.assertRedirects(self.login(), "/")
        self.assertEqual(self.client.session["role"], "student")
        self.assertNotEqual(old_key, self.client.session.session_key)
        self.assertNotIn("old", self.client.session)
        student_key = self.client.session.session_key
        self.assertRedirects(self.login("leader"), "/")
        self.assertEqual(self.client.session["role"], "leader")
        self.assertNotEqual(student_key, self.client.session.session_key)

    def test_invalid_login(self):
        self.assertEqual(self.login("wrong").status_code, 400)
        self.assertNotIn("role", self.client.session)

    def test_csrf_is_required_and_rotated(self):
        client = Client(enforce_csrf_checks=True)
        client.get("/login/")
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post("/login/", {"password": "leader"}).status_code, 403)
        self.assertEqual(client.post("/login/", {"password": "leader", "csrfmiddlewaretoken": token}).status_code, 302)
        self.assertNotEqual(token, client.cookies["csrftoken"].value)
        self.assertEqual(client.post("/logout/").status_code, 403)

    def test_logout_is_post_only_and_clears_access(self):
        self.login("leader")
        self.assertEqual(self.client.get("/logout/").status_code, 405)
        self.assertRedirects(self.client.post("/logout/"), "/login/")
        self.assertNotIn("role", self.client.session)
        self.assertRedirects(self.client.get("/lessons/u23-s1/leader/"), "/login/")

    def test_student_cannot_request_leader_route(self):
        self.login()
        self.assertEqual(self.client.get("/lessons/u23-s1/leader/").status_code, 403)

    def test_all_student_pages_omit_private_content(self):
        self.login()
        for item in lesson_library():
            data = load_lesson(item["id"])
            response = self.client.get(f"/lessons/{item['id']}/student/?lang=en")
            with self.subTest(lesson=item["id"]):
                self.assertEqual(response.status_code, 200)
                protected = [data["context"]["content"]["en"], data["before_you_teach"]["content"]["en"], data["theology_connection"]["prayer"]["content"]["en"], data["wrap_up"]["answer"]["en"]]
                protected.extend(q["answer"]["en"] for group in data["discussion"] for q in group["questions"])
                html = response.content.decode()
                for text in protected:
                    self.assertNotIn(str(escape(text[:70])), html)
                self.assertNotIn('class="leader-answer"', html)
                self.assertNotIn('id="before_you_teach"', html)
                self.assertIn("no-store", response["Cache-Control"])

    def test_leader_can_read_both_guides(self):
        self.login("leader")
        for guide in ("student", "leader"):
            self.assertEqual(self.client.get(f"/lessons/u23-s1/{guide}/").status_code, 200)
        response = self.client.get("/lessons/u23-s1/leader/?lang=en")
        self.assertContains(response, 'class="leader-answer"')
        self.assertContains(response, "The home Jesus preached in")
        self.assertContains(response, 'data-question="discussion-1"')

    def test_private_source_and_asset_paths_are_not_served(self):
        self.login()
        for path in (
            "/source/U23_S1_LG_ESV_2026SUM.pdf", "/lessons/u23_s1.json",
            "/static/lessons/u23_s1.json", "/static/source/U23_S1_LG_ESV_2026SUM.pdf",
            "/lessons/assets/u23-s1/leader-01.jpg", "/lessons/u23-s1/leader/assets/leader-p01-image/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_unknown_guide_or_lesson_is_not_found(self):
        self.login()
        self.assertEqual(self.client.get("/lessons/u23-s1/other/").status_code, 404)
        self.assertEqual(self.client.get("/lessons/u99-s1/student/").status_code, 404)

    def test_default_language_fallback_and_remembered_choice(self):
        self.login()
        response = self.client.get("/lessons/u23-s1/student/")
        self.assertContains(response, 'lang="zh-Hant"')
        self.assertContains(response, "本課中文翻譯尚未提供")
        self.client.get("/?lang=en")
        self.assertContains(self.client.get("/"), 'lang="en"')
        self.assertContains(self.client.get("/?lang=invalid"), 'lang="zh-Hant"')

    def test_rendered_reference_uses_selected_language(self):
        self.login("leader")
        for guide in ("student", "leader"):
            for lang, reference in (("en", "Mark 2"), ("zh-Hant", "馬可福音 2"), ("zh-Hans", "马可福音 2")):
                with self.subTest(guide=guide, lang=lang):
                    response = self.client.get(f"/lessons/u23-s1/{guide}/?lang={lang}")
                    self.assertContains(response, f'<p class="reference" lang="{lang}">{reference}</p>', html=True)

    def test_simplified_chinese_is_generated_from_traditional(self):
        self.login()
        data = load_lesson("u23-s1")
        data["title"]["zh-Hant"] = "學習神的話語"
        data["main_point"]["zh-Hant"] = "這是祂的應許。"
        with TemporaryDirectory() as directory:
            Path(directory, "u23_s1.json").write_text(json.dumps(data, ensure_ascii=False))
            with override_settings(LESSON_DIR=Path(directory)):
                response = self.client.get("/lessons/u23-s1/student/?lang=zh-Hans")
        self.assertContains(response, "学习神的话语")
        self.assertContains(response, "这是祂的应许。")

    def test_html_content_is_escaped(self):
        self.login()
        data = load_lesson("u23-s1")
        data["main_point"]["en"] = '<script>alert("unsafe")</script>'
        with TemporaryDirectory() as directory:
            Path(directory, "u23_s1.json").write_text(json.dumps(data))
            with override_settings(LESSON_DIR=Path(directory)):
                response = self.client.get("/lessons/u23-s1/student/?lang=en")
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<script>alert("unsafe")</script>')
