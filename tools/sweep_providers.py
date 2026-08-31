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

Usage:
  sweep_providers.py data/requirements-seed.yaml --providers POCLOUD [NSIDC_CPRD ...]
      [--page-size 200] [--max-pages 5] [--out-dir sweeps/]
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
    return {
        "short_name": umm.get("ShortName"),
        "doi": (umm.get("DOI") or {}).get("DOI"),
        "spatial": umm.get("SpatialExtent"),
        "temporal": umm.get("TemporalExtents"),
        "abstract": umm.get("Abstract"),
        "related_urls": umm.get("RelatedUrls"),
    }


SELFTEST_ENTRIES = [
    {"short_name": "GOOD", "doi": "10.5067/X", "spatial": {"HorizontalSpatialDomain": {}},
     "temporal": [{"RangeDateTimes": []}], "abstract": "fine", "related_urls": [{"URL": "x"}]},
    {"short_name": "NO_DOI", "spatial": {"HorizontalSpatialDomain": {}},
     "temporal": [{"RangeDateTimes": []}], "abstract": "fine", "related_urls": [{"URL": "x"}]},
    {"short_name": "BARE", "abstract": ""},
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
    for e in entries:
        for rid, r in rules.items():
            if r["fn"](e):
                out[rid]["pass"] += 1
            else:
                out[rid]["fail"].append(e.get("short_name") or e.get("id", "?"))
    return out


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
    ap.add_argument("--providers", nargs="+", default=["POCLOUD"])
    ap.add_argument("--page-size", type=int, default=200)
    ap.add_argument("--max-pages", type=int, default=5)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    rules = load_rules(args.rules_seed)
    if not rules:
        print("no cmr-structural rules in the seed", file=sys.stderr)
        return 2

    if args.selftest:
        t = tally(SELFTEST_ENTRIES, rules)
        ok = (rules["req-doi"]["class"] == "SHOULD*"
              and t["req-doi"]["pass"] == 1 and "NO_DOI" in t["req-doi"]["fail"]
              and t["req-temporal-extent"]["pass"] == 2
              and t["req-abstract"]["pass"] == 2)
        report("SELFTEST", len(SELFTEST_ENTRIES), t, None)
        print("selftest:", "PASS" if ok else "FAIL")
        return 0 if ok else 1

    for provider in args.providers:
        entries = fetch_provider(provider, args.page_size, args.max_pages)
        report(provider, len(entries), tally(entries, rules), args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
