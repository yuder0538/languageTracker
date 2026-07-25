from app.models.enums import DeArtikel, Language
from app.models.vocabulary import Vocabulary
from app.services.anki_export import build_anki_line


def test_en_line_includes_ipa_and_definition():
    vocab = Vocabulary(
        language=Language.EN,
        headword="run",
        ipa="/rʌn/",
        en_definition="to move fast",
        example_sentence="I love to run.",
    )

    line = build_anki_line(vocab)

    front, back = line.split("\t")
    assert front == "run [/rʌn/]"
    assert back == "to move fast<br>I love to run."


def test_en_line_falls_back_to_translation_zh_when_no_definition():
    vocab = Vocabulary(language=Language.EN, headword="run", translation_zh="跑")

    line = build_anki_line(vocab)

    _, back = line.split("\t")
    assert back == "跑"


def test_de_line_includes_artikel_prefix():
    vocab = Vocabulary(
        language=Language.DE,
        headword="Haus",
        de_artikel=DeArtikel.DAS,
        translation_zh="房子",
        example_sentence="Das ist mein Haus.",
    )

    line = build_anki_line(vocab)

    front, back = line.split("\t")
    assert front == "das Haus"
    assert back == "房子<br>Das ist mein Haus."


def test_de_line_without_artikel_omits_prefix():
    vocab = Vocabulary(language=Language.DE, headword="laufen", translation_zh="laufen")

    line = build_anki_line(vocab)

    front, _ = line.split("\t")
    assert front == "laufen"


def test_internal_newlines_are_escaped():
    vocab = Vocabulary(
        language=Language.EN,
        headword="run",
        en_definition="line one\nline two",
    )

    line = build_anki_line(vocab)

    assert line.count("\t") == 1  # only the Front/Back separator remains a real tab
    front, back = line.split("\t")
    assert back == "line one<br>line two"


def test_internal_tabs_are_replaced_with_spaces():
    vocab = Vocabulary(
        language=Language.EN,
        headword="run",
        en_definition="a\tb",
    )

    line = build_anki_line(vocab)

    assert line.count("\t") == 1  # only the Front/Back separator remains a real tab
    front, back = line.split("\t")
    assert back == "a b"


def test_bare_carriage_return_is_escaped():
    vocab = Vocabulary(
        language=Language.EN,
        headword="run",
        en_definition="line one\rline two",
    )

    line = build_anki_line(vocab)

    front, back = line.split("\t")
    assert back == "line one<br>line two"
    assert "\r" not in back
