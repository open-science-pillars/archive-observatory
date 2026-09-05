# Red-team verdict: PR 15 (resolve the knowledge checkout from a declared floor), round 1

VERDICT: PASS

The PR replaces the hand-pinned `ref:` of the knowledge checkout in
the seed job with a resolved one: data/dependencies.yaml declares a
version floor for nasa-daac-knowledge in the shape the marketplace
plugins use (name, repository, `>=2026.9.2`), and a new tool,
tools/resolve_release.py, lists the repository's release tags,
keeps the ones named `nasa-daac-knowledge--v{version}`, drops every
version outside the declared range, and writes the highest one and its
commit to the step outputs, which the checkout reads. R13's mitigation
and residual are rewritten to match; README and USING gain the tool
and the declaration. No rule, seed row, or provider-facing document
changes. Every register row was walked; the ones with a bearing are
below.

## What was checked

- **R2 (no rule misstated).** The seed check now runs against
  whichever release satisfies the floor, today
  nasa-daac-knowledge--v2026.9.2 (commit c6827f6), the same release
  PR 14 pinned. Run locally against it: PASS, 8 rules against 8
  concepts, 0 disagreements, 0 stale. The live resolve on the branch
  returned that tag from the 2 release tags upstream. The change
  moves who decides the reference from a steward's cue to the
  knowledge repository's release act, which is where the authority
  the seed mirrors is published.
- **R10 (credential-free tree).** The tree-wide grep is clean on the
  branch. The resolver makes one read-only call, `git ls-remote
  --tags https://github.com/...`, with no login, no environment
  variable, no secret; `persist-credentials: false` is kept on the
  checkout. The declaration file and the tool contain none of the
  register's pattern words.
- **R11 (verification-chain masking).** The resolver writes `ref=`
  and `commit=` to `$GITHUB_OUTPUT` itself; the step is a single
  command with no pipe and no `$(...)` capture, so a failing resolve
  fails the step. Its selftest is in the gates step in this PR, as the
  row requires of a new gate tool: 10 checks, no network, covering
  numeric ordering (2026.9.10 above 2026.9.9), peeled versus
  lightweight tags, a ceiling, an empty range, an exact pin, a branch
  name rejected as a range, the declaration read-back, and the output
  lines.
- **R12 (silent input dropping).** Tags that do not match
  `{name}--v{digits}` are ignored by design (other plugins' tags,
  `vnext`, bare `v2027.1.0`); the count of tags actually read is
  printed in the resolve line, so a floor that matches nothing shows
  how many candidates there were. An empty range is a FAIL with the
  floor and the count, not a fallback to a branch.
- **R13 (the rewritten row).** The mitigation still names a release
  tag, never a branch, and the tag is still chosen by this
  repository: the declaration is a reviewed file here, the resolver
  is reviewed code here, and only the set of published releases is
  upstream's. The residual is restated honestly: a new release can
  turn this job red with no commit here. That is the R2 signal the
  job exists to raise, arriving on the next run rather than on a
  steward's memory; the run log names the release and commit that
  produced it.
- **New attack surface.** A tag published upstream with a higher
  version is now picked up automatically. The tag namespace is the
  organization's, the release rule there binds a tag to a commit that
  owes no signatures, and a hostile tag would need write access to
  that repository, which is the same trust the pinned form relied on
  (a moved tag). A ceiling in the range (`<2027`) is available for a
  fork that wants to hold a major line without a hand pin.

## Closest call

Whether resolving the highest release quietly widens what runs in CI
compared with a literal pin. It does, by exactly one dimension: which
signed release of the organization's own knowledge repository. The
code path (seed_check and check_script_deps from that checkout) is
unchanged, the declaration is a literal a reviewer sees, and the
alternative, a hand-moved pin, had already produced its residual (a
cue that lives in someone's head). The PR trades a stale-reference
risk for a visible-red risk, and the register prefers visible.
