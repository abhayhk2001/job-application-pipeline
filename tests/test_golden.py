"""Golden-file test: the fixture must render to exactly tests/golden/resume.tex.

The golden file is generated, never hand-edited. To refresh it after an
intentional template change::

    python -c "import json; from resume_builder import TEST_RESUME, GOLDEN_TEX; \
from resume_builder.renderer import render; \
GOLDEN_TEX.write_text(render(json.loads(TEST_RESUME.read_text())))"

Then read the diff before committing: that diff *is* the review.
"""

from __future__ import annotations

import difflib

from resume_builder import GOLDEN_TEX
from resume_builder.renderer import render


def test_render_matches_golden(fixture_resume):
    expected = GOLDEN_TEX.read_text()
    actual = render(fixture_resume)
    if actual != expected:
        diff = "\n".join(
            difflib.unified_diff(
                expected.splitlines(),
                actual.splitlines(),
                fromfile="tests/golden/resume.tex",
                tofile="render(fixture)",
                lineterm="",
            )
        )
        raise AssertionError(f"rendered TeX drifted from the golden file:\n{diff}")


def test_golden_is_not_stale(fixture_resume):
    """Guard against the golden file being committed empty or truncated."""
    body = GOLDEN_TEX.read_text()
    assert body.startswith("%-------------------------")
    assert body.rstrip().endswith("\\end{document}")
    assert len(body) > 5000
