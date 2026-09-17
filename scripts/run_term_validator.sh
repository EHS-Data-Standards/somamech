#!/usr/bin/env bash
# Wrapper for linkml-term-validator that fails on warnings.
#
# The validator can emit WARNING results (e.g. a label that doesn't match the
# ontology) without a failing exit code in some versions. For our checks a
# warning about a wrong label IS a failure, so this wrapper reads the output
# and fails if any warning appears or the success line is missing.
# (Pattern borrowed from dismech's scripts/run_term_validator.sh.)

set -euo pipefail

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <linkml-term-validator subcommand> [args...]" >&2
    exit 2
fi

subcommand=$1
shift

if [[ "$subcommand" != "validate-data" ]]; then
    exec uv run linkml-term-validator "$subcommand" "$@"
fi

set +e
output="$(uv run linkml-term-validator validate-data "$@" 2>&1)"
exit_code=$?
set -e

printf '%s\n' "$output"

if [[ $exit_code -ne 0 ]]; then
    exit "$exit_code"
fi

if grep -Eq '(^|[^[:alnum:]_])(WARN|WARNING)([^[:alnum:]_]|$)' <<<"$output"; then
    echo "Strict term validation failed: validator emitted warnings." >&2
    exit 1
fi

# Accept single-file ("Validation passed") or multi-file ("N files passed validation") success
if ! grep -qE "(Validation passed|[0-9]+ files? passed)" <<<"$output"; then
    echo "Strict term validation failed: validator did not report success." >&2
    exit 1
fi
