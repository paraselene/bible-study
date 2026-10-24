from .i18n import labels, translate, translate_reference


def present_sections(data, lang):
    ui = labels(lang)
    fallback = False

    def text_block(value, kind="paragraph", **extra):
        nonlocal fallback
        text, missing = translate(value, lang)
        fallback |= missing
        return {"type": kind, "text": text, "text_lang": "en" if missing else lang, **extra}

    def blocks(value, scripture=False):
        if isinstance(value, list):
            return [block for child in value for block in blocks(child, scripture)]
        if "en" in value:
            return [text_block(value, "scripture" if scripture else "paragraph")]
        result = []
        if "title" in value:
            result.append(text_block(value["title"], "heading"))
        if "reference" in value:
            result.append({"type": "reference", "text": translate_reference(value["reference"], lang), "text_lang": lang})
        if "question" in value:
            result.append(text_block(value["question"], "question", id=value["id"]))
            if "answer" in value:
                result.append(text_block(value["answer"], "answer"))
            return result
        for key, child in value.items():
            if key in ("title", "reference", "id"):
                continue
            if key in ("commentary", "prayer", "supplies"):
                result.append({"type": "label", "text": ui[key], "text_lang": lang})
            result.extend(blocks(child, scripture))
        return result

    sections = [{"id": key, "title": ui[key], "blocks": blocks(value, key == "scripture")} for key, value in data.items() if key != "title"]
    return sections, fallback
