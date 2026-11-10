# Bible Study website and shared bilingual JSON

## Website

- Build a mobile-friendly Django website following `../voting`: Gunicorn, WhiteNoise, SQLite sessions, and Docker Compose.
- One password field: `leader` grants access to both guides; `disciple` grants access only to the disciple guide. No individual accounts.
- Provide a unit/session library and full scrolling lessons with section navigation.
- Enforce access on the server. Never send leader-only content to student browsers or expose source PDFs and complete JSON as public static files.
- Allow answers to study questions, saved automatically in the current browser. Key answers by lesson and stable question ID so language changes and shared questions preserve answers. Include save status and a confirmed clear-answers action.

## Content and JSON

Extract paired Leader and Daily Discipleship Guides into lesson JSON files. The library currently covers Units 20–26 and can grow as additional lessons are prepared. Prefer readable native PDF text; use OCR and visual verification when needed.

**Approved format:** the user approved [`lessons/u23_s1.json`](lessons/u23_s1.json), including commentary grouped under its printed teaching titles. Every lesson follows this format; see [`JSON_FORMAT.md`](JSON_FORMAT.md) and [`lesson.schema.json`](lesson.schema.json). This supersedes the original block dictionary and guide-reference design.

- Use the named lesson sections in the approved example. Store shared passages and questions once, with leader answers attached to their questions and additional teaching sections marked `leader_only`.
- Preserve lesson titles, subtitles, Scripture references and verse numbers, footnote indicators, questions, responses, and teaching material. Group commentary references under the correct teaching title.
- Omit printed page numbers, repeated unit/session headers, running footers, and extraction metadata from lesson JSON.
- Extract the lesson sections only and verify their page ranges in each source. U24 S5 uses pages 1–8 in both guides; U25 S1 uses LG pages 8–15 and DDG pages 6–13. Other lessons processed through U26 use pages 1–8.
- Enforce guide access on the server: remove leader-only sections and supplied answers from student responses. Apply the same authorization to instructional images.
- Validate with `.venv/bin/python scripts/validate_lessons.py`; check source-page selection and content completeness separately from runtime JSON.
- Preserve stable question IDs and existing translations when correcting or re-extracting text.
- Luna subagents extract and prepare the lesson JSON; visually verify reading order and uncertain text against the supplied PDFs rather than inventing wording.

## Languages

- Offer English, 繁體中文, 简体中文, and bilingual English/Chinese modes; default to Traditional Chinese and remember the selection. In bilingual modes, show English first.
- Deliver English lesson content with `zh-Hant` translation slots; preserve supplied Traditional Chinese translations. Translate interface labels.
- Missing Chinese lesson text displays English with a clear fallback notice.
- Generate Simplified Chinese at render time from Traditional Chinese using [OpenCC](https://github.com/BYVoid/OpenCC), without storing Simplified Chinese in the JSON.
- Later Chinese Scripture quotations use Traditional Chinese 和合本; preserve the supplied English quotations and store their Scripture references.
- Never convert user-entered answers when switching language.

## Docker and verification

- Production Compose uses `biblestudy-web`, persistent session data, and the existing `wordpress_wordpress_net` reverse-proxy network.
- Separate local Compose uses `127.0.0.1:18001`, avoiding the voting app’s port.
- Include environment examples, setup/update instructions, CSRF protection, session rotation on login, POST logout, and secure production cookies.
- Test both passwords, invalid login, logout, direct leader-route denial, and absence of leader content from student HTML and asset responses.
- Validate all available lessons, shared content, translation fallback, Simplified conversion, and browser answer persistence across reloads, language changes, and guide switches.
- Verify mobile layout, keyboard navigation, Docker startup, and persistence after restart.

## Scope and known limitations

- No individual accounts, answer synchronization, or content editor in this first version. Chinese lesson translation remains incomplete.
- Shared passwords are easily shared; anyone who knows `leader` can access leader material.
- Browser answers remain available to other users of the same browser and disappear if browser storage is cleared.
- This document records the agreed implementation plan, not completed implementation or verification.
