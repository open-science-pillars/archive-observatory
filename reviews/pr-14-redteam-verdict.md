# Red-team verdict: PR 14 (pin the knowledge checkout to a release tag), round 1

VERDICT: PASS

The PR changes one line of behavior in ci.yml, the `ref:` of the
knowledge checkout in the seed job, from the repository's default
branch to the release tag `nasa-daac-knowledge--v2026.9.2` (commit
c6827f6), and adds register row R13 naming the attack that line
closes. No tool, rule, seed row, or reader-facing document changes.
Every register row was walked; the ones with a bearing are below.

## What was checked

- **R2 (no rule misstated).** The seed check now compares the seed
  with a tagged, signed release of the esdis concepts instead of the
  moving branch. Run locally against that release: PASS, 8 rules
  against 8 concepts, 0 disagreements, 0 stale. The tree under
  knowledge/esdis at the tag is byte-identical to the branch tip at
  the time of this PR (`git diff --stat` between them is empty), so
  the pin changes what the job will compare against tomorrow, not
  what it compares against today.
- **R7 (framing).** The new prose is a workflow comment and a register
  row. Both describe a property of this repository's CI and name the
  upstream repository as the organization's own; neither makes a claim
  about any provider.
- **R9 (this file).** Verdict bound to the PR number, one round.
- **R10 (credential-free tree).** The tree-wide grep is clean on the
  branch. `persist-credentials: false` is kept on the pinned checkout;
  a tag ref adds no secret, no login, no environment variable. The row
  itself is written so the credential grep's own patterns do not
  self-match (the register is excluded from the grep for that reason,
  and the workflow comment avoids the pattern words).
- **R11 (verification-chain masking).** No `run:` step changes; the
  two steps that execute from the checkout remain single commands with
  no pipe, so their exit status is the step's.
- **R13 (the new row).** The mitigation is a designed-in control, not
  an intent: the pin is a literal in the workflow, a moved pin is a
  diff a reviewer sees, and the row binds moving it to a PR that
  re-runs the seed check. The residual is stated rather than waved
  away: the steward carries the cue to move the pin at each knowledge
  release, and a moved tag upstream is that repository's defect by
  its own release rule. A stricter pin (a commit SHA) was considered
  and not taken, because the tag name says which release the seed is
  measured against and the organization controls both repositories;
  the SHA is recorded in the comment for anyone who wants to check.
- **New attack surface.** None introduced. The change narrows what
  the checkout can do: before it, the code that ran in this job was
  chosen upstream; after it, by a reviewed commit here.

## Closest call

The residual in R13 is real: if a knowledge release corrects an esdis
concept, this repository's seed keeps passing against the old release
until someone moves the pin. That is the cost of choosing a release as
the reference, and it is the right reference for a published
observatory; a cue in the knowledge repository's release checklist
would close the gap from the other side and is worth a line there.
