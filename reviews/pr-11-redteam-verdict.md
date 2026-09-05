# Red-team verdict: PR 11 (the partner team named ASSET), round 1

VERDICT: PASS

The PR renames the partner team in five reader-facing files after
ESDIS's renaming of the Science Enabling Teams to the Application
Support and Science Enabling Teams (ASSETs). Every changed line was
read against the register.

## What was checked

- **R2 (no claim without a source, no rule restated wrong).** Each
  edit is a proper noun swap with the expansion at first mention in
  its file; no rule text, class, mitigation, or seed row changed. The
  seed still agrees with the esdis concepts field by field (8 rules, 0
  disagreements, 0 stale, run against the companion nasa-daac-knowledge
  branch), so the authority chain R2 protects is intact.
- **R7 (framing).** "The partnership with the ASSET" and "the ASSET is
  the natural broker" keep the community-member, with-the-archive
  posture the row requires; nothing in the new wording claims
  affiliation or authority.
- **R10 (credential-free tree).** The tree-wide grep is clean on the
  branch.
- **Authoring staleness (the PR 6 and PR 9 family).** A grep for the
  old name and the bare acronym across the tree finds no remaining
  reader-facing mention outside dated log entries. README's register
  count is unaffected (the register still has twelve rows).

## One correction made during review

The first push edited the 2026-08-30 entry in docs/policy-log.md to
carry the new name. A dated log entry is a record of what was true
and said on its date; rewriting it is the same class of error as
backdating a claim. The edit is reverted in this PR's second commit:
the log keeps the name in use when the entry was written, which is
also the discipline the esdis bundle's own log follows in the
companion PR.

## Scope note for the steward

The source of the rename is an internal PO.DAAC status slide. If the
new name has not yet been used publicly by ESDIS, holding this PR
until it has costs nothing; the change is inert until merged.
