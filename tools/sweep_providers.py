#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""sweep_providers: cross-archive structural sweep of public CMR
collection metadata, against the MUST/SHOULD rules the requirements
bundle declares as cmr-structural.

Reads the rules seed, sweeps each named provider's collections (public
CMR, no credentials, Client-Id set, throttled), tallies per-provider
pass rates per rule, and emits the aggregate report the publication
policy allows to be public plus a per-provider detail file the policy
routes privately. Sweeps are throttled by construction: Client-Id on every request,
one second between pages, bounded pages, monthly cadence (register
R4). An incremental mode keyed on revision dates is future work,
deliberately not claimed as present behavior.

Structural rules this sweeper can check from a CMR search result alone:
doi-present, spatial-extent-present, temporal-extent-present,
abstract-present, related-urls-present. The search endpoint is
collections.umm_json, not collections.json: the .json flavor omits the
DOI field entirely (observed 2026-08-30, same CMR quirk the citation
plumbing hit), so a doi-present check against it fails every collection. Everything deeper (vocabulary
validity, link resolution, granule consistency) belongs to the pyQuARC
harness, not here.

Three ways to name what gets checked, so a producer can check their own
metadata before it is anyone else's problem:
  --files    local UMM-C JSON on disk; nothing needs to be registered
  --short-names  a subset of registered collections, by ShortName
  --providers    a whole provider's registered collections

Usage:
  sweep_providers.py data/requirements-seed.yaml --files draft.json [more.json ...]
  sweep_providers.py data/requirements-seed.yaml --short-names ECCO_L4_SSH_LLC0090GRID_MONTHLY_V4R4
  sweep_providers.py data/requirements-seed.yaml --providers POCLOUD [NSIDC_CPRD ...]
      [--page-size 200] [--max-pages 5] [--out-dir sweeps/] [--fail-on-must]
  sweep_providers.py data/requirements-seed.yaml --selftest
"""

import argparse
import datetime
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml required", file=sys.stderr)
    sys.exit(2)

CMR = "https://cmr.earthdata.nasa.gov/search/collections.umm_json"
CLIENT_ID = "osp-archive-observatory"

STRUCTURAL = {
    # Entries are flattened from umm_json items by fetch_provider.
    "doi-present": lambda e: bool(e.get("doi")),
    "spatial-extent-present": lambda e: bool(e.get("spatial")),
    "temporal-extent-present": lambda e: bool(e.get("temporal")),
    "abstract-present": lambda e: bool((e.get("abstract") or "").strip()),
    "related-urls-present": lambda e: bool(e.get("related_urls")),
}


def flatten_umm(item: dict) -> dict:
    """One flat entry per umm_json item; a DOI object whose DOI key is
    absent (MissingReason form) correctly reads as no DOI."""
    umm = item.get("umm", {}) or {}
    doi_obj = umm.get("DOI")
    if isinstance(doi_obj, dict) and doi_obj.get("DOI"):
        doi_state = "registered"
    elif isinstance(doi_obj, dict) and doi_obj.get("MissingReason"):
        doi_state = "missing-reason declared"
    else:
        doi_state = "malformed or absent"
    return {
        "doi_state": doi_state,
        "short_name": umm.get("ShortName"),
        "doi": (umm.get("DOI") or {}).get("DOI"),
        "spatial": umm.get("SpatialExtent"),
        "temporal": umm.get("TemporalExtents"),
        "abstract": umm.get("Abstract"),
        "related_urls": umm.get("RelatedUrls"),
    }


SELFTEST_ENTRIES = [
    {"short_name": "GOOD", "doi": "10.5067/X", "doi_state": "registered", "spatial": {"HorizontalSpatialDomain": {}},
     "temporal": [{"RangeDateTimes": []}], "abstract": "fine", "related_urls": [{"URL": "x"}]},
    {"short_name": "NO_DOI", "doi_state": "missing-reason declared", "spatial": {"HorizontalSpatialDomain": {}},
     "temporal": [{"RangeDateTimes": []}], "abstract": "fine", "related_urls": [{"URL": "x"}]},
    {"short_name": "BARE", "doi_state": "malformed or absent", "abstract": ""},
]


def load_rules(path: Path) -> dict:
    seed = yaml.safe_load(path.read_text(encoding="utf-8"))
    rules = {}
    for r in seed.get("rules", []):
        if r.get("check", {}).get("binding") == "cmr-structural":
            cid = r["check"]["id"]
            if cid not in STRUCTURAL:
                print(f"WARN: rule {r['id']} binds unknown structural check {cid}",
                      file=sys.stderr)
                continue
            cls = r["class"]
            section = str((r.get("source") or {}).get("section", ""))
            if cls == "MUST" and section != "verified":
                # Register R2, enforced not intended: an unverified
                # source citation can never surface as MUST.
                cls = "SHOULD*"
            rules[r["id"]] = {"fn": STRUCTURAL[cid], "class": cls}
    return rules


def read_local(paths: list) -> list:
    """Local UMM-C JSON, nothing registered anywhere. Accepts a bare UMM
    record, a {"umm": ...} item, or a search-result envelope with
    "items"; a file that is none of those is reported, never guessed at."""
    entries, problems = [], []
    for path in paths:
        try:
            doc = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{path}: unreadable ({exc.__class__.__name__})")
            continue
        if isinstance(doc, dict) and isinstance(doc.get("items"), list):
            items = doc["items"]
        elif isinstance(doc, dict) and isinstance(doc.get("umm"), dict):
            items = [doc]
        elif isinstance(doc, dict) and "ShortName" in doc:
            items = [{"umm": doc}]
        else:
            problems.append(f"{path}: not a UMM-C record, a umm item, or a "
                            "search envelope")
            continue
        for item in items:
            e = flatten_umm(item)
            e["source_file"] = str(path)
            e["short_name"] = e.get("short_name") or f"(no ShortName in {path})"
            entries.append(e)
    for problem in problems:
        print(f"  skipped: {problem}", file=sys.stderr)
    return entries


def fetch_short_names(short_names: list) -> list:
    """A named subset of registered collections. One request per name so
    a typo shows up as its own miss rather than silently shrinking the
    set."""
    entries = []
    for name in short_names:
        params = {"short_name": name, "page_size": 50}
        req = urllib.request.Request(CMR + "?" + urllib.parse.urlencode(params),
                                     headers={"Client-Id": CLIENT_ID,
                                              "User-Agent": CLIENT_ID})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.loads(r.read()).get("items", []) or []
        if not batch:
            print(f"  no registered collection matches ShortName {name}",
                  file=sys.stderr)
        entries += [flatten_umm(it) for it in batch]
        time.sleep(1)  # register R4: polite by construction
    return entries


def fetch_provider(provider: str, page_size: int, max_pages: int) -> list:
    entries = []
    for page in range(1, max_pages + 1):
        params = {"provider": provider, "page_size": page_size, "page_num": page}
        req = urllib.request.Request(CMR + "?" + urllib.parse.urlencode(params),
                                     headers={"Client-Id": CLIENT_ID,
                                              "User-Agent": CLIENT_ID})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.loads(r.read()).get("items", []) or []
        entries += [flatten_umm(it) for it in batch]
        if len(batch) < page_size:
            break
        time.sleep(1)  # register R4: polite by construction
    return entries


def tally(entries: list, rules: dict) -> dict:
    out = {rid: {"pass": 0, "fail": [], "class": r["class"]} for rid, r in rules.items()}
    if "req-doi" in out:
        states = {}
        for e in entries:
            s = e.get("doi_state", "unknown")
            states[s] = states.get(s, 0) + 1
        out["req-doi"]["states"] = states
    for e in entries:
        for rid, r in rules.items():
            if r["fn"](e):
                out[rid]["pass"] += 1
            else:
                out[rid]["fail"].append(e.get("short_name") or e.get("id", "?"))
    return out


def must_failures(tallies: dict) -> list:
    """Rule ids of MUST-class rules with at least one failing record.
    A MUST demoted to SHOULD* for want of a verified citation (register
    R2) is deliberately not a build breaker."""
    return sorted(rid for rid, t in tallies.items()
                  if t["class"] == "MUST" and t["fail"])


def report(provider: str, n: int, tallies: dict, out_dir: Path | None):
    today = datetime.date.today().isoformat()
    agg = [f"{provider}: {n} collections swept {today}"]
    detail = [f"# {provider} detail (private per publication policy) {today}", "",
              "Produced by Open Science Pillars, a community project; not a "
              "NASA, JPL, or PO.DAAC product. Delivered privately per the "
              "publication policy.", ""]
    for rid, t in sorted(tallies.items()):
        pct = (100.0 * t["pass"] / n) if n else 0.0
        agg.append(f"  {rid:<26} [{t['class']:<6}] {t['pass']}/{n} ({pct:.1f} percent)")
        if t.get("states"):
            agg.append("      states: " + ", ".join(
                f"{k} {v}" for k, v in sorted(t["states"].items())))
        if t["fail"]:
            detail.append(f"## {rid} ({t['class']}): {len(t['fail'])} failing")
            detail += [f"- `{sn}`" for sn in sorted(t["fail"])[:200]]
            detail.append("")
    if any(v["class"] == "SHOULD*" for v in tallies.values()):
        agg.append("  * MUST candidate held at SHOULD until its source"
                   " citation is verified (register R2)")
    agg.append("  Produced by Open Science Pillars, a community project;"
               " not a NASA, JPL, or PO.DAAC product.")
    print("\n".join(agg))
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{provider}-{today}-aggregate.txt").write_text(
            "\n".join(agg) + "\n", encoding="utf-8")
        (out_dir / f"{provider}-{today}-detail-PRIVATE.md").write_text(
            "\n".join(detail) + "\n", encoding="utf-8")
        print(f"wrote aggregate (publishable) and detail (private) -> {out_dir}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rules_seed", type=Path)
    ap.add_argument("--files", nargs="+", default=None,
                    help="local UMM-C JSON files; nothing needs to be registered")
    ap.add_argument("--short-names", nargs="+", default=None,
                    help="a named subset of registered collections")
    ap.add_argument("--providers", nargs="+", default=None,
                    help="whole registered providers (default POCLOUD when "
                         "no other selector is given)")
    ap.add_argument("--page-size", type=int, default=200)
    ap.add_argument("--max-pages", type=int, default=5)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--fail-on-must", action="store_true",
                    help="exit 1 when any MUST-class rule has a failing "
                         "record; for a producer's own CI")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    rules = load_rules(args.rules_seed)
    if not rules:
        print("no cmr-structural rules in the seed", file=sys.stderr)
        return 2

    if args.selftest:
        t = tally(SELFTEST_ENTRIES, rules)
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tf:
            tf.write("rules:\n  - id: r-gate\n    class: MUST\n"
                     "    statement: synthetic\n"
                     "    source: {doc: pending, section: not-yet-verified}\n"
                     "    check: {binding: cmr-structural, id: doi-present}\n")
        gate = load_rules(Path(tf.name))
        Path(tf.name).unlink()  # red-team tidiness note, PR 2 verdict
        ok = (t["req-doi"].get("states") == {"registered": 1,
              "missing-reason declared": 1, "malformed or absent": 1}
              and gate["r-gate"]["class"] == "SHOULD*"
              and rules["req-doi"]["class"] == "SHOULD"
              and t["req-doi"]["pass"] == 1 and "NO_DOI" in t["req-doi"]["fail"]
              and t["req-temporal-extent"]["pass"] == 2
              and t["req-abstract"]["pass"] == 2)
        # Local-file reading and the CI exit lever, exercised here so a
        # producer's two entry points are covered by the same gate.
        import tempfile as _tf
        with _tf.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "bare.json").write_text(json.dumps(
                {"ShortName": "BARE_UMM", "Abstract": "x",
                 "DOI": {"DOI": "10.5067/Y"}}))
            (tdp / "item.json").write_text(json.dumps(
                {"umm": {"ShortName": "WRAPPED", "Abstract": "y"}}))
            (tdp / "envelope.json").write_text(json.dumps(
                {"items": [{"umm": {"ShortName": "ENV1", "Abstract": "z"}},
                           {"umm": {"ShortName": "ENV2", "Abstract": "w"}}]}))
            (tdp / "junk.json").write_text('{"not": "a record"}')
            local = read_local([tdp / "bare.json", tdp / "item.json",
                                tdp / "envelope.json", tdp / "junk.json",
                                tdp / "missing.json"])
            ok = ok and [e["short_name"] for e in local] == [
                "BARE_UMM", "WRAPPED", "ENV1", "ENV2"]
            ok = ok and all(e.get("source_file") for e in local)
            lt = tally(local, rules)
            # Every local record lacks spatial and temporal extents, so
            # both MUST rules fail and the CI lever must trip.
            ok = ok and must_failures(lt) == ["req-spatial-extent",
                                              "req-temporal-extent"]
            ok = ok and must_failures(tally([SELFTEST_ENTRIES[0]], rules)) == []
        report("SELFTEST", len(SELFTEST_ENTRIES), t, None)
        print("selftest:", "PASS" if ok else "FAIL")
        return 0 if ok else 1

    selectors = [bool(args.files), bool(args.short_names), bool(args.providers)]
    if sum(selectors) > 1:
        ap.error("choose one of --files, --short-names, or --providers")

    failed_must = []
    if args.files:
        entries = read_local(args.files)
        if not entries:
            print("no readable UMM-C records in the named files", file=sys.stderr)
            return 2
        tallies = tally(entries, rules)
        report("LOCAL", len(entries), tallies, args.out_dir)
        failed_must = must_failures(tallies)
    elif args.short_names:
        entries = fetch_short_names(args.short_names)
        if not entries:
            print("no registered collections matched", file=sys.stderr)
            return 2
        tallies = tally(entries, rules)
        report("SUBSET", len(entries), tallies, args.out_dir)
        failed_must = must_failures(tallies)
    else:
        for provider in args.providers or ["POCLOUD"]:
            entries = fetch_provider(provider, args.page_size, args.max_pages)
            tallies = tally(entries, rules)
            report(provider, len(entries), tallies, args.out_dir)
            failed_must += must_failures(tallies)

    if args.fail_on_must and failed_must:
        print("FAIL: MUST-class rules with failing records: "
              + ", ".join(sorted(set(failed_must))))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
