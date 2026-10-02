#!/usr/bin/env python3
"""Build the static KB review site from kb/publications/ YAML files.

The per-paper YAML files are the source of truth — validated, quote-checked,
reviewed. This site is a generated product for human reviewers: one page per
paper showing every assay, exposure condition, output and evidence quote, plus
a pooled key-event network across all papers. It is deployed to GitHub Pages
by .github/workflows/deploy-kb-site.yaml whenever a release is published, and
is never committed to the repository.

Usage:
    uv run python scripts/build_site.py                          # kb/publications -> _site/
    uv run python scripts/build_site.py --kb-dir tests/data/valid --out tmp/site
    uv run python scripts/build_site.py --version v1.0.0         # stamp a release tag
"""
from __future__ import annotations

import argparse
import datetime
import html
import re
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = Path(__file__).resolve().parent / "site_templates"
REPO = "EHS-Data-Standards/somamech"

LEVEL_ORDER = ["molecular", "cellular", "tissue", "organ", "organism", "unspecified"]
SUPPORT_RANK = {"strong": 3, "moderate": 2, "weak": 1, "not_specified": 0, None: 0}

# Fields rendered explicitly by the templates; every OTHER scalar field on an
# entity is shown generically as a "key: value" chip, so new schema slots
# appear on the site without a template change.
ASSAY_KNOWN_KEYS = {
    "id", "name", "description", "evidence", "has_exposure_condition",
    "has_specified_output", "informs_on_key_event", "study_subject",
    "follows_protocols", "assay_date",
}
PROTOCOL_KNOWN_KEYS = {"id", "name", "description", "protocol_type", "equipment_required"}


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


ACRONYMS = {"mcc", "balf", "asl", "cftr", "egfr", "foxj", "ros"}


def section_label(key: str) -> str:
    words = [w.upper() if w in ACRONYMS else w for w in key.split("_")]
    if words and words[0] not in {w.upper() for w in ACRONYMS}:
        words[0] = words[0].capitalize()
    return " ".join(words)


def short_label(slug: str) -> str:
    """Compact per-paper label for cross-reference lists: 'han2021-pm25-...' -> 'han2021'."""
    return slug.split("-", 1)[0]


def count_snippets(obj) -> int:
    if isinstance(obj, dict):
        n = 1 if ("snippet" in obj and "reference" in obj) else 0
        return n + sum(count_snippets(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(count_snippets(v) for v in obj)
    return 0


def load_publication(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    source = data.get("source_publication") or {}
    reference = source.get("reference") or ""
    pmid = reference[5:] if reference.startswith("PMID:") else None

    sections, subjects, agents, species = [], {}, {}, {}
    for key, value in data.items():
        if not (key.endswith("_assays") and isinstance(value, list)):
            continue
        sections.append({"key": key, "label": section_label(key), "entries": value})
        for assay in value:
            subject = assay.get("study_subject")
            if isinstance(subject, dict) and subject.get("id") not in subjects:
                subjects[subject.get("id")] = subject
            for cond in assay.get("has_exposure_condition") or []:
                agent = (cond.get("exposure_agent") or {}).get("name")
                if agent:
                    agents[agent] = True
            sp = ((subject or {}).get("model_species") or {}).get("name")
            if sp:
                species[sp] = True

    slug = slugify(path.stem.removeprefix("Container-"))
    title = source.get("reference_title") or path.stem
    pub = {
        "file": path.name,
        "slug": slug,
        "short": short_label(slug),
        "title": title,
        "pmid": pmid,
        "doi": source.get("doi"),
        "sections": sections,
        "subjects": list(subjects.values()),
        "agents": sorted(agents),
        "species": sorted(species),
        "protocols": data.get("protocols") or [],
        "response_comparisons": data.get("response_comparisons") or [],
        "key_events": data.get("key_events") or [],
        "key_event_relationships": data.get("key_event_relationships") or [],
        "n_assays": sum(len(s["entries"]) for s in sections),
        "n_evidence": count_snippets(data),
        "n_kers": len(data.get("key_event_relationships") or []),
    }
    ke_names = {ke.get("name") for ke in iter_key_events(pub) if ke.get("name")}
    pub["search_text"] = " ".join(
        filter(None, [title.lower(), (pmid or "").lower(),
                      " ".join(pub["agents"]).lower(), " ".join(pub["species"]).lower(),
                      " ".join(s["label"].lower() for s in sections),
                      " ".join(sorted(n.lower() for n in ke_names))])
    )
    return pub


def iter_key_events(pub: dict):
    """Every KeyEvent mention in a publication, in document order."""
    for sec in pub["sections"]:
        for assay in sec["entries"]:
            ke = assay.get("informs_on_key_event")
            if isinstance(ke, dict):
                yield ke
    for ke in pub["key_events"]:
        yield ke
    for ker in pub["key_event_relationships"]:
        for side in ("upstream_event", "downstream_event"):
            ke = ker.get(side)
            if isinstance(ke, dict):
                yield ke


def aggregate(pubs: list[dict]):
    """Pool key events and relationships across papers."""
    key_events: dict[str, dict] = {}
    for pub in pubs:
        for ke in iter_key_events(pub):
            ke_id = ke.get("id")
            if not ke_id:
                continue
            entry = key_events.setdefault(ke_id, {
                "id": ke_id,
                "anchor": slugify(ke_id),
                "name": ke.get("name") or ke_id,
                "level": ke.get("level_of_biological_organization") or "unspecified",
                "papers": {},
            })
            entry["papers"][pub["slug"]] = {"slug": pub["slug"], "short": pub["short"]}
    for entry in key_events.values():
        entry["papers"] = list(entry["papers"].values())

    kers: dict[tuple, dict] = {}
    for pub in pubs:
        for ker in pub["key_event_relationships"]:
            up, dn = ker.get("upstream_event") or {}, ker.get("downstream_event") or {}
            if not (up.get("id") and dn.get("id")):
                continue
            key = (up["id"], dn["id"])
            entry = kers.setdefault(key, {
                "upstream_id": up["id"], "downstream_id": dn["id"],
                "upstream_name": up.get("name") or up["id"],
                "downstream_name": dn.get("name") or dn["id"],
                "up_anchor": slugify(up["id"]), "dn_anchor": slugify(dn["id"]),
                "up_level": up.get("level_of_biological_organization") or "unspecified",
                "dn_level": dn.get("level_of_biological_organization") or "unspecified",
                "relationship_type": ker.get("relationship_type") or "leads to",
                "support": ker.get("evidence_support") or "not_specified",
                "papers": {},
            })
            entry["papers"][pub["slug"]] = {"slug": pub["slug"], "short": pub["short"]}
            if SUPPORT_RANK.get(ker.get("evidence_support"), 0) > SUPPORT_RANK.get(entry["support"], 0):
                entry["support"] = ker["evidence_support"]
    for entry in kers.values():
        entry["papers"] = list(entry["papers"].values())

    def level_key(ke):
        return (LEVEL_ORDER.index(ke["level"]) if ke["level"] in LEVEL_ORDER else len(LEVEL_ORDER),
                ke["name"].lower())

    return sorted(key_events.values(), key=level_key), list(kers.values())


# ---------------------------------------------------------------------------
# Key-event network SVG (layered left-to-right by level of organization)
# ---------------------------------------------------------------------------
NODE_W, NODE_H, V_GAP, COL_GAP, TOP, MARGIN = 196, 46, 16, 130, 46, 12


def wrap_label(name: str, width: int = 29) -> list[str]:
    words, lines, cur = name.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    if len(lines) > 2:
        lines = [lines[0], lines[1][: width - 1] + "…"]
    return lines


def build_network_svg(key_events: list[dict], kers: list[dict]) -> str:
    levels = [lvl for lvl in LEVEL_ORDER if any(ke["level"] == lvl for ke in key_events)]
    columns = {lvl: [ke for ke in key_events if ke["level"] == lvl] for lvl in levels}
    col_of = {ke["id"]: levels.index(ke["level"]) for ke in key_events}

    neighbors: dict[str, list[str]] = {}
    for ker in kers:
        neighbors.setdefault(ker["upstream_id"], []).append(ker["downstream_id"])
        neighbors.setdefault(ker["downstream_id"], []).append(ker["upstream_id"])

    # Barycenter sweeps: order each column by the mean row of connected nodes,
    # which keeps most edges short and roughly horizontal.
    for _ in range(3):
        row_of = {ke["id"]: i for col in columns.values() for i, ke in enumerate(col)}
        for lvl in levels:
            col = columns[lvl]
            col.sort(key=lambda ke: (
                sum(row_of[n] for n in neighbors.get(ke["id"], []) if n in row_of)
                / max(1, len([n for n in neighbors.get(ke["id"], []) if n in row_of]))
                if any(n in row_of for n in neighbors.get(ke["id"], [])) else row_of[ke["id"]],
                row_of[ke["id"]],
            ))

    pos = {}
    for c, lvl in enumerate(levels):
        x = MARGIN + c * (NODE_W + COL_GAP)
        for r, ke in enumerate(columns[lvl]):
            pos[ke["id"]] = (x, TOP + r * (NODE_H + V_GAP))

    width = MARGIN * 2 + len(levels) * NODE_W + (len(levels) - 1) * COL_GAP
    height = TOP + max(len(col) for col in columns.values()) * (NODE_H + V_GAP) + MARGIN

    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="{width}" role="img" '
        f'aria-label="Key-event network: {len(key_events)} key events, {len(kers)} relationships. '
        f'The tables below list the same data." xmlns="http://www.w3.org/2000/svg">',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" class="arrowhead"/></marker></defs>',
    ]
    for c, lvl in enumerate(levels):
        x = MARGIN + c * (NODE_W + COL_GAP) + NODE_W / 2
        parts.append(f'<text x="{x}" y="{TOP - 18}" text-anchor="middle" class="col-label">{html.escape(lvl)}</text>')

    for ker in kers:
        if ker["upstream_id"] not in pos or ker["downstream_id"] not in pos:
            continue
        (sx, sy), (dx, dy) = pos[ker["upstream_id"]], pos[ker["downstream_id"]]
        sc, dc = col_of[ker["upstream_id"]], col_of[ker["downstream_id"]]
        sy, dy = sy + NODE_H / 2, dy + NODE_H / 2
        if sc < dc:          # forward: right edge -> left edge
            x1, x2 = sx + NODE_W, dx
            mid = (x1 + x2) / 2
            d = f"M {x1} {sy} C {mid} {sy}, {mid} {dy}, {x2} {dy}"
        elif sc > dc:        # backward: left edge -> right edge
            x1, x2 = sx, dx + NODE_W
            mid = (x1 + x2) / 2
            d = f"M {x1} {sy} C {mid} {sy}, {mid} {dy}, {x2} {dy}"
        else:                # same column: loop out the right side
            x1 = sx + NODE_W
            bulge = x1 + 46
            d = f"M {x1} {sy} C {bulge} {sy}, {bulge} {dy}, {x1 + 4} {dy}"
        support = ker["support"] if ker["support"] in SUPPORT_RANK else "not_specified"
        stroke = "2.5" if support == "strong" else "1.6"
        dash = ' stroke-dasharray="5 4"' if support in ("weak", "not_specified") else ""
        label = (f'{html.escape(ker["upstream_name"])} {html.escape(ker["relationship_type"])} '
                 f'{html.escape(ker["downstream_name"])} ({support} support)')
        parts.append(f'<path class="ker-edge" d="{d}" stroke-width="{stroke}"{dash} '
                     f'marker-end="url(#arrow)"><title>{label}</title></path>')

    for ke in key_events:
        x, y = pos[ke["id"]]
        lines = wrap_label(ke["name"])
        text_y = y + (NODE_H / 2 - 6 * (len(lines) - 1)) + 4
        tspans = "".join(
            f'<tspan x="{x + NODE_W / 2}" y="{text_y + i * 14}">{html.escape(line)}</tspan>'
            for i, line in enumerate(lines)
        )
        parts.append(
            f'<a href="#{ke["anchor"]}"><g class="ke-node">'
            f'<title>{html.escape(ke["name"])} ({ke["level"]}; {len(ke["papers"])} paper(s))</title>'
            f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="8" '
            f'stroke="var(--lvl-{ke["level"]})"/>'
            f'<text font-size="11" text-anchor="middle">{tspans}</text>'
            f"</g></a>"
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------


def build_site(kb_dir: Path, out_dir: Path, version: str) -> int:
    files = sorted(kb_dir.glob("Container-*.yaml"))
    pubs = [load_publication(f) for f in files]
    pubs.sort(key=lambda p: p["slug"])
    key_events, kers = aggregate(pubs)

    stats = {
        "publications": len(pubs),
        "assays": sum(p["n_assays"] for p in pubs),
        "evidence": sum(p["n_evidence"] for p in pubs),
        "key_events": len(key_events),
        "kers": len(kers),
    }
    all_species = sorted({sp for p in pubs for sp in p["species"]})
    levels_present = [lvl for lvl in LEVEL_ORDER if any(ke["level"] == lvl for ke in key_events)]

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(enabled_extensions=("j2", "html")),
    )
    env.filters["slugify"] = slugify

    # A real tag ref makes "Source YAML" links point at the released tree.
    ref = version if version not in ("dev", "main") else "main"
    common = {
        "repo": REPO,
        "ref": ref,
        "version": version,
        "build_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "publications").mkdir(exist_ok=True)
    (out_dir / "assets").mkdir(exist_ok=True)
    shutil.copy(TEMPLATES / "site.css", out_dir / "assets" / "site.css")

    (out_dir / "index.html").write_text(env.get_template("index.html.j2").render(
        root=".", active="publications", publications=pubs, stats=stats,
        all_species=all_species, **common))

    network_svg = Markup(build_network_svg(key_events, kers)) if key_events else ""
    (out_dir / "key-events.html").write_text(env.get_template("key_events.html.j2").render(
        root=".", active="key-events", key_events=key_events, kers=kers, stats=stats,
        levels_present=levels_present, network_svg=network_svg, **common))

    pub_template = env.get_template("publication.html.j2")
    for pub in pubs:
        (out_dir / "publications" / f"{pub['slug']}.html").write_text(pub_template.render(
            root="..", active="publications", pub=pub,
            assay_known_keys=ASSAY_KNOWN_KEYS, protocol_known_keys=PROTOCOL_KNOWN_KEYS,
            **common))

    print(f"Site built: {len(pubs)} publications, {stats['assays']} assays, "
          f"{stats['key_events']} key events, {stats['kers']} relationships -> {out_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kb-dir", type=Path, default=ROOT / "kb" / "publications")
    parser.add_argument("--out", type=Path, default=ROOT / "_site")
    parser.add_argument("--version", default="dev",
                        help="Release tag to stamp into the footer and source links")
    args = parser.parse_args()
    return build_site(args.kb_dir, args.out, args.version)


if __name__ == "__main__":
    sys.exit(main())
