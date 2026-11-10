---
name: bible-verse
description: Fetch published Bible passage text by reference for quotation or version comparison, including quoted Scripture needed by the PDF translation workflow.
---

# Bible verse lookup

Run from the repository root:

```bash
python3 .agents/skills/bible-verse/scripts/get_verse.py "<reference>" --versions 和合本
```

Use `--versions ESV,NIV` for an ordered comparison or `--json` for structured output. Without `--versions`, the default is 和合本 (CUNP), then ESV; specify versions when only one is requested. The script retrieves published text from bolls.life, not model memory.

## Reference and version choices

- Chinese/English names, abbreviations, and full-width punctuation are accepted.
- Examples: `John 3:16`, `Romans 8:1-4`, `John 3:16-4:2`, `Psalm 23` (whole chapter).
- A bare number means a chapter for multi-chapter books, but a verse for single-chapter books, e.g. `Jude 3`.
- `和合本`, `CUV`, `CUNP` select Traditional 新標點和合本; `思高本` selects 思高本. Use `CUNPS` only when Simplified Chinese is requested. English version codes such as ESV, NIV, KJV, NASB and NLT pass through to the provider.

## Verify and relay

Verify the returned book, chapter, version, and complete requested range. Relay the returned wording unchanged, with a citation and one numbered verse or merged range per line. Cross-chapter labels use `chapter:verse`. Preserve merged labels such as `34-35`; never split a merged verse block or invent text for a missing line.

Quotation marks can span verses. Preserve them as returned; when inserting quotations into a translation, do not add surrounding verses that the source did not quote. Citation-only references stay citations. The script strips source markup and annotations for plain-text output.

Correct an obvious malformed reference/version and rerun; retry a transient network failure once. If retrieval remains unavailable, report the error and never supply remembered or self-translated Scripture. Within the PDF workflow, follow its translation contract for the exact placeholder and failure report.
