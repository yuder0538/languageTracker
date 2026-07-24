from dataclasses import dataclass

from app.models.enums import ReviewGrade

MIN_EASE_FACTOR = 1.3

_EASE_DELTA = {
    ReviewGrade.HARD: -0.15,
    ReviewGrade.GOOD: 0.0,
    ReviewGrade.EASY: 0.15,
}


@dataclass
class SrsState:
    interval_days: int
    ease_factor: float
    repetitions: int
    lapses: int


def schedule_next_review(state: SrsState, grade: ReviewGrade) -> SrsState:
    if grade == ReviewGrade.AGAIN:
        return SrsState(
            interval_days=1,
            ease_factor=max(MIN_EASE_FACTOR, state.ease_factor - 0.2),
            repetitions=0,
            lapses=state.lapses + 1,
        )

    new_ease_factor = max(MIN_EASE_FACTOR, state.ease_factor + _EASE_DELTA[grade])
    repetitions = state.repetitions + 1

    if repetitions == 1:
        new_interval = 1
    elif repetitions == 2:
        new_interval = 6
    else:
        new_interval = round(state.interval_days * new_ease_factor)
        if grade == ReviewGrade.HARD:
            new_interval = max(state.interval_days + 1, round(new_interval * 0.8))
        elif grade == ReviewGrade.EASY:
            new_interval = round(new_interval * 1.3)

    return SrsState(
        interval_days=max(1, new_interval),
        ease_factor=new_ease_factor,
        repetitions=repetitions,
        lapses=state.lapses,
    )
