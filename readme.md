# BibleStudy

## Current state

Updated 2026-10-24. The goal is a mobile-friendly Django website for reading the supplied Bible-study curriculum, with shared leader/student access and browser-local written responses.

The website reads **25 canonical lesson JSONs from `lessons/`**, covering Units 20–25. Units 20, 21, 22, 23, and 25 have four sessions each; Unit 24 has five. Files are named `u20_s1.json`, `u21_s2.json`, etc. The library discovers them automatically. They are private server data, not public static assets.

The local Docker website is available at **http://localhost:18001** when the local Compose service is running.

- Password `student`: shared lesson content and questions.
- Password `leader`: both guides, including teaching notes and supplied reference answers.
- English, 繁體中文, and 简体中文 interface labels; Traditional Chinese is the default and the selection is remembered.
- Lesson text is currently English. Missing Chinese text displays English with a fallback notice. Simplified Chinese is generated from Traditional Chinese with OpenCC.
- Written responses save in the current browser, keyed by lesson and stable question ID. Language and guide changes preserve them. Clearing a lesson's responses requires confirmation.
- Responses are not sent to the server or synchronized. They remain after logout and can be read by other people using the same browser. Clearing browser storage deletes them.

No remote deployment has been performed.

## Decisions to preserve in future sessions

The user approved [`lessons/u23_s1.json`](lessons/u23_s1.json) as the format reference. Its content was preserved unchanged when moved into `lessons/`. See [`JSON_FORMAT.md`](JSON_FORMAT.md) and [`lesson.schema.json`](lesson.schema.json).

Use its simple named sections: title, main point, Christ connection, Scripture, Before You Teach, context, theology connection, kickoff/activity/cultural material, discussion, wrap-up, and devotions. Keep text bilingual as `en` and `zh-Hant`, with `zh-Hant: null` until translated.

**Commentary title grouping is important.** Each commentary group contains its teaching title and an ordered list of reference/content entries. Different quotations with the same Scripture reference remain separate entries. Keep supplied Bible chapter/verse numbers, quotations, questions, answers, and footnote indicators. Omit folios, repeated unit/session headers, running footers, OCR coordinates/confidence, block dictionaries, and guide-reference maps.

Store shared LG/DDG material once. Keep supplied leader responses in `answer` and additional private teaching sections marked `leader_only`. Student responses are filtered on the server before template rendering; hiding content with CSS or JavaScript is insufficient.

Preserve question IDs and existing translations when correcting text. The supplied PDFs remain the authority for transcription corrections; do not invent replacement questions or reference answers.

## Extraction skill

The skill is **repo-only** at [`.agents/skills/bible-study-pdf-to-json/SKILL.md`](.agents/skills/bible-study-pdf-to-json/SKILL.md). There is no global copy. Invoke it as `$bible-study-pdf-to-json` when extracting more lessons or correcting an extraction.

The workflow uses Luna subagents to extract and prepare JSON, followed by source and structure checks. The skill includes the approved example, schema, and a fallback validator. The user explicitly declined skill evaluation; do not run skill evaluations unless requested.

The current local source set is 50 paired LG/DDG PDFs in `source/`. Raw PDFs and rendered review images are ignored by Git and excluded from the production Docker image; a production clone needs the checked JSONs, not these working files. Units 20–21 have extractable PDF text; Units 22–25 require OCR and visual review. Extract the eight-page session sections only:

| Source | Selected PDF pages |
| --- | --- |
| U25 S1 LG | 8–15 |
| U25 S1 DDG | 6–13 |
| U24 S5 LG and DDG | 1–8; ignore the extra end matter |
| All other supplied PDFs | 1–8 |

Extraction drafts and review artifacts are under ignored `tmp/`; superseded block-dictionary JSONs are in `tmp/legacy-extraction/`. They are not website input. Rendered source-page images in `lessons/assets/` are review artifacts, not routed or included in the Docker image. Neither the source PDFs nor full lesson JSONs are publicly downloadable through the app.

`scripts/extract_lessons.py` is a legacy OCR staging helper, not a canonical lesson converter. Prepare final files through the repo-local skill and approved schema.

## Start locally with Docker

```sh
rtk proxy docker compose -f compose.local.yaml up -d --build
rtk proxy docker compose -f compose.local.yaml ps
```

Open http://localhost:18001. The service is `biblestudy-web`, bound to `127.0.0.1:18001`. Local sessions persist in `data/local-docker/db.sqlite3`. This setup does not use production `.env` or the reverse-proxy network. The Docker build validates the lesson JSONs before creating a new image.

To stop it:

```sh
rtk proxy docker compose -f compose.local.yaml stop
```

## Python development and checks

For a new Python environment:

```sh
rtk proxy uv --cache-dir /private/tmp/biblestudy-uv-cache venv .venv
rtk proxy uv --cache-dir /private/tmp/biblestudy-uv-cache pip install --python .venv/bin/python -r requirements-dev.txt
rtk proxy mkdir -p data
```

Run checks:

```sh
rtk proxy .venv/bin/python scripts/validate_lessons.py
rtk proxy .venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
rtk proxy env BUILD_STATIC=1 .venv/bin/python manage.py collectstatic --noinput
rtk proxy env DEBUG=1 .venv/bin/python manage.py check
rtk proxy env DEBUG=1 .venv/bin/python manage.py makemigrations --check --dry-run
rtk proxy env DEBUG=1 .venv/bin/python manage.py test
rtk proxy node scripts/test_answers.cjs
```

`collectstatic` must precede local Django tests because tests use the production manifest-backed static storage. Docker builds perform this automatically.

To run without Docker, first stop the local container to free port 18001, then:

```sh
rtk proxy env DEBUG=1 .venv/bin/python manage.py migrate --noinput
rtk proxy env DEBUG=1 .venv/bin/python manage.py runserver 127.0.0.1:18001
```

For HTTP checks against the running local Docker app:

```sh
rtk proxy .venv/bin/python scripts/smoke_local.py
```

That smoke check deliberately restarts the local container to verify that both authenticated sessions survive. It does not touch production.

## Production setup, when deployment is requested

Copy `.env.example` to `.env`, set a random `SECRET_KEY` of at least 40 characters, and set the real `ALLOWED_HOSTS` and HTTPS `PUBLIC_URL`. Production rejects missing/invalid settings and forces HTTPS with secure cookies. Keep `.env` private and out of version control.

`compose.yaml` uses service `biblestudy-web`, persistent `data/production/`, and the existing external network `wordpress_wordpress_net`. It publishes no host port. The reverse proxy must terminate HTTPS, reach the container on port 8000, and overwrite `X-Forwarded-Proto` with the actual request scheme. Do not expose the container directly through an untrusted proxy path.

Use `docker compose up -d --build` or `./update.sh` only for an authorized deployment. These commands build/validate content, migrate sessions, and run Gunicorn with WhiteNoise. They do not pull or publish Git changes.

## Implementation map

- `study/content.py`: file discovery/loading and recursive guide projection.
- `study/presentation.py`: presents the approved named JSON sections.
- `study/views.py`: shared-password login, session rotation, POST logout, and guide access checks.
- `study/i18n.py`: interface labels, fallback, and OpenCC conversion.
- `study/templates/study/`, `study/static/study/`: interface and browser-local responses.
- `config/settings.py`: SQLite sessions, cookies, HTTPS/proxy settings, and WhiteNoise.
- `scripts/validate_lessons.py`, `lesson.schema.json`: approved JSON format checks.
- `scripts/test_answers.cjs`: isolated storage behavior checks without a browser.
- `scripts/smoke_local.py`: real HTTP and local Docker restart checks.

The current lesson JSON contains text rather than instructional image fields; the app does not expose source-page images. Any future need to add image/table structures should be agreed against the approved format before changing it.

## Verification and remaining limits

Completed: all 25 lessons pass schema/content-structure checks; source commentary reference grouping was checked; the approved U23 S1 example stayed unchanged. Fifteen Django tests cover permissions across every student lesson, both passwords, session rotation, CSRF, POST logout, fallback/conversion, escaped content, and private file paths. Validator tests and standalone answer-storage checks pass. Local Docker build/startup, WhiteNoise, HTTP access controls, secure production settings, and session persistence after a restart passed.

**Real browser/mobile layout and keyboard QA remain unverified.** Browser preview was denied by browser security policy, and no alternate browser automation was attempted. The JavaScript checks cover storage logic in isolation, not a real browser. No Chinese lesson translation, account management, response synchronization, content editor, or remote deployment was included.

Shared passwords are intentionally simple and shareable; anyone who knows `leader` can read leader material. JSON validation verifies structure and consistency, not the correctness of every OCR word. Use the original PDFs for any future text corrections.
