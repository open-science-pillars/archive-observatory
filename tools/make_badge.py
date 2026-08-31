#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10,<3.12"
# dependencies = ["pyQuARC @ git+https://github.com/NASA-IMPACT/pyQuARC@v1.3.0"]
# ///
# The dependency mirrors quarc_attest.py's pin exactly: a full attest
# (ruleset hash, revision binding) needs the pinned pyQuARC in the
# environment, and the badge path never runs a lesser attest.
"""Emit a shields.io endpoint badge for one attested pyQuARC receipt.

The kit-2 pattern over quarc receipts, bound by register R1 and R6:
- R1: refuses unless the provider's written opt-in exists at
  optin/<PROVIDER>.md; badges are strictly opt-in.
- R6: refuses unless a FULL attest of the receipt passes in this
  environment (pinned version, ruleset hash, revision binding with the
  hardened fail-closed A4/A5; --skip-env-checks is never accepted
  here). The badge publishes alongside a copy of its receipt.

Usage:
  make_badge.py receipt.json --provider POCLOUD [--out badges/]
  make_badge.py --selftest
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import quarc_attest  # noqa: E402


def emit(receipt_path: Path, provider: str, out_dir: Path) -> int:
    optin = Path("optin") / f"{provider}.md"
    if not optin.exists():
        print(f"REFUSED: no written opt-in recorded at {optin} "
              "(publication policy, register R1); no badge is emitted.")
        return 1
    r = json.loads(receipt_path.read_text(encoding="utf-8"))
    # Checked before attestation so the refusal names the specific
    # reason: a badge binds to a published collection revision, which a
    # file-based run does not have (register R6).
    if not any(rec.get("concept_id") for rec in (r.get("records") or [])):
        print("REFUSED: no registered records in this receipt (register R6); "
              "a badge binds to a published collection revision, so a "
              "file-based run cannot produce one.")
        return 1
    if quarc_attest.attest(receipt_path, max_errors=0,
                           skip_env_checks=False) != 0:
        print("REFUSED: full attest did not PASS (register R6); "
              "no badge is emitted.")
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    for rec in r.get("records", []):
        cid = rec.get("concept_id")
        if not cid:
            continue
        badge = {
            "schemaVersion": 1,
            "label": "pyQuARC attested",
            "message": (f"errors 0, rev {rec.get('revision_id')}, "
                        f"run {r.get('run_id')}"),
            "color": "brightgreen",
        }
        (out_dir / f"{cid}.json").write_text(
            json.dumps(badge, indent=2) + "\n", encoding="utf-8")
        shutil.copy(receipt_path, out_dir / f"{cid}-receipt.json")
        print(f"badge emitted: {out_dir / (cid + '.json')} "
              "(receipt copied alongside)")
    return 0


def selftest() -> int:
    import os
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        receipt = tdp / "r.json"
        receipt.write_text(json.dumps({
            "run_id": "t1", "pyquarc_version": quarc_attest.PINNED_VERSION,
            "ruleset_sha256": "deadbeef",
            "records": [{"concept_id": "C1-X", "revision_id": "3"}],
            "counts": {"error": 0, "warning": 0, "info": 0}}))
        cwd = os.getcwd()
        os.chdir(td)
        try:
            ok = ok and emit(receipt, "TESTPROV", tdp / "badges") == 1
            (tdp / "optin").mkdir()
            (tdp / "optin" / "TESTPROV.md").write_text("written opt-in\n")
            ok = ok and emit(receipt, "TESTPROV", tdp / "badges") == 1
            ok = ok and not (tdp / "badges").exists()
            # A file-based receipt is refused before any badge work,
            # never a silent success with an empty directory (R6).
            filebased = tdp / "fb.json"
            filebased.write_text(json.dumps({
                "run_id": "t2", "pyquarc_version": quarc_attest.PINNED_VERSION,
                "ruleset_sha256": "deadbeef",
                "records": [{"file": "draft.json"}],
                "counts": {"error": 0, "warning": 0, "info": 0}}))
            ok = ok and emit(filebased, "TESTPROV", tdp / "badges2") == 1
            ok = ok and not (tdp / "badges2").exists()
        finally:
            os.chdir(cwd)
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("receipt", type=Path, nargs="?")
    ap.add_argument("--provider", default=None)
    ap.add_argument("--out", type=Path, default=Path("badges"))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if not args.receipt or not args.provider:
        ap.error("receipt and --provider are required (or --selftest)")
    return emit(args.receipt, args.provider, args.out)


if __name__ == "__main__":
    sys.exit(main())
