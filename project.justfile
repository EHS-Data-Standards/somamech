## Add your own just recipes here. This is imported by the main justfile.

# ============ Paper-extraction pipeline paths ============

# Where validated, per-paper extraction files live (one Container YAML per paper)
kb_pubs_dir := "kb/publications"
# The paper queue: one small YAML per paper still waiting to be extracted
stubs_dir := "stubs"
# Committed cache of cited publications (abstracts + open-access full text,
# written only by fetch-reference — never by hand)
refs_cache := "references_cache"
# Local-only cache of full text extracted from PDFs on this machine
# (gitignored; lets the quote check cover paywalled papers locally)
refs_cache_local := "references_cache_local"
# Schema files inside the installed soma-schema package (see justfile)
soma_schema := source_schema_path
stub_schema := source_schema_dir / "publication_stub.yaml"
oak_conf := "conf/oak_config.yaml"
ref_conf := "conf/reference_validator_config.yaml"
term_validator_wrapper := "scripts/run_term_validator.sh"
ref_validator_wrapper := "scripts/run_reference_validator.sh"

# ============ Reference cache ============

# Fetch a publication's record (abstract + metadata, open-access full text
# when available) into references_cache/. Never write cache files by hand —
# a cache the extractor can edit can't catch anything.
[group('references')]
fetch-reference +identifiers:
    #!/usr/bin/env bash
    set -euo pipefail
    for identifier in {{identifiers}}; do
        echo "Fetching reference: $identifier"
        {{ref_validator_wrapper}} cache reference "$identifier" --cache-dir {{refs_cache}}
    done

# Extract the text of a local PDF into the local-only cache so quotes from a
# paywalled paper can be verified on this machine. Usage:
#   just extract-paper-text path/to/paper.pdf PMID:12345678
[group('references')]
extract-paper-text pdf pmid:
    uv run python scripts/extract_paper_text.py "{{pdf}}" "{{pmid}}" --out-dir {{refs_cache_local}}

# Report whether each paper's FULL TEXT can be fetched into the committed
# reference cache, or only its abstract can. Fetches anything not yet cached,
# then reads the cache entry's content_type. Usage:
#   just check-fulltext PMID:12345678 PMID:23456789
#
# This is the triage step /claim-paper runs BEFORE claiming a paper. Full-text
# papers are extracted first, because every quote in one can be verified by CI
# against the committed cache. An abstract-only paper is still extractable
# (local PDF + verification receipt) but goes to the back of the queue.
#
# Do not trust the stub's `open_access:` flag for this — it only means the
# paper has a PubMed Central record, and a PMC record often yields no
# retrievable full text (every stub in the queue today says true; two of the
# four papers extracted so far came back abstract-only).
#
# Report which papers are fully downloadable; always exits 0 (a report, not a gate).
[group('curation')]
check-fulltext +identifiers:
    #!/usr/bin/env bash
    set -uo pipefail
    for identifier in {{identifiers}}; do
        file="{{refs_cache}}/$(printf '%s' "$identifier" | tr ':/?=' '____').md"
        ctype=""
        if [ -f "$file" ]; then
            ctype=$(awk -F': *' '/^content_type:/{print $2; exit}' "$file")
            attempted=$(awk -F': *' '/^full_text_attempted:/{print $2; exit}' "$file")
            # Re-fetch a non-full-text entry that never cleanly tried for full
            # text: the fetcher re-runs the provider chain in exactly that case,
            # so a one-off provider outage does not cache as permanent absence.
            case "$ctype" in
                full_text_*) ;;
                *) [ "${attempted:-}" = "true" ] || rm -f "$file" ;;
            esac
        fi
        if [ ! -f "$file" ]; then
            {{ref_validator_wrapper}} cache reference "$identifier" --cache-dir {{refs_cache}} >/dev/null 2>&1 || true
            ctype=$(awk -F': *' '/^content_type:/{print $2; exit}' "$file" 2>/dev/null || true)
        fi
        if [ ! -f "$file" ]; then
            printf '  %-20s UNFETCHED      (fetch failed — retry before judging this paper)\n' "$identifier"
        else
            case "$ctype" in
                full_text_*) printf '  %-20s FULL TEXT      (%s)\n' "$identifier" "$ctype" ;;
                *)           printf '  %-20s ABSTRACT ONLY  (%s)\n' "$identifier" "${ctype:-unknown}" ;;
            esac
        fi
    done

# ============ Validation ============

# Validate one kb file: schema, then ontology terms, then evidence quotes.
[group('QC')]
validate-file file:
    uv run linkml-validate --schema {{soma_schema}} --target-class Container {{file}}
    {{term_validator_wrapper}} validate-data {{file}} -s {{soma_schema}} -t Container --labels -c {{oak_conf}}
    ALLOW_ABSTRACT_ONLY_MISSES=1 {{ref_validator_wrapper}} validate data {{file}} --schema {{soma_schema}} --target-class Container --config {{ref_conf}} --cache-dir {{refs_cache}} --no-full-text
    uv run python scripts/snippet_receipts.py check {{file}}

# Verify the evidence quotes in one kb file, including quotes from paywalled
# papers whose text only exists in the local cache. Builds a temporary merged
# cache (committed + local) and runs the quote checker against it. Prints the
# report to paste into the PR description. When the file quotes a paper whose
# committed cache entry is abstract-only, a passing run also writes a
# verification receipt (verification/PMID_<n>.json) — commit it with the PR
# so CI can hold the quotes to it (see check-receipts).
[group('QC')]
verify-snippets file:
    #!/usr/bin/env bash
    set -euo pipefail
    merged=$(mktemp -d)
    trap 'rm -rf "$merged"' EXIT
    [ -d {{refs_cache}} ] && cp {{refs_cache}}/*.md "$merged"/ 2>/dev/null || true
    # Merge, don't replace. When a paper is in BOTH caches the local PDF
    # extraction is APPENDED to the committed entry instead of overwriting it,
    # so the fetcher-written abstract stays visible to the quote checker.
    # Overwriting discarded the authoritative text: pypdf renders ligatures as
    # single codepoints and sprays spurious spaces around them and around
    # subscripts ("in <fl>ammation", "con <fi>rms", "PM 2.5"), so a quote that
    # is verbatim in the cached abstract could fail this check purely because
    # of a PDF artifact — and a failing check writes no receipt at all. The
    # append only ever adds more real text from the same paper, so it cannot
    # make a wrong quote pass.
    if [ -d {{refs_cache_local}} ]; then
        for local_file in {{refs_cache_local}}/*.md; do
            [ -e "$local_file" ] || continue
            base=$(basename "$local_file")
            if [ -f "$merged/$base" ]; then
                printf '\n\n## Full text (local PDF extraction)\n\n' >> "$merged/$base"
                awk 'seen >= 2 { print } /^---[[:space:]]*$/ { seen++ }' "$local_file" >> "$merged/$base"
            else
                cp "$local_file" "$merged"/
            fi
        done
    fi
    echo "Quote verification for {{file}} (committed + local cache):"
    {{ref_validator_wrapper}} validate data {{file}} --schema {{soma_schema}} --target-class Container --config {{ref_conf}} --cache-dir "$merged" --no-full-text
    uv run python scripts/snippet_receipts.py write {{file}}

# Check that every quote CI cannot verify (its paper is abstract-only in the
# committed cache) is covered by a committed verification receipt written by
# a passing local verify-snippets run. A receipt hash-binds the receipt to
# the exact snippet text, so a quote edited after verification fails here.
[group('QC')]
check-receipts:
    #!/usr/bin/env bash
    set -euo pipefail
    shopt -s nullglob
    files=({{kb_pubs_dir}}/*.yaml)
    if [ ${#files[@]} -eq 0 ]; then
        echo "No kb files in {{kb_pubs_dir}} yet — nothing to check."
        exit 0
    fi
    uv run python scripts/snippet_receipts.py check "${files[@]}"

# Validate every kb file (schema + terms + quotes), batched.
[group('QC')]
validate-all:
    #!/usr/bin/env bash
    set -euo pipefail
    shopt -s nullglob
    files=({{kb_pubs_dir}}/*.yaml)
    if [ ${#files[@]} -eq 0 ]; then
        echo "No kb files in {{kb_pubs_dir}} yet — nothing to validate."
        exit 0
    fi
    echo "Validating ${#files[@]} kb files..."
    uv run linkml-validate --schema {{soma_schema}} --target-class Container "${files[@]}"
    {{term_validator_wrapper}} validate-data "${files[@]}" -s {{soma_schema}} -t Container --labels -c {{oak_conf}}
    ALLOW_ABSTRACT_ONLY_MISSES=1 {{ref_validator_wrapper}} validate data "${files[@]}" --schema {{soma_schema}} --target-class Container --config {{ref_conf}} --cache-dir {{refs_cache}} --no-full-text
    echo "All kb files validated."

# Term-check the test fixtures with the same validator (and --labels) that
# gates kb/publications. The fixtures are source material that curation
# copies from (the claim-paper skill points extraction agents at them), so a
# mislabelled term here is latent until it lands in a real extraction and
# becomes a hard CI failure there (issue #137). Only the term validator runs
# here — fixtures have no committed reference-cache entries, so the
# reference/quote validator does not apply; schema shape is covered by
# _test-examples and the pytest suite. tests/data/invalid/ and
# tests/data/quote_mismatch/ stay excluded: they are deliberately broken.
[group('QC')]
validate-fixtures:
    #!/usr/bin/env bash
    set -euo pipefail
    shopt -s nullglob
    files=(tests/data/valid/*.yaml)
    if [ ${#files[@]} -eq 0 ]; then
        echo "No fixtures in tests/data/valid — nothing to validate."
        exit 0
    fi
    echo "Term-checking ${#files[@]} fixture files..."
    {{term_validator_wrapper}} validate-data "${files[@]}" -s {{soma_schema}} -t Container --labels -c {{oak_conf}}

# Check that no YAML file repeats a key (a silent way merges break files).
[group('QC')]
check-duplicate-keys *files:
    uv run python scripts/check_duplicate_yaml_keys.py {{files}}

# Check the paper queue: every stub parses, matches the stub schema, and no
# two stubs claim the same PMID. Fails only on broken files.
[group('QC')]
check-stubs:
    #!/usr/bin/env bash
    set -euo pipefail
    shopt -s nullglob
    files=({{stubs_dir}}/*.yaml)
    if [ ${#files[@]} -eq 0 ]; then
        echo "No stubs in {{stubs_dir}} yet — nothing to check."
        exit 0
    fi
    uv run linkml-validate -s {{stub_schema}} -C PublicationStub "${files[@]}"
    uv run python scripts/build_stubs.py --check-only

# Check the cross-paper ID rules over kb/publications: KeyEvent IDs are
# shared vocabulary (identical content merges; divergent content fails);
# every other ID must be unique to one paper.
[group('QC')]
check-entity-ids:
    uv run python scripts/build_workbook.py --check-only

# Smoke-test the DuckDB build: the schema still maps cleanly to tables, value
# objects stay flattened, and measurement_full still joins a number to its
# paper, assay and exposure. Catches soma-schema drift breaking the loader.
[group('QC')]
db-test:
    uv run python -m pytest tests/test_build_duckdb.py -q

# Run every automatic check. This is what CI runs on every PR, over the whole
# repository (checking only changed files lets two individually-green PRs
# break each other when both merge).
[group('QC')]
qc: check-duplicate-keys check-stubs check-entity-ids validate-all validate-fixtures check-receipts pipeline-test db-test
    @echo "All QC checks passed!"

# ============ Derived products ============

# Build the ONE pooled workbook from every per-paper YAML in kb/publications.
# The YAML files are the source of truth; this workbook is a generated
# product — never hand-edit it, never commit it in a curation PR (exports/
# is gitignored; CI publishes the current workbook from main).
[group('exports')]
generate-workbook out="exports/soma_extractions.xlsx":
    uv run python scripts/build_workbook.py --output "{{out}}"

# ============ Paper queue ============

# (Re)build the paper queue from corpus.csv: one stub per paper not already
# stubbed or extracted. Safe to re-run any time corpus.csv grows.
[group('curation')]
build-stubs:
    uv run python scripts/build_stubs.py

# List open claim issues (who is working on what right now).
[group('curation')]
fetch-claims out="tmp/claims.json":
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p "$(dirname {{out}})"
    gh issue list --label claim --state open \
      --json number,title,assignees,url,createdAt,closedByPullRequestsReferences \
      --limit 1000 > {{out}}
    echo "Open claims written to {{out}}"

# Show the next papers in the queue that nobody has claimed.
[group('curation')]
next-unclaimed count="5" claims="tmp/claims.json":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -f "{{claims}}" ]; then
        just fetch-claims {{claims}}
    fi
    uv run python scripts/build_stubs.py --next {{count}} --claims "{{claims}}"

# Run the YAML-to-Excel pipeline test on example data
[group('model development')]
pipeline-test:
  mkdir -p tmp
  uv run linkml-validate -s {{soma_schema}} tests/data/valid/Container-liu2024-pm25-cftr.yaml
  uv run python scripts/yaml_to_excel.py --input tests/data/valid/Container-liu2024-pm25-cftr.yaml --output tmp/Liu2024_pipeline_test.xlsx
  uv run linkml-validate -s {{soma_schema}} tests/data/valid/Container-montgomery2020-pm25-mucociliary.yaml
  uv run python scripts/yaml_to_excel.py --input tests/data/valid/Container-montgomery2020-pm25-mucociliary.yaml --output tmp/Montgomery2020_pipeline_test.xlsx
  @echo "Pipeline test completed. Output in tmp/"

# ============ Local analytical database (DuckDB) ============

# Build exports/soma.duckdb from every kb/publications/ YAML file. The YAML is
# the source of truth; this database is a generated product — never committed.
# Falls back to tests/data/valid only if kb/publications/ has no YAML files.
# Layout: one table per LinkML class (value objects flattened into named
# columns), plus measurement (one row per number), link (entity edges),
# term_ref (each use of an ontology term) and term (the terms themselves);
# then the analysis views assay, assay_output, measurement_full, evidence and
# term_usage. Pass --strict via scripts/build_duckdb.py to make the build fail
# on any warning; the recipe does not, because the current kb/ files raise
# content conflicts that need fixing in the YAML first.
[group('exports')]
build-db out="exports/soma.duckdb" kb_dir="":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -n "{{kb_dir}}" ]; then
        uv run python scripts/build_duckdb.py --kb-dir "{{kb_dir}}" --output "{{out}}"
    else
        uv run python scripts/build_duckdb.py --output "{{out}}"
    fi

# Dump every table and view as a TSV, for people who would rather open this in
# Excel, pandas or R than write SQL. measurement_full.tsv is the one to start
# with: one row per number with its paper, assay, exposure and key event.
[group('exports')]
dump-tsv out="exports/tsv" db="exports/soma.duckdb":
    #!/usr/bin/env bash
    set -euo pipefail
    [ -f "{{db}}" ] || just build-db "{{db}}"
    uv run python -c "import sys; sys.path.insert(0,'scripts'); \
      from build_duckdb import dump_tsv; from pathlib import Path; \
      w = dump_tsv(Path('{{db}}'), Path('{{out}}')); \
      print(f'Wrote {len(w)} TSV files to {{out}}')"

# Build the database and the TSV dump in one go.
[group('exports')]
build-db-all: build-db dump-tsv

# Print the generated DDL and views without building anything — the schema this
# DuckDB instance uses, derived from the installed soma-schema.
[group('exports')]
db-schema:
    uv run python scripts/build_duckdb.py --ddl-only

# The vanilla LinkML relational model, for provenance and comparison. Differs
# from db-schema deliberately: it keeps QuantityValue as a joined table (114 FK
# columns across the schema) and gives reused children one FK column per
# possible parent (EvidenceItem gets 27). See scripts/soma_duckdb.py.
#
# The dialect is sqlite, not duckdb: gen-sqltables resolves dialects through
# SQLAlchemy and there is no duckdb dialect installed. It makes no difference
# here — DuckDB executes this DDL as-is once the `--` comment lines are stripped
# (they contain semicolons and prose, so they break naive statement splitting).
[group('exports')]
db-schema-linkml out="tmp/soma.linkml.sql":
    mkdir -p "$(dirname {{out}})"
    uv run gen-sqltables --dialect sqlite {{soma_schema}} > {{out}}
    @echo "Wrote {{out}}"

# Open a DuckDB shell on the built database, or run one query:
#   just query
#   just query 'SELECT measurement, value, unit_label FROM measurement_full LIMIT 10'
[group('exports')]
query sql="" db="exports/soma.duckdb":
    #!/usr/bin/env bash
    set -euo pipefail
    [ -f "{{db}}" ] || just build-db "{{db}}"
    uv run python scripts/soma_query.py "{{db}}" "{{sql}}"

# Build the static KB review site — one page per extracted paper plus the
# pooled key-event network. Deployed to GitHub Pages from each release by
# .github/workflows/deploy-kb-site.yaml; this recipe is the local preview.
[group('exports')]
gen-site out="_site" version="dev":
    uv run python scripts/build_site.py --out {{out}} --version {{version}}

# Build the KB site and serve it at http://localhost:8900 for review.
[group('exports')]
serve-site out="_site": (gen-site out)
    uv run python -m http.server --directory {{out}} 8900

# Package the DataHarmonizer build and the MkDocs schema docs into one static
# site. Shared by deploy-kb-site.yaml (which deploys it under /docs/ in the
# Pages artifact) and deploy-docs.yaml (build-only validation), so the steps
# live in one place. Assumes `just gen-project` and `just gen-doc` have run.
[group('exports')]
build-docs-site out="tmp/docs-site": build-dh
    uv run mkdocs build -d {{out}}
