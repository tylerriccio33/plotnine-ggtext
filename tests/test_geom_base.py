import numpy as np
import pytest
from plotnine.exceptions import PlotnineError

from plotnine_ggtext._geom_base import compute_just


# --- compute_just ------------------------------------------------------------


def test_compute_just_numbers():
    out = compute_just(0.3, np.array([0.1, 0.9]))
    assert out == pytest.approx([0.3, 0.3])
    out = compute_just([0.0, 1.0], np.array([0.5, 0.5]))
    assert out == pytest.approx([0.0, 1.0])


@pytest.mark.parametrize(
    "name, val",
    [("left", 0), ("center", 0.5), ("centre", 0.5), ("right", 1),
     ("bottom", 0), ("middle", 0.5), ("top", 1)],
)
def test_compute_just_named(name, val):
    assert compute_just(name, np.array([0.2]))[0] == val


def test_compute_just_inward():
    out = compute_just("inward", np.array([0.1, 0.5, 0.9]))
    assert out == pytest.approx([0, 0.5, 1])


def test_compute_just_outward():
    out = compute_just("outward", np.array([0.1, 0.5, 0.9]))
    assert out == pytest.approx([1, 0.5, 0])


def test_compute_just_inward_tolerance():
    out = compute_just("inward", np.array([0.5004]))
    assert out[0] == 0.5


def test_compute_just_unknown_raises():
    with pytest.raises(PlotnineError):
        compute_just("sideways", np.array([0.5]))
