"""
Image comparison harness, adapted from plotnine's own test suite

Tests compare a plot with a baseline image using ``assert p == "name"``.
Result images are written to ``tests/result_images/<test_module>/`` and
compared with ``tests/baseline_images/<test_module>/<name>.png``.

To create or update a baseline, run the test once and copy the result
image into the baseline directory (or run ``pytest --update-baselines``).
"""

from __future__ import annotations

import inspect
import shutil
import types
import warnings
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from matplotlib.testing.compare import compare_images
from plotnine import ggplot
from plotnine.options import set_option
from plotnine.themes.theme import DEFAULT_RCPARAMS

TOLERANCE = 2  # Same default tolerance as plotnine
DPI = 72

# Use fonts that ship with matplotlib for uniform images
DEFAULT_RCPARAMS["font.monospace"] = ["DejaVu Sans Mono"]
DEFAULT_RCPARAMS["font.sans-serif"] = ["DejaVu Sans"]
DEFAULT_RCPARAMS["font.serif"] = ["DejaVu Serif"]

# 640 x 480 pixels, the same size as ggtext's vdiffr snapshots and the
# R reference images in tests/reference_r/
set_option("dpi", DPI)
set_option("figure_size", (640 / DPI, 480 / DPI))

tests_dir = Path(__file__).parent
baseline_images_dir = tests_dir / "baseline_images"
result_images_dir = tests_dir / "result_images"

_UPDATE = False


def pytest_addoption(parser):
    parser.addoption(
        "--update-baselines",
        action="store_true",
        default=False,
        help="Write result images as the new baselines",
    )


def pytest_configure(config):
    global _UPDATE
    _UPDATE = config.getoption("--update-baselines")


def make_test_image_filenames(name: str, test_file: str):
    name_ = Path(name).with_suffix(".png")
    subdir = Path(test_file).stem
    filenames = types.SimpleNamespace(
        baseline=baseline_images_dir / subdir / name_,
        result=result_images_dir / subdir / name_,
        expected=result_images_dir / subdir / f"{name_.stem}-expected.png",
    )
    filenames.result.parent.mkdir(parents=True, exist_ok=True)
    return filenames


class _test_cleanup:
    def __enter__(self):
        plt.close("all")
        mpl.use("Agg")
        mpl.rcdefaults()
        mpl.rcParams["text.hinting"] = "auto"
        mpl.rcParams["text.antialiased"] = True
        return self

    def __exit__(self, *args):
        plt.close("all")
        warnings.resetwarnings()


def ggplot_equals(plot: ggplot, name: str) -> bool:
    test_file = inspect.stack()[1][1]
    filenames = make_test_image_filenames(name, test_file)
    with _test_cleanup():
        plot.save(filenames.result, verbose=False)

    if _UPDATE:
        filenames.baseline.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(filenames.result, filenames.baseline)

    if not filenames.baseline.exists():
        raise Exception(f"Baseline image {filenames.baseline} is missing")

    shutil.copyfile(filenames.baseline, filenames.expected)
    err = compare_images(
        str(filenames.expected), str(filenames.result), TOLERANCE, in_decorator=True
    )
    plot._err = err  # pyright: ignore[reportAttributeAccessIssue]
    return not err


ggplot.__eq__ = ggplot_equals  # pyright: ignore[reportAttributeAccessIssue]


def draw_test(self: ggplot):
    with _test_cleanup():
        self.draw()


ggplot.draw_test = draw_test  # pyright: ignore[reportAttributeAccessIssue]


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, ggplot) and isinstance(right, str) and op == "==":
        err = getattr(left, "_err", None)
        if err:
            return [
                "images not close: {actual:s} vs. {expected:s} "
                "(RMS {rms:.2f})".format(**err)
            ]


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")
