from .i18n import display_text, labels, translate_reference


def present_sections(data, lang):
    ui = labels(lang)
    fallback = False

    def text_block(value, kind="paragraph", **extra):
        nonlocal fallback
        text = display_text(value, lang)
        fallback |= text["fallback"]
        return {"type": kind, **text, **extra}

    def blocks(value, scripture=False):
        if isinstance(value, list):
            return [block for child in value for block in blocks(child, scripture)]
        if "en" in value:
            return [text_block(value, "scripture" if scripture else "paragraph")]
        result = []
        if "title" in value:
            result.append(text_block(value["title"], "heading"))
        if "reference" in value:
            result.append(text_block({"en": value["reference"], "zh-Hant": translate_reference(value["reference"], "zh-Hant")}, "reference"))
        if "question" in value:
            result.append(text_block(value["question"], "question", id=value["id"]))
            if "answer" in value:
                result.append(text_block(value["answer"], "answer"))
            return result
        for key, child in value.items():
            if key in ("title", "reference", "id"):
                continue
            if key in ("commentary", "prayer", "supplies"):
                result.append({"type": "label", "text": ui[key], "text_lang": "en" if lang.startswith("en-") else lang})
            result.extend(blocks(child, scripture))
        return result

    sections = [{"id": key, "title": ui[key], "blocks": blocks(value, key == "scripture")} for key, value in data.items() if key != "title"]
    return sections, fallback
