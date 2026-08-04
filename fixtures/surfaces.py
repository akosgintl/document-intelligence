"""Where an Example's two projections are written.

Two surfaces, one source (#46, convention 1):

- **Golden** — `eval/golden/<key>/{submission.png,expected.json}`, the accuracy set
  `eval/run_eval.py` runs against a real Model Provider.
- **Sample** — `scripts/samples/<sample>.{png,pdf}`, the files `scripts/manual_test.py` posts at
  a running API. The PDF exists because that script defaults to one, and because a PDF
  exercises the rendering path a PNG skips.
"""

from pathlib import Path

from fixtures.expectations import write_expectation
from fixtures.model import Example
from fixtures.render import render_pdf_bytes, render_png_bytes

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_ROOT = REPO_ROOT / "eval" / "golden"
SAMPLE_ROOT = REPO_ROOT / "scripts" / "samples"


def write_golden(example: Example, root: Path = GOLDEN_ROOT) -> Path:
    """Write the Example's page and expectation as one golden example directory."""
    directory = root / example.key
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "submission.png").write_bytes(render_png_bytes(example))
    write_expectation(example, directory / "expected.json")
    return directory


def write_sample(example: Example, root: Path = SAMPLE_ROOT) -> list[Path]:
    """Write the Example's page as a manual-testing sample, in both accepted formats."""
    if example.sample is None:
        raise ValueError(f"{example.key} declares no sample name")
    root.mkdir(parents=True, exist_ok=True)
    png = root / f"{example.sample}.png"
    pdf = root / f"{example.sample}.pdf"
    png.write_bytes(render_png_bytes(example))
    pdf.write_bytes(render_pdf_bytes(example))
    return [png, pdf]
