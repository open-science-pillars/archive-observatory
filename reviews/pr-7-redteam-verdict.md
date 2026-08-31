# Red-team verdict: PR 7 (operator's guide), round 1

VERDICT: BLOCK

One finding in 117 lines. The guide's accuracy was walked sentence by
sentence against the running tools, and it is very good; the one miss
sits exactly on a residual this red team recorded two reviews ago,
which is why it does not pass.

## Finding 1 (R2): "quarantined visibly" claims a surface the recipe
does not produce

docs/USING.md, the fitness section, says malformed domains "are
quarantined visibly and adjudicate nothing". Adjudicate nothing is
true and was verified live in the PR 5 rounds. Visibly is true only
of the receipt: the quarantine lands in the receipt's
malformed_domains list, and tools/fitness_attest.py's console output
prints governing and advisory entries but never malformed ones. The
guide's worked recipe for this tool passes no --receipt flag, so an
operator following the recipe exactly as printed sees no quarantine
anywhere, and the guide never says where the quarantine is visible.
This is the precise visibility gap recorded as the closest call in
the PR 5 round 2 verdict (quarantined exclusion "visible only in the
receipt, not in the console summary").

Attack: none required; the consequence is R2's, applied to the
observatory's own documentation. An operator who reads "quarantined
visibly", runs the recipe against a bundle with a malformed signed
domain, and sees nothing has caught the guide claiming behavior the
command does not show, and the wholesale-dismissal risk R2 names then
attaches to the rest of a guide that is otherwise verifiably exact.

Fix direction (the builder fixes, not the red team), either is
sufficient: add --receipt to the recipe and state that the receipt's
malformed_domains list carries the quarantine with problems named, or
reword to "quarantined in the receipt" without the visibility claim.
Making the tool print the quarantine is a code change and does not
belong in this docs-only PR.

## Register walk, what held

- Accuracy, sweep section: the aggregate filename
  (PROVIDER-DATE-aggregate.txt), the -PRIVATE detail suffix, the
  one-second page throttle, the umm_json-over-json DOI rationale, the
  DOI state breakdown, the SHOULD* footnote, and the non-affiliation
  line all match sweep_providers.py's report() and fetch_provider();
  the MUST demotion at load time is code (load_rules sets SHOULD*
  when the source section is not verified) and the selftest proves
  it. The .gitignore holds sweeps/, and sweep.yml sweeps nothing
  without the written opt-in, removes PRIVATE files, and force-adds
  only *-aggregate.txt, exactly as the guide states (R1, R2, R4).
- Accuracy, quarc section: the receipt anatomy block matches run()'s
  receipt field for field; A1 through A5 match attest() clause for
  clause, including A5's fail-closed unverifiable branch; the
  version.txt discrepancy framing (pin v1.3.0, self-report 1.2.8)
  matches the R3 record in the code and PINNED_VERSION; the
  skip-env-checks caveat matches make_badge.py's hardcoded
  skip_env_checks=False (R3, R5, R6).
- Accuracy, badge section: both refusals verified in code and proven
  by the selftest run live (opt-in missing refuses; full attest
  failure refuses and no badge directory is created); endpoint JSON
  named by concept id with the receipt copied alongside matches
  emit() (R1, R6).
- Accuracy, fitness section: the three verdicts, exclusion
  precedence on intersection, containment for IN, advisory drafts
  never adjudicating, the governed-vocabulary refusal, and the
  provenance sentence all match behavior verified live in the PR 5
  and 6 rounds, and the provenance clause carries the repaired
  "assurance that does not exist" wording verbatim.
- Structure: every file the guide and the refreshed README layout
  name exists on this branch (all four tools, data/claim-classes.yaml,
  docs/policy-log.md, reviews/pr-1 through pr-6, templates,
  sweep.yml); the register is eleven rows as stated; all four
  selftests are in ci.yml's gates step unmasked and all four ran PASS
  at exit 0 locally (R11).
- R10: the exact CI credential grep finds no patterns in either
  changed file; the guide adds no credentialed step anywhere.
- R7 tone: mirror throughout; the sweep "pages politely", detail is
  delivered privately, the non-affiliation line is quoted, and no
  provider is named negatively; POCLOUD appears only as the opt-in
  exemplar the policy designed (R1).
- R2 MUST/SHOULD: the guide's definitions match the seed's header and
  the enforced load-time gate, and it claims the gate as code, which
  is exactly what load_rules is.
- R9: this verdict is filed at reviews/pr-7-redteam-verdict.md, bound
  to PR 7.

Accepted as written, noted for the record: the aggregate-scoped claim
that a conformant DOI declaration "never reads as a miss" holds for
the aggregate, whose states line separates missing-reason declared
from malformed or absent, though the private detail file does list
such collections under the failing heading; and "suffixed -PRIVATE"
describes detail-PRIVATE.md loosely but truthfully. Neither steers an
operator wrong.

Round 2 on the one-sentence fix should be immediate.

# Red-team verdict: PR 7 (operator's guide), round 2

VERDICT: APPROVE

Finding 1 is withdrawn on its factual premise, and the error was the
red team's. Round 1 asserted that the console prints governing and
advisory entries but never malformed ones; that was verified against
a stale local checkout at 0ab111a, not against the branch under
review. Commit 80d1878 on main, an ancestor of this branch's tip
(6076bdc), applied the PR 5 round 2 closest-call note as a four-line
builder fix: main() prints every malformed_domains entry on stdout
with a [SIGNED] tag and the problems joined. Verified the direct way
the dispute proposed, against the branch's own code extracted from
6076bdc: a signed domain with scalar claim_classes, run through the
guide's documented recipe with no --receipt flag, prints "malformed
(quarantined, adjudicates nothing) [SIGNED]" with the problem named,
alongside verdict UNADJUDICATED, and the branch selftest passes at
exit 0. The guide's sentence "malformed domains are quarantined
visibly and adjudicate nothing" is therefore accurate against the
running code, and no fix is needed. The lesson lands on the red team:
verify against the branch under review, not against memory of a
checkout, which is this contract's own first rule.

Register IDs checked, round 2: R2 (the disputed sentence is accurate
as published; no overclaim remains anywhere in the guide, per the
round 1 walk that otherwise held in full), R5 (the four added print
lines render only validator-generated problem strings, the concept
path, and the signed flag, as labeled data, consistent with the
quoted-data posture), R9 (this round appends to the verdict file
bound to PR 7), R11 (the branch's own selftest runs PASS at exit 0,
and ci.yml's gates step is unchanged by this PR).

On the builder's concession offered for judgment: adding --receipt to
the fitness recipe so operators capture the full receipt would match
the guide's receipt-anatomy habit elsewhere and is a fair
improvement, and it is exactly that, an improvement and not a
correction; nothing blocks on it.

Closest call: none on the content; the round turned entirely on the
red team re-verifying its own premise and finding it stale.
