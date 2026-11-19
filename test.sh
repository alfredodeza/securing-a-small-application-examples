#!/bin/sh
# Runs the whole review in a copy of this repository: every finding open, then each fix in
# order closing its own, and the report at the end.
exec uv run --frozen python -m unittest discover -s tests -v
