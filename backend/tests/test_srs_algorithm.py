import pytest

from app.models.enums import ReviewGrade
from app.services.srs import MIN_EASE_FACTOR, SrsState, schedule_next_review


def _new_state() -> SrsState:
    return SrsState(interval_days=0, ease_factor=2.5, repetitions=0, lapses=0)


def test_again_resets_interval_and_increments_lapses():
    state = SrsState(interval_days=10, ease_factor=2.5, repetitions=3, lapses=1)

    result = schedule_next_review(state, ReviewGrade.AGAIN)

    assert result.interval_days == 1
    assert result.repetitions == 0
    assert result.lapses == 2


def test_first_good_review_sets_interval_to_one_day():
    result = schedule_next_review(_new_state(), ReviewGrade.GOOD)

    assert result.interval_days == 1
    assert result.repetitions == 1
    assert result.lapses == 0


def test_second_good_review_sets_interval_to_six_days():
    state = SrsState(interval_days=1, ease_factor=2.5, repetitions=1, lapses=0)

    result = schedule_next_review(state, ReviewGrade.GOOD)

    assert result.interval_days == 6
    assert result.repetitions == 2


def test_third_good_review_multiplies_interval_by_ease_factor():
    state = SrsState(interval_days=6, ease_factor=2.5, repetitions=2, lapses=0)

    result = schedule_next_review(state, ReviewGrade.GOOD)

    assert result.interval_days == 15  # round(6 * 2.5)
    assert result.repetitions == 3
    assert result.ease_factor == 2.5


def test_easy_grows_interval_faster_than_good():
    state = SrsState(interval_days=6, ease_factor=2.5, repetitions=2, lapses=0)

    result = schedule_next_review(state, ReviewGrade.EASY)

    assert result.interval_days > 15
    assert result.ease_factor > 2.5


def test_hard_grows_interval_slower_than_good():
    state = SrsState(interval_days=6, ease_factor=2.5, repetitions=2, lapses=0)

    result = schedule_next_review(state, ReviewGrade.HARD)

    assert result.interval_days < 15
    assert result.ease_factor < 2.5


def test_ease_factor_never_drops_below_minimum():
    state = SrsState(interval_days=1, ease_factor=1.35, repetitions=1, lapses=0)

    result = schedule_next_review(state, ReviewGrade.AGAIN)

    assert result.ease_factor == pytest.approx(MIN_EASE_FACTOR)

    result_hard = schedule_next_review(state, ReviewGrade.HARD)
    assert result_hard.ease_factor >= MIN_EASE_FACTOR


def test_ease_factor_already_at_minimum_stays_clamped():
    state = SrsState(
        interval_days=1, ease_factor=MIN_EASE_FACTOR, repetitions=1, lapses=0
    )

    result_again = schedule_next_review(state, ReviewGrade.AGAIN)
    result_hard = schedule_next_review(state, ReviewGrade.HARD)

    assert result_again.ease_factor == pytest.approx(MIN_EASE_FACTOR)
    assert result_hard.ease_factor == pytest.approx(MIN_EASE_FACTOR)


def test_ease_factor_well_above_minimum_is_not_clamped():
    state = SrsState(interval_days=6, ease_factor=2.5, repetitions=2, lapses=0)

    result = schedule_next_review(state, ReviewGrade.AGAIN)

    assert result.ease_factor == pytest.approx(2.3)
