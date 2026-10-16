"""Reproduce the controlled retail environment, analysis and local dashboard."""

import argparse

from analyze import analyze
from build_dashboard import build
from evaluate import evaluate
from generate import generate
from discount_solution import replay
from visuals import render


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-generate", action="store_true", help="Reuse checksummed generated CSVs")
    args = parser.parse_args()
    if not args.skip_generate:
        generate()
    analyze()
    replay()
    evaluate()
    render()
    build()

