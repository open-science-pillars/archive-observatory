#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10,<3.12"
# dependencies = ["pyQuARC @ git+https://github.com/NASA-IMPACT/pyQuARC@v1.3.0"]
# ///
"""quarc_attest: run pyQuARC as a receipted check, or attest a receipt.

Register R3 made concrete: pyQuARC installs from GitHub (not PyPI), its
dependency pins are dated (urllib3/six breakage observed on Python 3.13),
and its rules change across versions. So this harness pins the git tag
and a compatible Python in its own PEP 723 block, and every run receipt
records the pyQuARC version plus a sha256 over the effective ruleset
files (schemas/checks.json and any overrides), so a verdict is
reproducible or it is nothing.

run mode:    execute pyQuARC on CMR concept ids (network) or a local
             record file (offline), write a receipt JSON:
             { run_id, pyquarc_version, ruleset_sha256, records:
               [{concept_id|file, revision_id?}], counts: {error, warning,
               info}, generated_at }
attest mode: verify a receipt: pyQuARC version matches the pin, ruleset
             hash matches this environment's effective rules, and error
             count is at or below --max-errors. Deterministic, no LLM
             (register R5). Exit 0 PASS, 1 FAIL.
selftest:    exercise receipt and attest logic on a synthetic receipt,
             no network and no pyQuARC import needed.

Usage:
  quarc_attest.py run --concept-ids C1990404799-POCLOUD [--receipt r.json]
  quarc_attest.py run --file record.json --format umm-c [--receipt r.json]
  quarc_attest.py attest r.json --max-errors 0
  quarc_attest.py --selftest
"""

import argparse
import datetime
import hashlib
import json
import sys
import uuid
from pathlib import Path

# Register R3 event, observed 2026-08-30: the pinned git tag v1.3.0
# ships version.txt reading 1.2.8 (upstream never bumped the file at
# the tag). The PEP 723 pin on the tag is the code identity; this
# constant pins what that environment self-reports, so A1 stays a
# meaningful drift check. Upstream issue is the Session 4 loop.
PINNED_VERSION = "1.2.8"


def ruleset_sha() -> str:
    import pyQuARC
    base = Path(pyQuARC.__file__).parent / "schemas"
    h = hashlib.sha256()
    for name in ["checks.json", "checks_override.json", "rule_mapping.json",
                 "rules_override.json"]:
        p = base / name
        if p.exists():
            h.update(name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def pyquarc_version() -> str:
    import pyQuARC
    vt = Path(pyQuARC.__file__).parent / "version.txt"
    return vt.read_text().strip() if vt.exists() else "unknown"


def current_revision(concept_id: str):
    """Current CMR revision id for a collection, via public search
    (Client-Id, no credentials). None on any failure: the attester
    treats an unreachable revision as unverifiable, not as a match."""
    import urllib.request
    url = ("https://cmr.earthdata.nasa.gov/search/collections.umm_json"
           "?concept_id=" + concept_id)
    req = urllib.request.Request(url, headers={
        "Client-Id": "osp-archive-observatory",
        "User-Agent": "osp-archive-observatory"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            items = json.loads(r.read()).get("items", [])
        return str(items[0]["meta"]["revision-id"]) if items else None
    except Exception:
        return None


def revision_check(records, fetch=None) -> dict:
    """Register R6, hardened per the PR 1 round 2 closest call: a
    record with a concept id whose current revision cannot be verified
    (no revision_id recorded, or CMR unreachable) is UNVERIFIABLE and
    fails closed in a full attest; it is never silently skipped.
    File-based records carry no concept id and have nothing to bind."""
    fetch = fetch or current_revision
    out = {"mismatched": [], "unverifiable": []}
    for rec in records or []:
        cid, rev = rec.get("concept_id"), rec.get("revision_id")
        if not cid:
            continue
        if rev is None:
            out["unverifiable"].append(f"{cid}: no revision_id recorded")
            continue
        now = fetch(cid)
        if now is None:
            out["unverifiable"].append(f"{cid}: current revision unreachable")
        elif str(now) != str(rev):
            out["mismatched"].append(f"{cid}: receipt revision {rev}, CMR now {now}")
    return out


def severity_counts(results) -> dict:
    """Structural counts only (register R5): pyQuARC results carry a
    valid flag per executed check, not severity strings, so the receipt
    counts failed checks as errors, alongside CMR ingest validation
    errors and harness errors. No serialized text is scanned; metadata
    content can never steer the count."""
    counts = {"error": 0, "warning": 0, "info": 0}
    for item in results or []:
        for field_checks in (item.get("errors") or {}).values():
            for res in (field_checks or {}).values():
                if isinstance(res, dict) and res.get("valid") is False:
                    counts["error"] += 1
        cmr = item.get("cmr_validation") or {}
        counts["error"] += len(cmr.get("errors") or [])
        counts["warning"] += len(cmr.get("warnings") or [])
        counts["error"] += len(item.get("pyquarc_errors") or [])
    return counts


def run(args) -> int:
    from pyQuARC import ARC
    # Register R3 workaround (recorded before working around, per the
    # session prompt): pyQuARC v1.3.0's package-import branch
    # (main.py else-clause) omits CONTENT_TYPE_MAP from its constants
    # import, so library use via concept ids raises NameError inside
    # _validate_with_cmr. Bind the name from its defining module; the
    # pinned tag stays pinned. Upstream issue is the Session 4 loop.
    import pyQuARC.main as _pqm
    from pyQuARC.code.constants import CONTENT_TYPE_MAP as _ctm
    if not hasattr(_pqm, "CONTENT_TYPE_MAP"):
        _pqm.CONTENT_TYPE_MAP = _ctm
    if args.concept_ids:
        arc = ARC(input_concept_ids=args.concept_ids)
        records = [{"concept_id": c, "revision_id": current_revision(c)}
                   for c in args.concept_ids]
    else:
        arc = ARC(file_path=str(args.file), metadata_format=args.format)
        records = [{"file": str(args.file)}]
    results = arc.validate()
    receipt = {
        "run_id": str(uuid.uuid4())[:8],
        "pyquarc_version": pyquarc_version(),
        "ruleset_sha256": ruleset_sha(),
        "records": records,
        "counts": severity_counts(results),
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if args.full_results:
        args.full_results.write_text(json.dumps(results, indent=2, default=str),
                                     encoding="utf-8")
    print(f"run {receipt['run_id']}: pyQuARC {receipt['pyquarc_version']}, "
          f"counts {receipt['counts']} -> {args.receipt}")
    return 0


def attest(receipt_path: Path, max_errors: int, skip_env_checks: bool) -> int:
    r = json.loads(receipt_path.read_text(encoding="utf-8"))
    if r.get("pyquarc_version") != PINNED_VERSION:
        print(f"FAIL A1: receipt pyQuARC {r.get('pyquarc_version')} "
              f"is not the pinned {PINNED_VERSION}")
        return 1
    if not skip_env_checks:
        env_sha = ruleset_sha()
        if r.get("ruleset_sha256") != env_sha:
            print(f"FAIL A2: ruleset hash {str(r.get('ruleset_sha256'))[:12]}... "
                  f"does not match this environment {env_sha[:12]}...")
            return 1
    errors = int((r.get("counts") or {}).get("error", 10**9))
    if errors > max_errors:
        print(f"FAIL A3: {errors} error-severity findings exceed {max_errors}")
        return 1
    if not skip_env_checks:
        rc = revision_check(r.get("records"))
        if rc["mismatched"]:
            print("FAIL A4: record revisions no longer match CMR "
                  "(register R6): " + "; ".join(rc["mismatched"]))
            return 1
        if rc["unverifiable"]:
            print("FAIL A5: record revisions unverifiable, failing "
                  "closed (register R6): " + "; ".join(rc["unverifiable"]))
            return 1
        print(f"PASS run {r.get('run_id', '?')}: pinned version, ruleset "
              f"and record revisions verified, errors {errors} <= {max_errors}")
    else:
        print(f"PASS run {r.get('run_id', '?')}: receipt internally "
              f"consistent (env and revision checks SKIPPED; never the "
              f"badge path), errors {errors} <= {max_errors}")
    return 0


def selftest() -> int:
    good = {"run_id": "t1", "pyquarc_version": PINNED_VERSION,
            "ruleset_sha256": "deadbeef", "records": [{"concept_id": "C1-X"}],
            "counts": {"error": 0, "warning": 3, "info": 5},
            "generated_at": "2026-08-29T00:00:00Z"}
    p = Path("/tmp/quarc_selftest_receipt.json")
    p.write_text(json.dumps(good), encoding="utf-8")
    ok = attest(p, 0, skip_env_checks=True) == 0
    bad = dict(good, pyquarc_version="1.2.0")
    p.write_text(json.dumps(bad), encoding="utf-8")
    ok = ok and attest(p, 0, skip_env_checks=True) == 1
    worse = dict(good, counts={"error": 4, "warning": 0, "info": 0})
    p.write_text(json.dumps(worse), encoding="utf-8")
    ok = ok and attest(p, 0, skip_env_checks=True) == 1
    crafted = [{"concept_id": "C1-X",
                "errors": {"Collection/Abstract": {
                    "a_check": {"valid": False, "message": ['abstract says "error" "error" "warning"']},
                    "b_check": {"valid": True, "message": ['fine, mentions "info"']}}},
                "cmr_validation": {"errors": [], "warnings": ["w1"]},
                "pyquarc_errors": []}]
    ok = ok and severity_counts(crafted) == {"error": 1, "warning": 1, "info": 0}
    rc = revision_check([{"concept_id": "C1-X", "revision_id": "3"}],
                        fetch=lambda cid: "5")
    ok = ok and rc["mismatched"] == ["C1-X: receipt revision 3, CMR now 5"]
    rc = revision_check([{"concept_id": "C1-X", "revision_id": "3"}],
                        fetch=lambda cid: "3")
    ok = ok and rc == {"mismatched": [], "unverifiable": []}
    rc = revision_check([{"concept_id": "C1-X", "revision_id": None}],
                        fetch=lambda cid: "3")
    ok = ok and rc["unverifiable"] == ["C1-X: no revision_id recorded"]
    rc = revision_check([{"concept_id": "C1-X", "revision_id": "3"}],
                        fetch=lambda cid: None)
    ok = ok and rc["unverifiable"] == ["C1-X: current revision unreachable"]
    ok = ok and revision_check([{"file": "x.json"}]) == {"mismatched": [], "unverifiable": []}
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    rp = sub.add_parser("run")
    rp.add_argument("--concept-ids", nargs="+", default=None)
    rp.add_argument("--file", type=Path, default=None)
    rp.add_argument("--format", default="umm-c")
    rp.add_argument("--receipt", type=Path, default=Path("quarc_receipt.json"))
    rp.add_argument("--full-results", type=Path, default=None)
    at = sub.add_parser("attest")
    at.add_argument("receipt", type=Path)
    at.add_argument("--max-errors", type=int, default=0)
    at.add_argument("--skip-env-checks", action="store_true",
                    help="attest the receipt's internal consistency only "
                         "(no pyQuARC import); CI convenience, never the badge path")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if args.cmd == "run":
        if not args.concept_ids and not args.file:
            print("run needs --concept-ids or --file", file=sys.stderr)
            return 2
        return run(args)
    if args.cmd == "attest":
        return attest(args.receipt, args.max_errors, args.skip_env_checks)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
