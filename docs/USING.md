# Using the observatory (the operator's guide)

For a data engineer who wants to go from clone to first receipt
without anyone in the room. Everything here runs against public CMR
with a Client-Id and no login of any kind; the only prerequisite is
uv (https://docs.astral.sh/uv/), and every tool carries its own
pinned dependencies in its PEP 723 header. Run every command from the
repository root.

## The four tools, in one look

| Tool | What it does | Credential-free |
|---|---|---|
| tools/sweep_providers.py | Structural checks against the rules seed, over local files, a named subset, or a whole provider | yes |
| tools/quarc_attest.py | pyQuARC run on collections, receipt with pinned identity, deterministic attestation | yes |
| tools/make_badge.py | Shields badge from an attested receipt; strictly opt-in | yes |
| tools/fitness_attest.py | Can-I-use-X-for-Y verdicts against signed validity domains | yes |

Selftests for all four run in CI on every push; run them yourself the
same way CI does:

    uv run tools/sweep_providers.py data/requirements-seed.yaml --selftest
    uv run tools/quarc_attest.py --selftest
    uv run tools/make_badge.py --selftest
    uv run tools/fitness_attest.py --selftest

## What has to be registered, and what does not

The short answer for a data producer: **you can check metadata that
exists only on your laptop.** Nothing has to be in CMR for the checks
themselves, and no step here needs credentials.

| What you have | Structural rules | pyQuARC deep checks | Badge |
|---|---|---|---|
| A draft record on disk, unpublished | yes, `--files` | yes, `run --file` | no, badges bind to a registered revision |
| One registered collection | yes, `--short-names` | yes, `run --concept-ids` | yes, with a written opt-in |
| Several of your collections | yes, `--short-names` | yes, several `--concept-ids` | yes, per collection |
| A whole provider | yes, `--providers` | yes, but sweep first and target what fails | yes, per collection |

One honest caveat on the deep checks: the local-file path and the
registered path are not identical. `run --file` checks the record you
hand it; `run --concept-ids` checks what CMR holds and additionally
runs CMR's own ingest validation. Running both against the same ECCO
collection on 2026-08-30 produced different error counts (12 from the
file, 9 from the registered record), so treat a pre-publication run as
a smoke test that finds real problems early, not as a prediction of
what the registered record will report.

## Use cases, in the order a producer meets them

**1. Check a draft before anyone else sees it.** Export the record you
are about to submit as UMM-C JSON (a bare UMM object, a `{"umm": ...}`
item, or a search-result envelope all work) and run both tools with no
network dependency beyond the pyQuARC install:

    uv run tools/sweep_providers.py data/requirements-seed.yaml \
        --files draft-collection.json
    uv run tools/quarc_attest.py run --file draft-collection.json \
        --format umm-c --receipt draft-receipt.json
    uv run tools/quarc_attest.py attest draft-receipt.json --max-errors 0

Several files at once are fine. A file that is not a UMM-C record is
named and skipped, never guessed at. Attesting a file-based receipt
says so plainly ("no registered records to revision-bind"), because
there is no published revision to bind to yet.

**2. Check one collection you just published.**

    uv run tools/sweep_providers.py data/requirements-seed.yaml \
        --short-names MY_COLLECTION_SHORTNAME
    uv run tools/quarc_attest.py run --concept-ids C1234567890-PROVIDER \
        --receipt r.json

A ShortName that matches nothing registered is reported as its own
miss rather than silently shrinking the set.

**3. Check the handful you maintain.** Pass several names; the sweep
requests one at a time, a second apart, and reports them together as
SUBSET.

    uv run tools/sweep_providers.py data/requirements-seed.yaml \
        --short-names COLLECTION_A COLLECTION_B COLLECTION_C

**4. Gate your own pipeline.** `--fail-on-must` exits 1 when any
MUST-class rule has a failing record, so a producer's CI can block a
submission on its own terms:

    uv run tools/sweep_providers.py data/requirements-seed.yaml \
        --files draft-collection.json --fail-on-must

A MUST candidate that is held at SHOULD* for want of a verified
citation (register R2) deliberately does not break your build; only
rules whose mandate is cited do.

Exit codes are distinct on purpose, so your pipeline can tell a
finding from a malfunction:

| Code | Meaning |
|---|---|
| 0 | The run completed; no MUST-class rule failed, or `--fail-on-must` was not passed |
| 1 | `--fail-on-must` was passed and a cited-mandate rule has a failing record: a finding about your metadata |
| 2 | The tool could not do its job (no readable records, no structural rules in the seed): a malfunction, not a finding |

A file that is not a UMM-C record is named on stderr and skipped
rather than crashing the run, so one bad export never masquerades as a
compliance failure.

**Where results land.** Only a whole-provider sweep writes an
aggregate marked publishable. `--files` and `--short-names` produce
per-collection results by construction, so both their files carry the
PRIVATE suffix and the scheduled workflow's publish step cannot pick
them up. Your own drafts are yours; nothing here publishes them, and
`sweeps/` is gitignored so a stray `git add` cannot either.

**5. Prove a fix worked.** Re-run the same command after the edit and
compare; every number the tools print is derived, and pyQuARC receipts
carry the ruleset hash, so two runs are comparable when their
`ruleset_sha256` matches.

**6. Ask whether a product supports a claim.** That is
tools/fitness_attest.py, further below; it answers from signed
validity domains in a knowledge bundle rather than from the metadata.

## Sweep a whole provider

    uv run tools/sweep_providers.py data/requirements-seed.yaml \
        --providers POCLOUD --out-dir sweeps/

The sweep pages politely through CMR collections.umm_json (Client-Id
header, one second between pages; the .json flavor omits the DOI
field entirely, which is why umm_json is the endpoint). It writes two
files. The aggregate (PROVIDER-DATE-aggregate.txt) shows per-rule pass
counts, the DOI state breakdown (registered, missing-reason declared,
malformed or absent, so a conformant declaration never reads as a
miss), a footnote when a MUST candidate is held at SHOULD pending its
citation, and the non-affiliation line. The detail file is suffixed
-PRIVATE and lists failing collections by name; it is delivered
privately per docs/publication-policy.md and never committed (the
.gitignore holds sweeps/ by construction; the scheduled workflow
force-adds only the aggregate, and only when a written opt-in exists
at optin/PROVIDER.md).

Rule classes come from data/requirements-seed.yaml: MUST means a
verified citation to an authoritative document; SHOULD means an
attributed practice. A MUST whose source section is not verified is
demoted to SHOULD* at load time; that gate is code, not convention.

## Run pyQuARC and attest the receipt

    uv run tools/quarc_attest.py run \
        --concept-ids C1991543732-POCLOUD --receipt r.json
    uv run tools/quarc_attest.py attest r.json --max-errors 0

The run installs pyQuARC from its pinned git tag (v1.3.0; the tag
self-reports 1.2.8 in version.txt, a documented upstream discrepancy)
and writes a receipt:

    {
      "run_id": "8eec9055",          one run, one id
      "pyquarc_version": "1.2.8",    what the pinned environment reports
      "ruleset_sha256": "fd00...",   hash of the effective ruleset files
      "records": [ { "concept_id": "...", "revision_id": "23" } ],
      "counts": { "error": 9, ... }, failed checks, counted structurally
      "generated_at": "..."
    }

Attestation is deterministic and fails closed: A1 rejects a receipt
from an unpinned version, A2 rejects a ruleset hash that does not
match this environment, A3 rejects error counts over the bound, A4
rejects records whose CMR revision has moved since the run, and A5
rejects records whose revision cannot be verified at all (none
recorded, or CMR unreachable). The --skip-env-checks flag exists for
CI convenience on synthetic receipts and is never accepted on the
badge path.

## Emit a badge (opt-in only)

    uv run tools/make_badge.py r.json --provider POCLOUD

Two refusals guard this, both proven by the selftest: no badge
without a written opt-in at optin/POCLOUD.md, and no badge without a
FULL attest PASS of the receipt in this environment. A badge that
emits is a shields.io endpoint JSON named by collection concept id,
with the receipt copied alongside so anyone can re-attest what the
badge claims.

## Ask can-I-use-X-for-Y

    uv run tools/fitness_attest.py PATH/TO/BUNDLE/validity-domains \
        --product ECCO_L4_TEMP_SALINITY_LLC0090GRID_MONTHLY_V4R4 \
        --claim trend --region "35,45,-75,-65" --period "2010-01:2010-12" \
        --receipt fitness.json

Three verdicts, from signed validity-domain concepts in a knowledge
bundle: IN (a signed supporting domain fully contains your
declaration), OUT (a signed exclusion intersects it; exclusions take
precedence), UNADJUDICATED (no steward has spoken; honest silence,
never failure). Unsigned drafts are listed as advisory and never
adjudicate; malformed domains are quarantined visibly (on the console
and in the receipt's malformed_domains list, each problem named) and
adjudicate nothing; a claim class outside the governed vocabulary
(data/claim-classes.yaml) is refused outright. The receipt names the
governing concepts and records how the declaration was produced
(hand-declared today; the capsule-derived tier is refused until
capsules exist, so no receipt implies assurance that does not exist).

## Where the trust comes from

RED-TEAM.md is the eleven-row adversarial register every change is
reviewed against, and reviews/ holds the verdict of every PR, merged
with the change it reviewed: what was challenged, what blocked, what
was fixed. The publication policy (docs/publication-policy.md) binds
what leaves this repo, and docs/policy-log.md records each delivery
window in event-metadata-only form. Contributions take DCO sign-off
and one maintainer review plus the red-team verdict file; a new gate
tool lands its selftest in ci.yml's gates step in the same PR.
