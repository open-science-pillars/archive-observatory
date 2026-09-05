# Red-team verdict: PR 16 (the knowledge repository's wording check from the release checkout), round 1

VERDICT: APPROVE

The PR adds one step to the seed job: the knowledge repository's
wording check (tools/check_prose.py), run from the release checkout
that job already makes, over this tree with reviews/ excluded. It
raises the floor in data/dependencies.yaml from `>=2026.9.2` to
`>=2026.9.3`, the first release that carries the tool, and names the
check in the purpose line. USING.md gains a paragraph on the two
borrowed checks and the sibling-clone commands. No rule, seed row,
tool, or provider-facing document changes. Every register row was
walked; the ones with a bearing are below.

## What was checked

- **R2 (no rule misstated).** Nothing about the seed or the concepts
  moves. The resolver on the branch returns
  nasa-daac-knowledge--v2026.9.3 (commit 3abb2fb) as the highest of 3
  release tags satisfying the new floor; seed_check against a sibling
  clone at that release: PASS, 8 rules against 8 concepts, 0
  disagreements, 0 stale. That release's own tag run passed with the
  signature debt enforced, so the reference stays a signed release.
- **R7 (mirror, not enforcement).** The check reads this repository's
  own prose and nothing a provider wrote; its rules are about how
  this project cites and speaks. No provider-facing text changes.
- **R10 (credential-free tree).** The tree-wide grep, CI's exact
  command, is clean on the branch. The borrowed tool reads disk and
  makes no network call; the checkout keeps `persist-credentials:
  false`. The new YAML, workflow lines and USING paragraph contain
  none of the register's pattern words.
- **R11 (verification-chain masking).** One finding, raised in this
  round and fixed by the builder before the verdict (commit f58e796):
  the row requires a gate tool's selftest to run where a nonzero exit
  fails the job, and the first commit ran the borrowed check's
  selftest only upstream, in the knowledge repository's own gate. The
  step now runs `check_prose.py --selftest` first and the scan second,
  from the same release checkout; the step's shell stops on the first
  failing line, neither line is piped, and no output is captured. The
  selftest builds its own fixtures and needs no data. Verified on the
  branch: selftest ok, scan clean, 23 files.
- **R12 (silent input dropping).** The exclusion is one glob,
  `reviews/*`, stated in the workflow, in USING.md and in this file,
  with the reason: a verdict quotes the text it judged, dated, and two
  earlier verdicts (PR 6 and PR 9) quote a phrase the tree has since
  dropped, which is exactly the case the exclusion exists for. The
  tool prints how many files it scanned, so a glob that swallowed the
  tree would show as a falling count, not as silence. The tool's own
  skip list (SPECIFICATION.md, bundle logs, upstream vendored text)
  touches nothing in this repository.
- **R13 (release, never a branch).** The new step executes from the
  same tagged checkout as the two before it; the floor moved in this
  repository, in a reviewed file, and the tag was published before
  the floor named it, which is the order the release rule requires.
  The residual is unchanged: a new knowledge release can turn this
  job red with no commit here, and now also by a wording rule the
  knowledge repository tightens, which the run log names by release.
- **New attack surface.** A wording check is a text scan with three
  regular expressions; a hostile pattern would have to arrive in a
  signed release of the organization's own repository, the same trust
  the seed check already places there. A green here says the prose
  follows the rules the check encodes, no more.

## Closest call

Whether excluding reviews/ from the wording check quietly exempts the
one directory that documents this repository's judgment. It does, for
the wording rules only: a verdict is a dated record that quotes what
it judged, and rewriting old quotations to satisfy a later rule would
falsify the record, which is a worse property than an unchecked
adjective. The credential grep already treats reviews/ the same way
for the same reason, so the exclusion follows a line the register
drew, and new verdicts are still read by a human before they merge.
