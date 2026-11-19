import math

import pytest

from plotnine_ggtext._units import LINE_PT, as_margin_pt, as_pt, as_pt_scalar, unit


@pytest.mark.parametrize(
    "value, units, expected",
    [
        (10, "pt", 10.0),
        (1, "in", 72.0),
        (2.54, "cm", 72.0),
        (25.4, "mm", 72.0),
        (96, "px", 72.0),
        (1, "lines", 14.4),
        (2, "lines", 28.8),
    ],
)
def test_to_pt(value, units, expected):
    assert unit(value, units).to_pt() == pytest.approx([expected])


def test_default_unit_is_pt():
    assert unit(5).to_pt() == [5.0]


def test_line_pt_constant():
    assert LINE_PT == pytest.approx(14.4)


def test_vector_values():
    assert unit([1, 2, 3], "in").to_pt() == pytest.approx([72, 144, 216])


def test_npc_requires_reference():
    with pytest.raises(ValueError):
        unit(0.5, "npc").to_pt()


def test_npc_with_reference():
    assert unit(0.5, "npc").to_pt(200) == pytest.approx([100])


def test_invalid_unit_raises():
    with pytest.raises(ValueError):
        unit(1, "furlongs")


def test_as_pt_variants():
    assert as_pt(None) is None
    assert as_pt(3) == [3.0]
    assert as_pt([1, 2]) == [1.0, 2.0]
    assert as_pt(unit(1, "in")) == [72.0]
    assert as_pt_scalar(None) is None
    assert as_pt_scalar(unit([1, 2], "in")) == 72.0


def test_as_margin_pt_single_recycled():
    assert as_margin_pt(5) == (5, 5, 5, 5)


def test_as_margin_pt_two_recycled():
    assert as_margin_pt([1, 2]) == (1, 2, 1, 2)


def test_as_margin_pt_three_recycled():
    assert as_margin_pt([1, 2, 3]) == (1, 2, 3, 1)


def test_as_margin_pt_four():
    assert as_margin_pt([1, 2, 3, 4]) == (1, 2, 3, 4)


def test_as_margin_pt_truncates():
    assert as_margin_pt([1, 2, 3, 4, 5]) == (1, 2, 3, 4)


def test_as_margin_pt_unit_conversion():
    m = as_margin_pt(unit(1, "in"))
    assert all(math.isclose(v, 72.0) for v in m)
    assert as_margin_pt(unit([1, 2], "in")) == (72, 144, 72, 144)
