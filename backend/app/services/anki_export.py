from app.models.enums import Language
from app.models.vocabulary import Vocabulary


def _clean_field(value: str) -> str:
    return (
        value.replace("\t", " ")
        .replace("\r\n", "<br>")
        .replace("\r", "<br>")
        .replace("\n", "<br>")
    )


def build_anki_line(vocabulary: Vocabulary) -> str:
    if vocabulary.language == Language.EN:
        front = vocabulary.headword
        if vocabulary.ipa:
            front = f"{front} [{vocabulary.ipa}]"

        back_parts = []
        definition = vocabulary.en_definition or vocabulary.translation_zh
        if definition:
            back_parts.append(definition)
    else:
        front = (
            f"{vocabulary.de_artikel.value} {vocabulary.headword}"
            if vocabulary.de_artikel
            else vocabulary.headword
        )

        back_parts = []
        if vocabulary.translation_zh:
            back_parts.append(vocabulary.translation_zh)

    if vocabulary.example_sentence:
        back_parts.append(vocabulary.example_sentence)

    front = _clean_field(front)
    back = _clean_field("<br>".join(back_parts))

    return f"{front}\t{back}"
