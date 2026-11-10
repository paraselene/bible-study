---
name: translate-lesson-json
description: Translate selected existing BibleStudy lesson JSON files into Traditional Chinese and independently review every English/Chinese pair, including existing translations. Use for lesson translation and translation corrections, not PDF extraction.
---

# Two-stage lesson translation

Run from the repository root. Process only the files or batch requested; ask for lesson selection if unspecified. Creating or updating this skill does not authorize translating production lessons, committing, or deploying. Use the existing project environment; add no dependencies or translation service.

## Prepare

Read each full lesson, `JSON_FORMAT.md`, `lesson.schema.json`, and the approved `lessons/u23_s1.json` example. Keep an untouched original snapshot and a working copy in a temporary directory, with a mapping back to each requested path. Inventory every bilingual field by JSON path, using `walk` from `scripts/validate_lessons.py` if helpful.

Change only existing `zh-Hant` values. Preserve English, references, IDs, object keys and order, array lengths and order, and leader-only flags. A missing language key is a format issue: report it instead of silently changing structure. Null or blank Chinese values are missing translations. Keep citations, retrieval evidence, coverage records, and review notes outside lesson JSON. Do not change the schema or application.

## Stage 1: Translate

Fill missing `zh-Hant` values with faithful, natural Traditional Chinese, preserving meaning, paragraph structure, and terminology across the lesson. Leave existing translations unchanged for Stage 2. Do not add explanations or Markdown decoration absent from the source.

For **every Bible quotation**, use the [bible-verse skill](../bible-verse/SKILL.md) to retrieve published Traditional Chinese 和合本 text. Read that skill and run its lookup from the repository root, for example:

```sh
rtk proxy .venv/bin/python .agents/skills/bible-verse/scripts/get_verse.py "John 11:35" --versions 和合本 --json
```

This applies to standalone passages and Scripture quoted within titles, commentary, answers, devotions, or any other field, including existing translations that need review. Never translate verses yourself or supply them from memory. Verify the returned version, reference, and complete range. Retain the quoted range, verse numbering, and verse line breaks; for inline excerpts, use only the corresponding retrieved words, without expanding to unquoted surrounding verses. Keep citation-only references as citations. Do not silently turn a paraphrase into a direct quotation.

Record the field path, reference, source/version, and retrieved text in temporary evidence files for the reviewer. If the reference or excerpt cannot be identified reliably, or retrieval fails after the bible-verse skill retry policy, leave that field unchanged and mark it unresolved outside the JSON. Do not insert invented Scripture or error messages into lesson text.

## Stage 2: Independent review

Use a separate reviewer agent; the translator cannot self-certify this stage. Give the reviewer the full original and candidate files, project format rules, this skill, and retrieved Scripture evidence. Ask it to compare **every** English/Chinese pair, including existing translations, and record coverage by JSON path. Do not restrict review to changed fields or tell it which seeded errors to expect.

The reviewer corrects omissions, mistranslations, unnatural phrasing, inconsistent terminology, and Simplified Chinese characters in the temporary candidate, changing only `zh-Hant` values. Check meaning in context rather than trusting character conversion alone. Verify every Bible quotation against published text retrieved through the bible-verse skill; retrieve missing evidence with that skill. Preserve the exact quoted scope and verse layout. Return corrections, coverage, and unresolved field paths separately from lesson JSON.

If a separate agent is unavailable or stops short of full coverage, retain the temporary files, report the incomplete review, and do not save them over the originals or claim a complete review. Apply all supported corrections before saving. For an unresolved field, retain its original value and explicitly report the limitation; never describe that field as verified.

## Verify and save

1. Compare original and reviewed JSON recursively: require identical types, object keys in identical order, array lengths and order, and scalar values everywhere except values at existing `zh-Hant` keys. Permit only string or null at those keys. Assert these invariants; removing Chinese keys and comparing unordered dictionaries alone misses object-order changes.
2. Reconcile review coverage with the original bilingual-field inventory. Account for every field as reviewed or explicitly unresolved; check missing translations and every quotation against the evidence. Structural checks cannot independently prove translation quality.
3. Run the existing validator on the temporary candidates:

   ```sh
   rtk proxy .venv/bin/python scripts/validate_lessons.py /absolute/path/to/temporary/lesson.json
   ```

4. Resolve structural or preservation failures before saving. Verify the destination still matches the original snapshot so concurrent edits are not overwritten. Save the reviewed candidates back to their original requested paths, retaining original values for unresolved fields. Re-run the validator and preservation comparison on saved files.
5. Report files saved, translations filled, existing translations corrected, review coverage, validation results, and exact unresolved paths/reasons. Do not commit or deploy unless separately requested.

## Exercise this skill after changes

Use a schema-valid synthetic lesson in a temporary directory, containing missing translations, deliberately wrong existing translations, Simplified Chinese, a numbered multiline Bible passage, and embedded Scripture quotations. Run Stage 1 and a separate Stage 2 reviewer, then the existing lesson validator and preservation assertions. Confirm the reviewer actually corrected the seeded errors and that only Chinese values changed. Keep test artifacts out of production lessons; report any retrieval or review limitations honestly.
