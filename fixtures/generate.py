"""Regenerate every committed fixture from its data table.

    uv run python -m fixtures.generate

Replaces `scripts/generate_sample_invoice.py` and `eval/golden/generate_golden_invoices.py`,
which were near-verbatim copies of each other and which each carried a plea to re-run them after
editing their data. That plea is gone: an expectation is now read out of the same table that
draws the page, so a stale `expected.json` is not a thing this repo can have — only a stale
image, which this command fixes.
"""

from fixtures import write_golden, write_sample
from fixtures.catalogue import EXAMPLES
from fixtures.surfaces import REPO_ROOT


def main() -> None:
    for example in EXAMPLES:
        if example.golden:
            directory = write_golden(example)
            print(f"wrote {directory.relative_to(REPO_ROOT)}/")
        if example.sample is not None:
            for path in write_sample(example):
                print(f"wrote {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
