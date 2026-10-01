#!/usr/bin/env python3
"""Run one query against the built DuckDB knowledge base, or list its relations.

A script rather than an inline `python -c` in the justfile: SQL is full of both
kinds of quote, and passing it through a shell into a Python string literal
mangles anything containing `'%...%'`. Here the SQL arrives as argv and is
handed to DuckDB untouched.

Usage:
    uv run python scripts/soma_query.py exports/soma.duckdb
    uv run python scripts/soma_query.py exports/soma.duckdb "SELECT * FROM paper"
"""
from __future__ import annotations

import sys

LIST_RELATIONS = """
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'main'
ORDER BY table_type, table_name
"""


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    import duckdb

    db = argv[0]
    sql = argv[1] if len(argv) > 1 and argv[1].strip() else LIST_RELATIONS
    con = duckdb.connect(db, read_only=True)
    try:
        con.sql(sql).show(max_rows=200)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
