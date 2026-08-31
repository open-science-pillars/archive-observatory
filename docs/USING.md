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
| tools/sweep_providers.py | Structural sweep of a provider's collections against the rules seed; aggregate plus private detail | yes |
| tools/quarc_attest.py | pyQuARC run on collections, receipt with pinned identity, deterministic attestation | yes |
| tools/make_badge.py | Shields badge from an attested receipt; strictly opt-in | yes |
| tools/fitness_attest.py | Can-I-use-X-for-Y verdicts against signed validity domains | yes |

Selftests for all four run in CI on every push; run them yourself the
same way CI does:

    uv run tools/sweep_providers.py data/requirements-seed.yaml --selftest
    uv run tools/quarc_attest.py --selftest
    uv run tools/make_badge.py --selftest
    uv run tools/fitness_attest.py --selftest

## Sweep your provider

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
        --claim trend --region "35,45,-75,-65" --period "2010-01:2010-12"

Three verdicts, from signed validity-domain concepts in a knowledge
bundle: IN (a signed supporting domain fully contains your
declaration), OUT (a signed exclusion intersects it; exclusions take
precedence), UNADJUDICATED (no steward has spoken; honest silence,
never failure). Unsigned drafts are listed as advisory and never
adjudicate; malformed domains are quarantined visibly and adjudicate
nothing; a claim class outside the governed vocabulary
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
