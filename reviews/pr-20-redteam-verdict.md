# Red-team verdict: PR 20 (README, place in the organization), round 1

VERDICT: APPROVE

Reviewed and approved by the steward (Paul Ramirez) on 2026-09-12; the
text was drafted for that review.

One file: the README gains a ten-line section stating what kind of
repository this is. It is a tooling repository classified on its own
terms rather than by sphere; its readers are data engineers and archive
operators; what it holds is PROVE instruments; its rules are KNOW,
authored as requirement concepts in the ESDIS bundle and owned by that
bundle's stewards. No tool, rule, seed, workflow, metadata or concept
changes.

## What was checked

- R7 (framing): the community-mirror frame is untouched; the new
  section says the observatory follows the ESDIS rules, not that it
  audits or grades the archives.
- R9 (verdict per PR): this file.
- R10 (credential-free tree): the grep is clean; prose only.
- R11 (masking): no gate tool added or changed.
- R13 (release, never a branch): no checkout added; nothing from
  another repository executes here.

## Closest call

Whether saying the rules are "owned by that bundle's stewards" hands
the observatory's behaviour to another repository. It does not: the
ownership named is authorship of the requirement concepts, which was
already the case. What runs here is still a signed release tag of the
knowledge repository resolved from the floor in data/dependencies.yaml,
never a branch, and the seed check (R2) fails this tree the moment the
concepts and data/requirements-seed.yaml disagree, so a rule change
upstream becomes visible here as a red run, not a silent change.
