# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Hold data/requirements-seed.yaml to the esdis requirement concepts.

The requirement concepts under nasa-daac-knowledge/knowledge/esdis/
requirements/ are the authority for what a rule says, which class it
carries, which sources back it, and which check binds it. The seed is
the observatory's hand-authored projection of those concepts, kept
because the sweeper reads YAML and never markdown. This tool holds the
two together: every seed rule names its concept, and every field the
seed carries is compared with that concept exactly, never by
paraphrase, which is the drift register R2 is about.

Per rule:
  concept    the path exists under the concepts root and is a
             type: requirement concept with parseable frontmatter
  class      the seed class equals the concept class
  statement  the seed statement equals the concept title or the first
             sentence of the concept body (footnote marks ignored)
  source     every id in source.cites is an id in the concept's
             sources list, and a MUST rule cites a verified section
  check      a cmr-structural id is the one the concept's Check
             binding paragraph names as Structural; a pyquarc id is
             either the co-build placeholder, accepted only when that
             paragraph speaks of pyQuARC, or a check id the paragraph
             names
Across the seed: rule ids are unique, no two rules share a concept,
and every requirement concept in the bundle has a rule, so nothing is
orphaned in either direction.

Exit 0 when everything agrees; 1 on any disagreement, each printed
with rule id, field, seed value and concept value; 2 on a malfunction
(unreadable seed, missing concepts root). No network anywhere: the
concepts are read from disk, by default the sibling clone at
../nasa-daac-knowledge/knowledge/esdis relative to this repository,
or the directory given with --concepts. CI checks the public
knowledge repository out beside this one and runs the same command.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SEED = REPO / "data" / "requirements-seed.yaml"
DEFAULT_CONCEPTS = REPO.parent / "nasa-daac-knowledge" / "knowledge" / "esdis"
PLACEHOLDER = "co-build-map"
FOOTNOTE = re.compile(r"\[\^[^\]]+\]")


class Malfunction(Exception):
    """Something the tool cannot read; exit 2, never a finding."""


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("no frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    meta = yaml.safe_load(text[4:end])
    if not isinstance(meta, dict):
        raise ValueError("frontmatter is not a mapping")
    return meta, text[end + 5:]


def paragraphs(body: str) -> list[str]:
    """Body paragraphs joined onto one line each, footnote marks
    removed, the title heading skipped."""
    out, cur = [], []
    for line in body.splitlines() + [""]:
        if line.strip():
            if line.startswith("# ") and not cur:
                continue
            cur.append(line.strip())
        elif cur:
            out.append(FOOTNOTE.sub("", " ".join(cur)))
            cur = []
    return out


def first_sentence(body: str) -> str:
    for para in paragraphs(body):
        if para.startswith("[^"):
            continue
        m = re.match(r"(.+?\.)(\s|$)", para)
        return m.group(1) if m else para
    return ""


def check_binding(body: str) -> str:
    for para in paragraphs(body):
        if para.startswith("**Check binding.**"):
            return para
    return ""


def norm(s: str) -> str:
    s = FOOTNOTE.sub("", str(s or ""))
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s[:-1] if s.endswith(".") else s


def load_concept(path: Path) -> dict:
    meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    return {
        "type": meta.get("type"),
        "title": str(meta.get("title", "")),
        "class": str(meta.get("class", "")),
        "sources": [str(s.get("id")) for s in meta.get("sources") or []
                    if isinstance(s, dict)],
        "first": first_sentence(body),
        "binding": check_binding(body),
    }


def compare(seed: dict, concepts_root: Path) -> list[str]:
    """Every disagreement as one line; empty means the seed agrees."""
    problems: list[str] = []
    req_dir = concepts_root / "requirements"
    if not req_dir.is_dir():
        raise Malfunction(f"no requirements/ under {concepts_root}")
    rules = seed.get("rules") if isinstance(seed, dict) else None
    if not isinstance(rules, list):
        raise Malfunction("seed has no rules list")

    seen_ids: dict[str, int] = {}
    seen_concepts: dict[str, str] = {}
    for r in rules:
        rid = str(r.get("id", "?"))
        seen_ids[rid] = seen_ids.get(rid, 0) + 1
        rel = r.get("concept")
        if not rel:
            problems.append(f"{rid}: concept: missing (every rule names "
                            "its esdis concept path)")
            continue
        rel = str(rel)
        if rel in seen_concepts:
            problems.append(f"{rid}: concept: {rel} is already the "
                            f"concept of {seen_concepts[rel]}")
        seen_concepts.setdefault(rel, rid)
        path = concepts_root / rel
        if not path.is_file():
            problems.append(f"{rid}: concept: {rel} not found under "
                            f"{concepts_root}")
            continue
        try:
            c = load_concept(path)
        except (ValueError, yaml.YAMLError) as exc:
            problems.append(f"{rid}: concept: {rel} unreadable ({exc})")
            continue
        if c["type"] != "requirement":
            problems.append(f"{rid}: concept: {rel} has type "
                            f"{c['type']!r}, not requirement")

        if str(r.get("class", "")) != c["class"]:
            problems.append(f"{rid}: class: seed {r.get('class')!r}, "
                            f"concept {c['class']!r}")

        stmt = norm(r.get("statement"))
        if stmt not in (norm(c["title"]), norm(c["first"])):
            problems.append(f"{rid}: statement: seed {r.get('statement')!r} "
                            f"is neither the concept title {c['title']!r} "
                            f"nor its first sentence {c['first']!r}")

        src = r.get("source") if isinstance(r.get("source"), dict) else {}
        cites = src.get("cites")
        if not isinstance(cites, list) or not cites:
            problems.append(f"{rid}: source.cites: missing (list the "
                            "concept source ids this rule rests on)")
        else:
            for cid in cites:
                if str(cid) not in c["sources"]:
                    problems.append(f"{rid}: source.cites: {cid!r} is not "
                                    f"a source id of {rel} "
                                    f"(has {c['sources']})")
        if str(r.get("class")) == "MUST" and src.get("section") != "verified":
            problems.append(f"{rid}: source.section: MUST needs "
                            f"'verified', seed has {src.get('section')!r}")

        chk = r.get("check") if isinstance(r.get("check"), dict) else {}
        binding, cid = str(chk.get("binding", "")), str(chk.get("id", ""))
        para = c["binding"]
        if not para:
            problems.append(f"{rid}: check: {rel} has no Check binding "
                            "paragraph")
        elif binding == "cmr-structural":
            m = re.search(r"Structural:\s*([A-Za-z0-9_-]+)", para)
            named = m.group(1) if m else None
            if named != cid:
                problems.append(f"{rid}: check.id: seed {cid!r}, concept "
                                f"names Structural: {named!r}")
        elif binding == "pyquarc":
            if cid == PLACEHOLDER:
                if "pyquarc" not in para.lower():
                    problems.append(f"{rid}: check.id: placeholder "
                                    f"{PLACEHOLDER!r} but the concept's "
                                    "Check binding never mentions pyQuARC")
            elif not re.search(rf"(?<![A-Za-z0-9_]){re.escape(cid)}"
                               r"(?![A-Za-z0-9_])", para):
                problems.append(f"{rid}: check.id: {cid!r} is not named "
                                f"in the concept's Check binding")
        else:
            problems.append(f"{rid}: check.binding: {binding!r} is neither "
                            "cmr-structural nor pyquarc")

    for rid, n in seen_ids.items():
        if n > 1:
            problems.append(f"{rid}: id: appears {n} times")
    for path in sorted(req_dir.glob("*.md")):
        rel = f"requirements/{path.name}"
        if rel not in seen_concepts:
            problems.append(f"(no rule): concept: {rel} has no seed rule")
    return problems


def run(seed_path: Path, concepts_root: Path) -> int:
    try:
        seed = yaml.safe_load(seed_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"seed_check: cannot read {seed_path}: {exc}", file=sys.stderr)
        return 2
    try:
        problems = compare(seed, concepts_root)
    except Malfunction as exc:
        print(f"seed_check: {exc}", file=sys.stderr)
        return 2
    n_rules = len(seed.get("rules", []))
    n_concepts = len(list((concepts_root / "requirements").glob("*.md")))
    for p in problems:
        print(f"DISAGREE {p}")
    verdict = "PASS" if not problems else "FAIL"
    print(f"{verdict} seed_check: {n_rules} rules against {n_concepts} "
          f"concepts under {concepts_root}, {len(problems)} disagreements")
    return 0 if not problems else 1


# --- selftest: a temporary bundle and seed, no network, no sibling clone

CONCEPT_TMPL = """---
type: requirement
title: {title}
description: "{title}"
tags: [requirement]
status: draft
class: {cls}
sources:
{sources}---

# {title}

{first} Second sentence with a note.[^a]

**Check binding.** {binding}

[^a]: a footnote
"""


def _concept(title, cls, sources, first, binding):
    src = "".join(f"  - id: {s}\n    resource: https://example.invalid/{s}\n"
                  f"    title: {s}\n" for s in sources)
    return CONCEPT_TMPL.format(title=title, cls=cls, sources=src,
                               first=first, binding=binding)


def _good_seed():
    return {"rules": [
        {"id": "req-a", "concept": "requirements/a.md", "class": "MUST",
         "statement": "Alpha declares its extent.",
         "source": {"cites": ["s1"], "section": "verified"},
         "check": {"binding": "cmr-structural", "id": "alpha-present"}},
        {"id": "req-b", "concept": "requirements/b.md", "class": "SHOULD",
         "statement": "Beta is present",
         "source": {"cites": ["s2"], "section": "attributed"},
         "check": {"binding": "pyquarc", "id": PLACEHOLDER}},
        {"id": "req-c", "concept": "requirements/c.md", "class": "SHOULD",
         "statement": "Gamma resolves",
         "source": {"cites": ["s2"], "section": "attributed"},
         "check": {"binding": "pyquarc", "id": "gamma_check"}},
    ]}


def selftest() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "esdis"
        req = root / "requirements"
        req.mkdir(parents=True)
        (req / "a.md").write_text(_concept(
            "Alpha is required", "MUST", ["s1"],
            "Alpha declares its extent.[^a]",
            "Structural: alpha-present (cmr-structural, the sweeper)."),
            encoding="utf-8")
        (req / "b.md").write_text(_concept(
            "Beta is present", "SHOULD", ["s2"],
            "Beta is present in the record as reviewed practice.",
            "pyQuARC candidates, pending confirmation: beta_check."),
            encoding="utf-8")
        (req / "c.md").write_text(_concept(
            "Gamma resolves", "SHOULD", ["s2"],
            "Gamma resolves without error.",
            "pyQuARC candidates: gamma_check, gamma_secure_check."),
            encoding="utf-8")

        def probs(mutate=None):
            seed = _good_seed()
            if mutate:
                mutate(seed)
            return compare(seed, root)

        def expect(name, mutate, *needles):
            got = probs(mutate)
            joined = "\n".join(got)
            ok = len(got) == len(needles) and all(n in joined for n in needles)
            print(f"  {'ok' if ok else 'FAIL'} {name}: {len(got)} "
                  f"disagreement(s)")
            if not ok:
                for g in got:
                    print("      " + g)
            return ok

        results = [
            expect("agreement", None),
            expect("class mismatch",
                   lambda s: s["rules"][1].__setitem__("class", "MUST"),
                   "req-b: class:", "req-b: source.section:"),
            expect("missing concept file",
                   lambda s: s["rules"][2].__setitem__(
                       "concept", "requirements/zed.md"),
                   "req-c: concept: requirements/zed.md not found",
                   "requirements/c.md has no seed rule"),
            expect("no concept key",
                   lambda s: s["rules"][2].pop("concept"),
                   "req-c: concept: missing",
                   "requirements/c.md has no seed rule"),
            expect("structural id drift",
                   lambda s: s["rules"][0]["check"].__setitem__(
                       "id", "alpha-declared"),
                   "req-a: check.id: seed 'alpha-declared'"),
            expect("paraphrased statement",
                   lambda s: s["rules"][0].__setitem__(
                       "statement", "Alpha declares an extent."),
                   "req-a: statement:"),
            expect("statement may equal the title",
                   lambda s: s["rules"][0].__setitem__(
                       "statement", "Alpha is required")),
            expect("unknown source id",
                   lambda s: s["rules"][1]["source"].__setitem__(
                       "cites", ["s9"]),
                   "req-b: source.cites: 's9'"),
            expect("no cites",
                   lambda s: s["rules"][1]["source"].pop("cites"),
                   "req-b: source.cites: missing"),
            expect("MUST without verified section",
                   lambda s: s["rules"][0]["source"].__setitem__(
                       "section", "attributed"),
                   "req-a: source.section:"),
            expect("pyquarc id not named",
                   lambda s: s["rules"][2]["check"].__setitem__(
                       "id", "gamma_other_check"),
                   "req-c: check.id: 'gamma_other_check' is not named"),
            expect("placeholder against a structural-only concept",
                   lambda s: s["rules"][0]["check"].update(
                       binding="pyquarc", id=PLACEHOLDER),
                   "req-a: check.id: placeholder"),
            expect("unknown binding",
                   lambda s: s["rules"][0]["check"].__setitem__(
                       "binding", "manual"),
                   "req-a: check.binding: 'manual'"),
            expect("two rules on one concept",
                   lambda s: s["rules"][2].__setitem__(
                       "concept", "requirements/b.md"),
                   "req-c: concept: requirements/b.md is already",
                   "req-c: statement:", "req-c: check.id:",
                   "requirements/c.md has no seed rule"),
            expect("duplicate rule id",
                   lambda s: s["rules"][2].__setitem__("id", "req-b"),
                   "req-b: id: appears 2 times"),
        ]
        # The whole file, through run(): exit code and summary line.
        seed_file = Path(td) / "seed.yaml"
        seed_file.write_text(yaml.safe_dump(_good_seed()), encoding="utf-8")
        results.append(run(seed_file, root) == 0)
        results.append(run(seed_file, Path(td) / "nowhere") == 2)
    if all(results):
        print(f"PASS seed_check selftest ({len(results)} scenarios)")
        return 0
    print("FAIL seed_check selftest")
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("seed", nargs="?", default=DEFAULT_SEED, type=Path,
                    help="rules seed (default data/requirements-seed.yaml)")
    ap.add_argument("--concepts", type=Path, default=DEFAULT_CONCEPTS,
                    help="esdis bundle root holding requirements/ "
                         "(default: the sibling nasa-daac-knowledge clone)")
    ap.add_argument("--selftest", action="store_true",
                    help="exercise the checks on a temporary bundle and "
                         "seed; touches nothing else")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    return run(args.seed, args.concepts)


if __name__ == "__main__":
    sys.exit(main())
