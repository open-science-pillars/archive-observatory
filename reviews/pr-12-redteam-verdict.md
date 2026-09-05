# Red-team verdict: PR 12 (every tool declares the dependencies it imports), round 1

VERDICT: PASS

The PR adds one CI step to the job that already checks out the public
knowledge repository: that repository's `check_script_deps.py` scans
`tools/` and fails when a script imports a package its PEP 723 header
does not declare. No tool, rule, seed row, or reader-facing document
changes. Every register row was walked; the ones with a bearing are
below.

## What was checked

- **R2 (no rule misstated).** No rule text or seed row is touched; the
  seed-agrees-with-concepts check that guards the authority chain runs
  unchanged in the same job, before the new step.
- **R7 (framing).** The only new prose is a workflow comment. It
  describes a property of this repository (a fork runs with nothing
  installed but uv); it makes no claim about any provider.
- **R9 (this file).** Verdict bound to the PR number, one round.
- **R10 (credential-free tree).** The tree-wide grep is clean on the
  branch. The new step reads files on disk and executes nothing that
  reaches a network; it runs in the job whose knowledge checkout
  already sets `persist-credentials: false`, and adds no secret, no
  login, no environment variable. The step's stated purpose is the
  same forkability R10 protects, for dependencies: a script that
  imports what it never declared runs only on a machine where the
  package happens to be present, which is a fork that silently fails.
- **R11 (verification-chain masking).** The step is a single `run:`
  command with no pipe, so the checker's exit status is the step's.
  Confirmed locally that the checker exits 1 on an undeclared import
  (its selftest covers the case) and 0 on the five tools here.
- **New attack surface.** None introduced. The step executes code from
  the knowledge repository's default branch, but so does the seed
  check beside it, in the same job, since the job was created; this
  PR does not widen what that checkout can do or where its code runs.

## Closest call

The knowledge checkout that both steps execute code from is unpinned
(default branch, not a tag), which the register does not currently
name. It predates this PR and applies equally to the seed check, so it
is not a finding against this change; it is worth a row of its own if
the steward wants the pin to be a rule rather than a habit.
