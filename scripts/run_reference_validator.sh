#!/usr/bin/env bash
# Wrapper for linkml-reference-validator (the quote checker).
#
# Behavior:
# - ERROR results (a quote that isn't in the publication, a wrong title) fail.
# - Warning-only results pass: a reference that couldn't be fetched because of
#   a flaky network should not block validation. Real mismatches are errors.
# - A crash (traceback) always fails — a run that didn't finish proves nothing.
#
# Usage: scripts/run_reference_validator.sh [args...]
#   e.g.: scripts/run_reference_validator.sh validate data file.yaml \
#           --schema src/soma/schema/soma.yaml --target-class Container \
#           --config conf/reference_validator_config.yaml

set -euo pipefail

set +e
output="$(uv run linkml-reference-validator "$@" 2>&1)"
exit_code=$?
set -e

printf '%s\n' "$output"

# The validator can exit 0 even when it found errors, so the exit code alone
# cannot be trusted — read the output. Any [ERROR] line or crash fails.
#
# With ALLOW_ABSTRACT_ONLY_MISSES=1 (set by validate-file/validate-all), a
# "Text part not found" error against a paper whose cache entry is
# abstract-only does NOT fail this wrapper: the validator marks those errors
# with "(note: only abstract available for PMID:...)", and responsibility for
# them moves to the verification receipts (scripts/snippet_receipts.py check,
# run right after this in the same recipe / via qc). Every other error still
# fails here.
decisive="$output"
if [ "${ALLOW_ABSTRACT_ONLY_MISSES:-}" = "1" ]; then
    decisive="$(grep -v 'only abstract available for PMID:' <<<"$output" || true)"
fi
if grep -Eq '\[ERROR\]|Traceback|^Error:' <<<"$decisive"; then
    echo "Reference validation failed: errors found (see above)." >&2
    exit 1
fi

# Warnings alone (e.g. a reference that couldn't be fetched) never fail.
exit 0
