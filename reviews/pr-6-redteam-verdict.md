# Red-team verdict: PR 6 (provenance property), round 1

VERDICT: BLOCK

One finding, small and one word deep, but it sits in the load-bearing
clause of the only content under review.

## Finding 1 (R2): the property's final clause is truncated and
asserts nothing

README.md, the added bullet's last sentence reads, verbatim: "so no
receipt implies assurance that does not." The sentence ends there. The
word "exist" is missing; the contract this bullet records is stated
correctly in tools/fitness_attest.py's own docstring ("so a receipt
can never claim assurance that does not exist") and in
data/claim-classes.yaml's capsule-derived note. As published, the
clause that justifies the property's title parses as broken English
and asserts nothing coherent.

Attack: none required; this is an authoring truncation. Consequence,
per R2's family: the Properties list is the observatory's public
credibility surface, and a property statement that ends mid-thought
invites the wholesale-dismissal failure R2 names, applied to the
observatory's own claims rather than a provider's. A reader deciding
whether to trust receipts meets a garbled sentence at exactly the
point where the no-inflation guarantee is stated.

Fix direction (the builder fixes, not the red team): restore the
dropped word so the clause reads "assurance that does not exist."

## Register walk, what held

- Accuracy against the running code (the review's core question): every
  other claim in the bullet is enforced, verified live during the PR 5
  rounds against tools/fitness_attest.py at 0ab111a. Receipts record
  declaration_provenance; hand-declared is recorded plainly; the
  capsule-derived tier is refused with REFUSED at exit 1, and the code
  is in fact stronger than the bullet claims, refusing every
  provenance other than hand-declared, not only capsule-derived. The
  kit 15 attribution matches the docstring and the vocabulary file.
  Nothing in the bullet claims what the code does not enforce.
- R7 tone: mirror, not enforcement. "Says so plainly" and "refused
  until capsules exist" describe the tool's own restraint, name no
  provider, and match the register's framing discipline of the
  sibling bullets.
- R10, R11: not implicated; the diff is one commit (bc7aa99) touching
  README.md only, no code, no gates, no credential patterns, and the
  branch README carries zero em or en dashes.
- R9: this verdict is filed at reviews/pr-6-redteam-verdict.md, bound
  to PR 6.

Round 2 on the one-word fix should be immediate.
