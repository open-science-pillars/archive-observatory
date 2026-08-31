# Red-team verdict: PR 5 (fitness attester), round 1

VERDICT: BLOCK

Two findings, both R5. The attester's promise is that a verdict derives
from structure and that third-party concept content cannot steer it. Two
type-confusion paths break that promise: a signed validity-domain whose
frontmatter carries a plain string where a list is expected produces a
spurious IN or OUT, because Python's membership and iteration operators
silently change meaning for a str. A steward who signs a domain that
reads as narrow is made to grant scope they never wrote, and a crafted
domain steers the verdict. Both are reachable from ordinary YAML
authoring habits, not only hostile input, which is what makes them
BLOCK rather than hardening notes.

## Finding 1 (R5): scalar claim_classes adjudicates by substring

tools/fitness_attest.py, class_covered (line 89): `if declared in
domain_classes`. When a domain's `claim_classes` is a YAML scalar string
instead of a list, `in` becomes substring containment, not list
membership. A signed domain with `claim_classes: trends-of-the-basin`
adjudicates a `trend` declaration IN, because `'trend' in
'trends-of-the-basin'` is true. The closed-vocabulary invariant is
enforced only on the declaration side (main, line 268), never on a
domain's claim_classes, so a domain may name an ungoverned string, and
that ungoverned string then adjudicates a governed class by coincidence
of letters.

Attack: land or sign a validity-domain whose claim_classes scalar
contains a governed class name as a substring (trend inside trends,
budgets inside budgets-heat), with matching product, region, and period
scope.

Consequence: a fitness verdict of IN backed by a signature that never
covered the declared class. The attestation asserts assurance the
steward did not grant, which is the exact steering R5 forbids.

Evidence: `uv run tools/fitness_attest.py $DIR --product
ECCO_TEST_MONTHLY --claim trend` against a signed domain with
`claim_classes: trends-of-the-basin` returns `verdict: IN`.

## Finding 2 (R5): scalar products becomes match-all-products

tools/fitness_attest.py, product_match (line 95): `any(fnmatch.fnmatch(
declared, pat) for pat in patterns)`. When a domain's `products` is a
YAML scalar string instead of a list, `for pat in patterns` iterates the
string character by character. Almost every real product glob contains a
`*`, and `fnmatch(anything, '*')` is true, so the domain matches every
product on earth.

Attack: sign a domain with `products: 'ECCO_L4_SSH_*'` written as a
scalar, the most natural single-pattern authoring form. For a supporting
domain this yields IN for unrelated products; for an exclusion it yields
OUT for unrelated products, and exclusions take precedence, so the blast
radius is the whole product space.

Consequence: a signature on a domain that reads as narrow silently
attests, or taints, every product. The IN semantics require that a
signed supporting domain fully contains the declaration; here
containment is decided by a stray glob character, not by structure.

Evidence: `uv run tools/fitness_attest.py $DIR --product
COMPLETELY_UNRELATED_PRODUCT --claim mean-state` against a signed
supporting domain with scalar `products: 'ECCO_TEST_*'` returns
`verdict: IN`.

Shared root cause and fix direction (the builder fixes, not the red
team): validate frontmatter types before use. Require `claim_classes`
and `products` to be lists, validate every domain claim_classes member
against the governed vocabulary, and reject or skip a domain whose scope
fields are malformed rather than reading them through str semantics.

## Register walk, what held

- Refusal paths verified against the code. Invented class: `--claim
  invented-thing` returns REFUSED, exit 1, main line 268. Capsule tier:
  `--provenance capsule-derived` returns REFUSED, exit 1, attest line
  145. Neither can be coaxed to a verdict.
- Draft-never-adjudicates held under attack (R5). A draft `polarity:
  exclusion` domain with `products: ['*']` did not veto a signed
  supporting IN; it was listed as advisory only. Unsigned never flips a
  verdict, is_signed gates the governing list at line 161.
- Signature spoofing on the by-field held. `by: 'humanX:Mallory'` and a
  non-string `by: 12345` both fail is_signed and fall to advisory. Note
  only: `by: 'human:'` with an empty actor is accepted as signed, since
  is_signed is a prefix check; that is consistent with the format's
  trust convention that anyone able to write the file can already write
  a named actor, so it is not a new hole, but a schema for the actor
  string would close the degenerate case.
- Umbrella subsumption is exactly one level (R subsumption). A vocabulary
  where grand covers middle covers leaf, with a domain signed for grand,
  returns IN for a middle declaration and UNADJUDICATED for a leaf
  declaration. It never recurses.
- Vocabulary sha binds. The receipt's vocabulary_sha256 equals the
  sha256 of the exact data/claim-classes.yaml bytes that main loaded and
  adjudicated with, so the receipt binds the vocabulary actually used.
- R11: the new gate's selftest lands in ci.yml's gates step in this same
  PR, line 14, inside the plain Selftests run block with no pipe, so a
  nonzero exit fails the job, unmasked. Verified by running `uv run
  tools/fitness_attest.py --selftest`, which prints PASS at exit 0.
- R10: the exact CI credential grep run at repo root returns exit 0, no
  matches; the new code adds no netrc, token, Authorization, api-key, or
  EDL patterns.
- R9: this verdict is filed at reviews/pr-5-redteam-verdict.md, bound to
  PR 5, which the CI R9 step checks.
- R7 tone: the docstring, refusal strings, UNADJUDICATED framing
  (honest silence, never failure), and the vocabulary notes read as a
  mirror, not enforcement, and name no provider. No R7 finding.

Closest call: R11 and R7 both pass cleanly and the refusal and draft
rules are sound, so the block rests entirely on the two type-confusion
verdict-steering paths under R5; had frontmatter types been validated,
this would have been an APPROVE.
