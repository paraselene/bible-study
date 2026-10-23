---
name: bible-study-pdf-to-json
description: Extract paired Bible-study Leader Guide (LG) and Daily Discipleship Guide (DDG) PDFs into the approved shared bilingual lesson JSON used by the BibleStudy website. Use for new lessons, extraction corrections, and additional units in this curriculum.
---

# Bible study PDF to JSON

Prepare source-faithful lesson JSON that the website can load directly. Use Luna subagents for extraction and preparation when delegation is available; the coordinating agent verifies the files and installs them in the website's lesson directory. If Luna is unavailable, report that limitation before using an otherwise authorized local extraction workflow.

## Establish the format and scope

- Read the project's `JSON_FORMAT.md` and approved `lessons/u23_s1.json` (or root `u23_s1.json` in an older checkout). These take precedence over bundled examples. For a new checkout without them, use [the approved example](references/approved-example.json) and [its schema](references/lesson.schema.json).
- The approved named sections are `title`, `main_point`, `christ_connection`, `scripture`, `before_you_teach`, `context`, `theology_connection`, `kick_starter`, `intro_activity`, `cultural_connection`, `discussion`, `wrap_up`, and `devotions`, in that order. Keep this simple structure; do not introduce a block dictionary, guide-reference map, or generic document engine.
- Store English and Traditional Chinese as `{ "en": "...", "zh-Hant": null }`. Keep existing translations when correcting English. Do not store Simplified Chinese; the website converts Traditional Chinese at render time.
- If the user has already approved the format, proceed with the requested batch. For a genuinely new format, prepare one complete real lesson for review before converting the batch.

## Inventory and select source pages

Pair LG and DDG by unit/session, then inspect every PDF's page count and native text. Prefer native text when it is complete and readable. An outlined or scanned PDF may have no extractable text; render it at about 250–300 dpi and use OCR as a draft for visual transcription.

Find the session section by its content, rather than assuming every file starts at its lesson. For the supplied Units 20–25, use the eight-page lesson sequence: LG introduction, Scripture, Before You Teach, Context/Theology, Kick Starter, Intro Options, and two Discussion pages; DDG introduction, Scripture, Discussion, then five devotional days. U24 S5 uses pages 1–8 in both PDFs; U25 S1 uses LG pages 8–15 and DDG pages 6–13. Verify these offsets against the actual files when processing another edition.

Exclude front matter, contributor biographies, advertisements, and end matter outside the requested lesson section. Ignore folios, running headers/footers, and repeated unit/session labels. Keep Bible chapter/verse numbers and meaningful footnote indicators.

## Extract with Luna

Delegate bounded units or sessions to `gpt-6-luna` when that model is available. Give each agent the approved example/schema, selected source PDFs, output directory, project instructions, and exclusive ownership of its lesson filenames. Require actual written files and a validation result; a status message or a contact sheet alone is not a completed extraction. Assign another available Luna agent or narrow the task if an agent stops without delivering its files.

Keep OCR/native-text drafts and rendered pages in a temporary audit directory, separate from production JSON. Use the PDF skill if available for rendering; it is not a prerequisite for this skill.

Correct reading order from the page layout. Extract two-column answers by their actual column boundaries; do not flatten the full page in geometric row order. On the final LG page, separate the wide discussion column from the narrow wrap-up sidebar. Native PDF text can interleave columns too.

The supplied material is the content authority. Do not invent questions, rewrite supplied leader answers, generate Scripture quotations from memory, or substitute a familiar prayer. Review all selected pages for completeness, and inspect uncertain text or narrow columns at full resolution.

## Preserve the lesson structure

- Store shared LG/DDG main points, Christ connections, quotations, theology/cultural text, and questions once. Attach each supplied LG response to its question as `answer`; mark additional teaching sections `leader_only`.
- Scripture has its printed title and overview reference, followed by passage objects containing `title`, `reference`, and `content`.
- Commentary groups have `title` and `content`; their entries have `reference` and `content`. Use the actual printed title grouping. Repeated references can introduce different quotations: retain each as a separate entry, in source order.
- Give questions stable, lesson-local IDs such as `discussion-1`, `wrap-up`, `activity-1`, and `day-1-question-1`. Preserve existing IDs on correction so browser answers survive. Do not renumber unrelated questions.
- The usual DDG discussion page has six discussion prompts plus a seventh wrap-up prompt. Keep the wrap-up separate and pair it with the LG sidebar response. Check the actual source instead of forcing every future curriculum into these counts.
- Separate devotional `content`, `questions`, and `prayer`. Uppercase question fragments and entire reading paragraphs must not leak into prayer fields. Read the prayer itself; do not select the final paragraph merely because an OCR block was labeled a heading.
- A kickoff prompt uses `id` and `question`; a kickoff fact uses `content`. Follow actual source wording and variable passage/question counts.
- Keep source paths, page coordinates, OCR confidence, review flags, schema versions, and approval metadata out of runtime lesson JSON. Keep unresolved transcription notes in a separate audit note and disclose them; do not silently guess or claim the affected lesson is verified.

## Check and install

Write candidates to a staging directory first. Run the project's validator, or the bundled fallback:

```sh
python /absolute/path/to/bible-study-pdf-to-json/scripts/validate_lessons.py /path/to/staged/u20_s1.json
```

The validator needs `jsonschema`. Use an existing project environment when possible. It checks the approved shape, section order, required content/answers, allowed language keys, duplicate question IDs/wording, and reading text copied into prayers. It does not prove that the transcription is correct.

Check titles, every commentary reference/title association, Bible passage completeness, leader question/answer pairing, devotional references, and complete paragraph endings against the source. Look for empty placeholders, missing answer objects, duplicated paragraphs, decorative OCR noise, stray sidebar letters, and corrupted footnote symbols. Correct failures before reporting completion. Preserve approved examples and existing translations.

After checks pass, place canonical files at `lessons/u<unit>_s<session>.json` or the website's established content directory. Archive superseded extraction drafts outside that directory. Verify the website reads these actual files and strips leader-only sections and `answer` fields on the server for student responses. Never publish full JSON, PDFs, or leader page images as public static assets.

Report the files actually created, validation performed, and any exact unresolved content. When requested, update the project's `readme.md` with the approved format, content paths, extraction command/skill, and remaining work. Do not claim website integration or visual verification that was not performed.
