# Red-team verdict: PR 17 (exclude the knowledge checkout from the wording scan), round 1

VERDICT: APPROVE

One workflow line changes: the wording step's scan gains
`--exclude 'nasa-daac-knowledge/*'`, and the step comment says why.
The first main run after PR 16 scanned 222 files where this repository
holds 23 the check reads, because the seed job checks the knowledge
release out inside this tree and the scan walked it. Every register
row was walked; the ones with a bearing are below.

## What was checked

- **R10 (credential-free tree).** The grep is clean on the branch;
  the new glob contains none of the pattern words and nothing else
  moves.
- **R11 (verification-chain masking).** The step is the same two
  unpiped lines with one more argument; the selftest still runs first
  and the shell still stops on the first failing line. Verified on
  the branch with a copy of the knowledge tools placed at the
  excluded path: 49 files without the exclusion, 23 with it, clean
  both ways; the CI count for the full checkout was 222.
- **R12 (silent input dropping).** The exclusion removes a tree that
  is not this repository's and that the knowledge repository gates
  itself, at the same release, on the tag run that publishes it. The
  scanned-file count is printed, and 23 is the number this
  repository's own tree produces locally, so the scope of the check
  is now a number a reader can compare with a sibling clone rather
  than one that grows with the upstream tree.
- **R13 (release, never a branch).** Unchanged. The exclusion does
  not alter which release is checked out or what executes from it; it
  changes what the borrowed check is pointed at, which was always
  meant to be this repository's prose.

## Closest call

Whether excluding the upstream checkout hides a wording defect in the
release this repository depends on. It does not hide anything the
check was meant to find here: that tree passed the same check in its
own gate before its tag was published, and a repository measuring a
dependency's prose in its own CI would be reporting a red no diff here
could explain, which is the R13 residual this repository chose to keep
narrow.
