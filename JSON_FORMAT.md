# Approved lesson JSON format

**Approved by the user on 2026-10-24.**

[`lessons/u23_s1.json`](lessons/u23_s1.json) is the approved reference. Every lesson JSON must follow its structure. Do not change this format without the user's approval.

- Use the same named lesson sections and their order: `title`, `main_point`, `christ_connection`, `scripture`, `before_you_teach`, `context`, `theology_connection`, `kick_starter`, `intro_activity`, `cultural_connection`, `discussion`, `wrap_up`, `devotions`.
- Store text as `{ "en": "…", "zh-Hant": null }`; retain existing Traditional Chinese translations. Simplified Chinese is generated when rendering.
- Scripture passages contain `title`, `reference`, and `content`.
- Group commentary under its printed teaching title. Each group contains `title` and `content`; its entries contain `reference` and `content`. Preserve the source's actual grouping and order.
- Questions contain a stable `id` and `question`; attach the supplied leader response as `answer`. Store shared LG/DDG text once. Keep leader-only teaching sections marked `leader_only`.
- Keep the number of passages, commentary entries, questions, and daily readings appropriate to the actual lesson. A kickoff fact uses `content` instead of inventing a question.
- Omit printed page numbers, repeated unit/session headers, running footers, OCR/layout metadata, block dictionaries, guide-reference maps, and approval metadata from lesson JSON.
- Extract the standard eight-page lesson sections only. U24 S5 uses pages 1–8 in both guides; U25 S1 uses LG pages 8–15 and DDG pages 6–13. Other supplied lessons use pages 1–8.

Changes to lesson wording must preserve question IDs and existing translations.

Validate all lesson files with:

```sh
.venv/bin/python scripts/validate_lessons.py
```

[`lesson.schema.json`](lesson.schema.json) defines the approved shape. Validation checks the section order, required content and leader answers, bilingual fields, Scripture references, and unique question IDs.
