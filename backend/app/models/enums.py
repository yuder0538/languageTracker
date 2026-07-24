import enum


class Language(str, enum.Enum):
    EN = "en"
    DE = "de"


class DeArtikel(str, enum.Enum):
    DER = "der"
    DIE = "die"
    DAS = "das"


class ReviewGrade(str, enum.Enum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"
