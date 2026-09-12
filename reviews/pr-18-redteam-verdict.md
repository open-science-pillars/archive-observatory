# Red-team verdict: PR 18 (canonical .osp metadata), round 1

VERDICT: APPROVE

Reviewed and approved by the steward (Paul Ramirez) on 2026-09-12; the
text was drafted for that review.

Two YAML files land under `.osp/` and nothing else moves: the
repository classification (kind tooling, status available, no sphere,
an audience line naming data engineers and archive operators) and the
governance file at schema version 2, which adds the runtime-adapter
review line and leaves maintainers and review counts as they were.

## What was checked

- R7 (framing): the audience line keeps the community-mirror frame and
  states the placement on the repository's own terms, in the file the
  organization renders its profile from.
- R10 (credential-free tree): the grep is clean; names and policy
  constants only.
- R11 (masking): no gate tool added or changed; nothing new needs a
  selftest.
- R13 (release, never a branch): no checkout added; nothing from another
  repository executes here.

## Closest call

Whether kind tooling with no sphere demotes the observatory beside the
science capabilities. It does not: the sphere view groups foundation
and tooling with their audience line, and ADR A records the placement
as deliberate because the readers are the archive's engineers.
