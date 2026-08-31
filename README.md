# Archive Observatory

Cross-archive metadata compliance as receipted checks: a structural
sweeper over public CMR, a pyQuARC harness pinned by git tag with a
hashed ruleset in every receipt, and a deterministic attester. Produced
by Open Science Pillars, a community open-source project; not a NASA,
JPL, or PO.DAAC product. The frame is a mirror held up with the
archives, not an audit performed on them.

## Properties, not preferences

- **Credential-free by construction.** Everything here runs against
  public CMR search with a Client-Id and no login of any kind; CI greps
  the tree and fails on credential patterns (register R10). That is
  also what makes the observatory forkable by any DAAC.
- **Aggregate-public, detail-private.** Cross-archive statistics are
  the only default-public output; per-provider detail goes privately to
  that provider with a 30-day window; per-collection reports and badges
  are strictly opt-in (docs/publication-policy.md).
- **Receipts on everything.** Every pyQuARC run records the pinned
  version, a sha256 of the effective ruleset files, and the record
  concept ids; the attester rejects receipts that do not match the
  environment (register R3, R6).
- **Rules carry provenance.** MUST means a documented requirement with
  a verified source citation; SHOULD means an attributed best practice,
  never presented as a mandate (register R2). Rule disagreements route
  upstream, held out of publication until resolved.
- **No LLM in the gate path.** Sweep, harness, and attester are
  deterministic; metadata is rendered as quoted data (register R5).
- **Provenance tiers never inflate.** Fitness verdicts
  (tools/fitness_attest.py) record how each declaration was produced;
  hand-declared says so plainly, and the capsule-derived tier is
  refused until capsules exist, so no
  receipt implies assurance that does not exist.

## The register

RED-TEAM.md is the standing adversarial register: ten attacks, their
consequences, and the designed-in mitigations. Every PR is reviewed
against it by the red-team agent (agents/red-team.md), whose verdict
file merges with the change; CI enforces its presence.

## Layout

```
tools/sweep_providers.py     structural sweep over CMR collections.umm_json
tools/quarc_attest.py        pinned pyQuARC runner, receipts, attester
tools/make_badge.py          opt-in badge from an attested receipt
tools/fitness_attest.py      can-I-use-X-for-Y verdicts from signed domains
data/requirements-seed.yaml  MUST/SHOULD rules with provenance gating
data/claim-classes.yaml      the governed claim-class vocabulary
docs/USING.md                the operator's guide (start here to run things)
docs/publication-policy.md   the publication policy, binding
docs/policy-log.md           delivery windows, event metadata only
agents/red-team.md           the reviewer contract
reviews/                     every PR's red-team verdict, merged with it
templates/provider-report.md the private-first receipted report
.github/workflows/           ci.yml (gates) and sweep.yml (monthly aggregate)
```

New here and want to run something? docs/USING.md walks all four
tools from clone to first receipt, credential-free (python via uv
only; the PEP 723 blocks carry the pins).

## Contributing

Apache 2.0, DCO sign-off on every commit (git commit -s). Ordinary
changes take one maintainer review plus the red-team verdict file.
Governance follows the org defaults (.osp/governance.yaml); maintainer
status is interim until the Science Enabling Team co-build.
