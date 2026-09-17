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
soma_schema := "src/soma/schema/soma.yaml"
stub_schema := "src/soma/schema/publication_stub.yaml"
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

# ============ Validation ============

# Validate one kb file: schema, then ontology terms, then evidence quotes.
[group('QC')]
validate-file file:
    uv run linkml-validate --schema {{soma_schema}} --target-class Container {{file}}
    {{term_validator_wrapper}} validate-data {{file}} -s {{soma_schema}} -t Container --labels -c {{oak_conf}}
    {{ref_validator_wrapper}} validate data {{file}} --schema {{soma_schema}} --target-class Container --config {{ref_conf}} --cache-dir {{refs_cache}} --no-full-text

# Verify the evidence quotes in one kb file, including quotes from paywalled
# papers whose text only exists in the local cache. Builds a temporary merged
# cache (committed + local) and runs the quote checker against it. Prints the
# report to paste into the PR description.
[group('QC')]
verify-snippets file:
    #!/usr/bin/env bash
    set -euo pipefail
    merged=$(mktemp -d)
    trap 'rm -rf "$merged"' EXIT
    [ -d {{refs_cache}} ] && cp {{refs_cache}}/*.md "$merged"/ 2>/dev/null || true
    [ -d {{refs_cache_local}} ] && cp {{refs_cache_local}}/*.md "$merged"/ 2>/dev/null || true
    echo "Quote verification for {{file}} (committed + local cache):"
    {{ref_validator_wrapper}} validate data {{file}} --schema {{soma_schema}} --target-class Container --config {{ref_conf}} --cache-dir "$merged" --no-full-text

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
    {{ref_validator_wrapper}} validate data "${files[@]}" --schema {{soma_schema}} --target-class Container --config {{ref_conf}} --cache-dir {{refs_cache}} --no-full-text
    echo "All kb files validated."

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

# Run every automatic check. This is what CI runs on every PR, over the whole
# repository (checking only changed files lets two individually-green PRs
# break each other when both merge).
[group('QC')]
qc: check-duplicate-keys check-stubs check-entity-ids validate-all pipeline-test
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
  uv run linkml-validate -s src/soma/schema/soma.yaml tests/data/valid/Container-liu2024-pm25-cftr.yaml
  uv run python scripts/yaml_to_excel.py --input tests/data/valid/Container-liu2024-pm25-cftr.yaml --output tmp/Liu2024_pipeline_test.xlsx
  uv run linkml-validate -s src/soma/schema/soma.yaml tests/data/valid/Container-montgomery2020-pm25-mucociliary.yaml
  uv run python scripts/yaml_to_excel.py --input tests/data/valid/Container-montgomery2020-pm25-mucociliary.yaml --output tmp/Montgomery2020_pipeline_test.xlsx
  @echo "Pipeline test completed. Output in tmp/"
