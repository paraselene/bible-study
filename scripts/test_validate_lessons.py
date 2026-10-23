import copy
import json
import unittest

from jsonschema import Draft202012Validator

from validate_lessons import ROOT, validate


class ApprovedFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads((ROOT / "lessons/u23_s1.json").read_text())
        schema = json.loads((ROOT / "lesson.schema.json").read_text())
        cls.validator = Draft202012Validator(schema)
        cls.fields = schema["required"]

    def errors(self, data):
        return validate(data, self.validator, self.fields)

    def test_approved_example(self):
        self.assertEqual(self.errors(self.example), [])

    def test_commentary_must_retain_title_groups(self):
        data = copy.deepcopy(self.example)
        data["before_you_teach"]["commentary"] = [
            entry for group in data["before_you_teach"]["commentary"]
            for entry in group["content"]
        ]
        self.assertTrue(self.errors(data))

    def test_missing_leader_answer_is_rejected(self):
        data = copy.deepcopy(self.example)
        del data["discussion"][0]["questions"][0]["answer"]
        self.assertTrue(self.errors(data))

    def test_saved_answer_ids_cannot_collide(self):
        data = copy.deepcopy(self.example)
        data["devotions"][0]["questions"][0]["id"] = "discussion-1"
        self.assertTrue(self.errors(data))

    def test_empty_content_and_ocr_metadata_are_rejected(self):
        data = copy.deepcopy(self.example)
        data["scripture"]["content"][1]["content"]["en"] = ""
        data["source_pages"] = [1, 2, 3]
        self.assertTrue(self.errors(data))

    def test_simplified_translation_is_not_stored(self):
        data = copy.deepcopy(self.example)
        data["title"]["zh-Hans"] = "标题"
        self.assertTrue(self.errors(data))

    def test_selected_pages_exclude_front_and_end_matter(self):
        from extract_lessons import lesson_pages

        self.assertEqual(lesson_pages(25, 1, "leader"), list(range(8, 16)))
        self.assertEqual(lesson_pages(25, 1, "student"), list(range(6, 14)))
        for unit, session in [(20, 1), (21, 4), (22, 1), (24, 5)]:
            self.assertEqual(lesson_pages(unit, session, "leader"), list(range(1, 9)))

    def test_reading_cannot_be_copied_into_prayer(self):
        data = copy.deepcopy(self.example)
        devotion = data["devotions"][0]
        devotion["prayer"]["en"] = devotion["content"]["en"] + devotion["prayer"]["en"]
        self.assertTrue(self.errors(data))

    def test_invalid_top_level_type_reports_errors(self):
        self.assertTrue(self.errors([]))

    def test_running_footer_is_rejected(self):
        data = copy.deepcopy(self.example)
        data["devotions"][0]["content"]["en"] += " session 1 | Your Sins Are Forgiven"
        self.assertTrue(self.errors(data))


if __name__ == "__main__":
    unittest.main()
