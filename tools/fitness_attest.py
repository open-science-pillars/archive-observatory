#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Fitness-for-use attestation: verify a declaration against signed
validity domains and emit a receipt naming the governing concepts.

Verdict semantics (settled before any domain was authored; the
vocabulary file data/claim-classes.yaml is the governed source):
- OUT: a SIGNED exclusion domain covers the declaration. Exclusions
  take precedence over everything and trigger on INTERSECTION (a
  declaration that touches excluded scope is tainted).
- IN: no exclusion applies and a SIGNED supporting domain fully
  CONTAINS the declaration: product matches, claim class matches with
  one-level subsumption only, declared region inside the domain
  region, declared period inside the domain period.
- UNADJUDICATED: no steward has spoken. Honest silence, never failure.
  Draft (unsigned) domains never adjudicate; the receipt lists them as
  advisory so authors see where signature would speak.

"Signed" means the domain concept carries at least one verified event
by a human: actor (the same trust key the whole format uses). The
attester verifies the DECLARATION, not the analysis; the receipt
records declaration_provenance, and only hand-declared exists until
capsule derivation lands (the capsule tier is refused until then, so
a receipt can never claim assurance that does not exist).

Usage:
  fitness_attest.py BUNDLE_ROOT [BUNDLE_ROOT ...] --product SHORTNAME
      --claim CLASS --region latmin,latmax,lonmin,lonmax|global
      --period YYYY-MM:YYYY-MM|any [--provenance hand-declared]
      [--classes data/claim-classes.yaml] [--receipt OUT.json]
  fitness_attest.py --selftest
"""

import argparse
import datetime
import hashlib
import json
import sys
import uuid
from pathlib import Path

import yaml

HAND = "hand-declared"


def parse_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    try:
        return yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return None


def is_signed(fm: dict) -> bool:
    v = fm.get("verified")
    evs = [v] if isinstance(v, dict) else (v if isinstance(v, list) else [])
    return any(isinstance(e, dict) and str(e.get("by", "")).startswith("human:")
               for e in evs)


def load_domains(roots):
    for root in roots:
        for p in sorted(Path(root).rglob("*.md")):
            fm = parse_frontmatter(p)
            if fm and fm.get("type") == "validity-domain" and isinstance(fm.get("domain"), dict):
                yield str(p), fm


def load_classes(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    umbrella = {}
    ids = set()
    for c in doc.get("classes", []):
        ids.add(c["id"])
        for child in c.get("children", []) or []:
            umbrella.setdefault(child, set()).add(c["id"])
    return {"ids": ids, "umbrella_of": umbrella}


def str_list(v) -> list | None:
    """A list of strings, or None. Register R5: scalar strings are
    NEVER read through list semantics (substring membership,
    character iteration), so anything else is malformed."""
    if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
        return v
    return None


def validate_domain(dom: dict, vocab: dict) -> list:
    """Structural validation before any adjudication (register R5,
    PR 5 round 1 findings F1 and F2). A malformed domain is
    quarantined into the receipt's malformed list and never
    adjudicates, signed or not."""
    problems = []
    if str_list(dom.get("products")) is None:
        problems.append("products must be a non-empty list of strings")
    classes = str_list(dom.get("claim_classes"))
    if classes is None:
        problems.append("claim_classes must be a non-empty list of strings")
    else:
        bad = sorted(set(classes) - vocab["ids"])
        if bad:
            problems.append("ungoverned claim classes: " + ", ".join(bad))
    if dom.get("polarity", "supporting") not in ("supporting", "exclusion"):
        problems.append("polarity must be supporting or exclusion")
    region = dom.get("region", "global")
    if region != "global" and not (isinstance(region, dict)
            and isinstance(region.get("bbox"), list) and len(region["bbox"]) == 4
            and all(isinstance(x, (int, float)) for x in region["bbox"])):
        problems.append("region must be global or {bbox: [latmin, latmax, lonmin, lonmax]}")
    period = dom.get("period", "any")
    if period != "any" and not (isinstance(period, dict)
            and isinstance(period.get("start"), str) and isinstance(period.get("end"), str)):
        problems.append("period must be any or {start, end} strings")
    return problems


def class_covered(declared: str, domain_classes: list, vocab: dict) -> bool:
    if declared in domain_classes:
        return True
    return any(u in domain_classes for u in vocab["umbrella_of"].get(declared, ()))


def product_match(declared: str, patterns: list) -> bool:
    import fnmatch
    return any(fnmatch.fnmatch(declared, pat) for pat in patterns)


def bbox_contains(outer, inner) -> bool:
    return (outer[0] <= inner[0] and inner[1] <= outer[1]
            and outer[2] <= inner[2] and inner[3] <= outer[3])


def bbox_intersects(a, b) -> bool:
    return not (a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2])


def period_key(s: str) -> str:
    return s  # YYYY-MM strings compare lexically


def period_contains(outer, inner) -> bool:
    return outer["start"] <= inner["start"] and inner["end"] <= outer["end"]


def period_intersects(a, b) -> bool:
    return not (a["end"] < b["start"] or b["end"] < a["start"])


def scope_hits(dom: dict, decl: dict, mode: str) -> bool:
    """mode 'contain' for supporting domains, 'intersect' for exclusions."""
    if not product_match(decl["product"], dom.get("products", [])):
        return False
    region = dom.get("region", "global")
    if region != "global" and decl["region"] != "global":
        f = bbox_contains if mode == "contain" else bbox_intersects
        if not f(region["bbox"], decl["region"]["bbox"]):
            return False
    elif region != "global" and decl["region"] == "global":
        if mode == "contain":
            return False  # a bounded domain cannot contain a global claim
    period = dom.get("period", "any")
    if period != "any" and decl["period"] != "any":
        f = period_contains if mode == "contain" else period_intersects
        if not f(period, decl["period"]):
            return False
    elif period != "any" and decl["period"] == "any":
        if mode == "contain":
            return False
    return True


def attest(roots, decl, vocab) -> dict:
    if decl["provenance"] != HAND:
        return {"error": f"declaration provenance '{decl['provenance']}' is not "
                         "available: capsule derivation is not built yet, and "
                         "this attester refuses to imply assurance that does not exist"}
    governing, advisory, malformed = [], [], []
    verdict = "UNADJUDICATED"
    for path, fm in load_domains(roots):
        dom = fm["domain"]
        problems = validate_domain(dom, vocab)
        if problems:
            # R5: never read a malformed domain through str semantics;
            # quarantine it visibly and adjudicate nothing from it.
            malformed.append({"concept": path, "problems": problems,
                              "signed": is_signed(fm)})
            continue
        if not class_covered(decl["claim"], dom["claim_classes"], vocab):
            continue
        polarity = dom.get("polarity", "supporting")
        mode = "intersect" if polarity == "exclusion" else "contain"
        if not scope_hits(dom, decl, mode):
            continue
        entry = {"concept": path, "polarity": polarity, "title": fm.get("title", "")}
        if is_signed(fm):
            governing.append(entry)
        else:
            advisory.append(entry)
    if any(g["polarity"] == "exclusion" for g in governing):
        verdict = "OUT"
        governing = [g for g in governing if g["polarity"] == "exclusion"]
    elif any(g["polarity"] == "supporting" for g in governing):
        verdict = "IN"
        governing = [g for g in governing if g["polarity"] == "supporting"]
    else:
        governing = []
    return {
        "run_id": str(uuid.uuid4())[:8],
        "verdict": verdict,
        "declaration": {k: decl[k] for k in ("product", "claim", "region", "period")},
        "declaration_provenance": decl["provenance"],
        "governing_concepts": governing,
        "advisory_unsigned": advisory,
        "malformed_domains": malformed,
        "vocabulary_sha256": decl["vocab_sha"],
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def parse_region(s: str):
    if s == "global":
        return "global"
    a = [float(x) for x in s.split(",")]
    assert len(a) == 4, "region is latmin,latmax,lonmin,lonmax or global"
    return {"bbox": a}


def parse_period(s: str):
    if s == "any":
        return "any"
    start, end = s.split(":")
    return {"start": start, "end": end}


def selftest() -> int:
    import tempfile
    ok = True
    vocab = {"ids": {"statistics", "trend", "budgets", "extremes", "mean-state"},
             "umbrella_of": {"trend": {"statistics"}}}
    with tempfile.TemporaryDirectory() as td:
        b = Path(td)
        (b / "excl.md").write_text(
            "---\ntype: validity-domain\ntitle: no budgets on interpolated\n"
            "verified: { by: human:Alice, at: 2026-01-01T00:00:00Z }\n"
            "domain:\n  products: ['*_05DEG_*']\n  claim_classes: [budgets]\n"
            "  polarity: exclusion\n---\nbody\n")
        (b / "supp.md").write_text(
            "---\ntype: validity-domain\ntitle: basin statistics ok\n"
            "verified:\n  - { by: human:Alice, at: 2026-01-01T00:00:00Z }\n"
            "domain:\n  products: ['ECCO_L4_SSH_LLC0090GRID_MONTHLY_*']\n"
            "  claim_classes: [statistics]\n  polarity: supporting\n"
            "  region: { bbox: [-90, 90, -180, 180] }\n"
            "  period: { start: '1992-01', end: '2017-12' }\n---\nbody\n")
        (b / "draft.md").write_text(
            "---\ntype: validity-domain\ntitle: draft extremes domain\n"
            "status: draft\n"
            "domain:\n  products: ['ECCO_*']\n  claim_classes: [extremes]\n"
            "  polarity: supporting\n---\nbody\n")
        def decl(product, claim, region="global", period="any"):
            return {"product": product, "claim": claim,
                    "region": parse_region(region), "period": parse_period(period),
                    "provenance": HAND, "vocab_sha": "t"}
        r = attest([b], decl("ECCO_L4_OCEAN_VEL_05DEG_MONTHLY_V4R4", "budgets"), vocab)
        ok = ok and r["verdict"] == "OUT" and len(r["governing_concepts"]) == 1
        r = attest([b], decl("ECCO_L4_SSH_LLC0090GRID_MONTHLY_V4R4", "trend",
                             "35,45,-75,-65", "2010-01:2010-12"), vocab)
        ok = ok and r["verdict"] == "IN"          # umbrella subsumption, contained
        r = attest([b], decl("ECCO_L4_SSH_LLC0090GRID_MONTHLY_V4R4", "trend",
                             "35,45,-75,-65", "2010-01:2018-06"), vocab)
        ok = ok and r["verdict"] == "UNADJUDICATED"  # period exceeds domain
        r = attest([b], decl("ECCO_L4_THETA_LLC0090GRID_MONTHLY_V4R4", "extremes"), vocab)
        ok = ok and r["verdict"] == "UNADJUDICATED" and len(r["advisory_unsigned"]) == 1
        r = attest([b], dict(decl("X", "trend"), provenance="capsule-derived"), vocab)
        ok = ok and "error" in r                   # refused tier
        # PR 5 round 1, F1: a SIGNED domain with scalar claim_classes
        # must never adjudicate by substring.
        (b / "f1.md").write_text(
            "---\ntype: validity-domain\ntitle: scalar classes\n"
            "verified: { by: human:Mallory, at: 2026-01-01T00:00:00Z }\n"
            "domain:\n  products: ['ECCO_TEST_*']\n"
            "  claim_classes: trends-of-the-basin\n"
            "  polarity: supporting\n---\nbody\n")
        r = attest([b], decl("ECCO_TEST_MONTHLY", "trend"), vocab)
        ok = ok and r["verdict"] == "UNADJUDICATED"
        ok = ok and any("claim_classes must be" in p for m in r["malformed_domains"]
                        for p in m["problems"])
        # PR 5 round 1, F2: a SIGNED domain with scalar products must
        # never become match-all via character iteration.
        (b / "f2.md").write_text(
            "---\ntype: validity-domain\ntitle: scalar products\n"
            "verified: { by: human:Mallory, at: 2026-01-01T00:00:00Z }\n"
            "domain:\n  products: 'ECCO_TEST_*'\n"
            "  claim_classes: [mean-state]\n"
            "  polarity: supporting\n---\nbody\n")
        r = attest([b], decl("COMPLETELY_UNRELATED_PRODUCT", "mean-state"), vocab)
        ok = ok and r["verdict"] == "UNADJUDICATED"
        # And a signed domain naming an ungoverned class in a proper
        # list is quarantined too (the invariant is now two-sided).
        (b / "f3.md").write_text(
            "---\ntype: validity-domain\ntitle: ungoverned member\n"
            "verified: { by: human:Mallory, at: 2026-01-01T00:00:00Z }\n"
            "domain:\n  products: ['ECCO_TEST_*']\n"
            "  claim_classes: [vibes]\n  polarity: exclusion\n---\nbody\n")
        r = attest([b], decl("ECCO_TEST_MONTHLY", "trend"), vocab)
        ok = ok and r["verdict"] == "UNADJUDICATED" and len(r["malformed_domains"]) == 3
        r2 = attest([b], decl("ECCO_L4_OCEAN_VEL_05DEG_MONTHLY_V4R4", "budgets"), vocab)
        ok = ok and {k: r2[k] for k in ("verdict", "governing_concepts")} \
                 == {"verdict": "OUT", "governing_concepts": r2["governing_concepts"]}
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roots", nargs="*", type=Path)
    ap.add_argument("--product")
    ap.add_argument("--claim")
    ap.add_argument("--region", default="global")
    ap.add_argument("--period", default="any")
    ap.add_argument("--provenance", default=HAND)
    ap.add_argument("--classes", type=Path,
                    default=Path(__file__).parent.parent / "data" / "claim-classes.yaml",
                    help="the governed vocabulary (data/claim-classes.yaml)")
    ap.add_argument("--receipt", type=Path, default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if not (args.roots and args.product and args.claim):
        ap.error("bundle roots, --product, and --claim required (or --selftest)")
    vocab = load_classes(args.classes)
    if args.claim not in vocab["ids"]:
        print(f"REFUSED: claim class '{args.claim}' is not in the governed "
              f"vocabulary ({', '.join(sorted(vocab['ids']))}); free invention "
              "silences the attester by design (extend by steward PR).")
        return 1
    decl = {"product": args.product, "claim": args.claim,
            "region": parse_region(args.region), "period": parse_period(args.period),
            "provenance": args.provenance,
            "vocab_sha": hashlib.sha256(args.classes.read_bytes()).hexdigest()}
    r = attest(args.roots, decl, vocab)
    if "error" in r:
        print("REFUSED:", r["error"])
        return 1
    out = json.dumps(r, indent=2)
    if args.receipt:
        args.receipt.write_text(out + "\n", encoding="utf-8")
    print(f"verdict: {r['verdict']}")
    for g in r["governing_concepts"]:
        print(f"  governing: {g['concept']} ({g['polarity']}: {g['title']})")
    for a in r["advisory_unsigned"]:
        print(f"  advisory (unsigned, does not adjudicate): {a['concept']}")
    for m in r["malformed_domains"]:
        tag = " [SIGNED]" if m.get("signed") else ""
        print(f"  malformed (quarantined, adjudicates nothing){tag}: "
              f"{m['concept']} ({'; '.join(m['problems'])})")
    if args.receipt:
        print(f"receipt -> {args.receipt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
