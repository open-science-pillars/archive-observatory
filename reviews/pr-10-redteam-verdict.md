# Red-team verdict: PR 10 (requirements seed check), round 1

VERDICT: BLOCK

Everything this PR claims about the eight rules is true, and I checked
each claim against the concepts and the running code rather than the
PR body: the three changed statements are byte-identical to the
concept text they name, the two MUST citations hold against the live
UMM-C v1.18.4 schema, the separate CI job is necessary rather than
precautionary, and the tool rejects every drift I could think of
inside the four fields it compares. The block is on what sits outside
those four fields. The PR's thesis is that the concepts are the
authority and the seed follows them, and the gate that enforces the
thesis cannot see the two ways an authority stops being one: the
concept withdrawing (Finding 1), and the concept naming a check the
observatory's own sweeper does not run (Finding 2). Both were
demonstrated on a mutated copy of the bundle, both leave the gate
green, and both are closed by small additions to the file under
review.

## Finding 1 (R2): the gate is blind to the concept lifecycle, so a withdrawn, disputed, or stale authority still holds the seed

seed_check reads a concept's type, title, class, sources, first
sentence, and Check binding paragraph, and nothing else from the
frontmatter. OKF 0.2 (marketplace docs/SPECIFICATION.md, section 5.6)
defines three things a steward changes when a requirement stops being
one, and this tool reads none of them: `status: deprecated` with
`superseded_by`, `disputed: <issue URL>` on a stable concept (which a
citer MUST state), and `stale_after`, past which a concept is stale by
date comparison.

Verified on a copy of the real bundle: temporal-extent.md with
`status: deprecated` and `stale_after: 2020-01-01`, body untouched,
produces 0 disagreements and PASS. The same with a status value OKF
does not even define produces 0 disagreements. The gate reports that
the seed agrees with a concept that has been withdrawn.

Attack: none required. An upstream steward supersedes a requirement
concept, or opens a dispute on it, or its sweep date passes (the two
MUST concepts carry `stale_after: 2026-11-30`, less than three months
out). The seed keeps the rule, `seed-agrees-with-concepts` stays
green, and every sweep keeps flagging providers on it. Today the
scheduled sweep publishes nothing, since no optin/ directory exists,
so the consequence is bounded to local and manual runs until the first
opt-in lands; it goes live the day one does.

Consequence, per R2's row: "OSP misstates a requirement and flags
providers wrongly". R2's own mitigation column names the control that
this PR quietly relocates and then severs: "disputed rules carry the
disputed key and an upstream question", and the README's "Rule
disagreements route upstream, held out of publication until resolved".
With this PR, upstream is the concept, the concept has an OKF key for
exactly that state, and the sync gate does not carry it across. The
seed has no `disputed` key on any rule and the sweeper reads none
(grep confirms nothing in tools/ reads disputed, status, or
stale_after), so the R2 dispute control was a convention before this
PR; after it, the convention has an authoritative source it cannot
hear.

Fix direction (the builder fixes, not the red team): read the
lifecycle fields in load_concept and act on them in compare. A
`deprecated` concept must have no live rule, or the rule must carry a
matching key; a `disputed` concept must be mirrored by `disputed` on
the seed rule, which the sweeper can then hold out of publication as
R2 already promises; a passed `stale_after` is either a disagreement
or a printed warning, the steward's choice, but not silence. `draft`
must stay allowed, since all eight concepts are drafts today and the
seed's own citation gate is what holds MUST; requiring `stable` would
turn CI red on merge and prove nothing. One selftest scenario per
field lands with it in the gates step (R11).

## Finding 2 (R12, with R11 and R2): a seed that follows its concept exactly can bind a check the sweeper does not run, and the sweeper drops it on stderr

seed_check holds a cmr-structural id to the name the concept gives
after "Structural:". It never asks whether the observatory implements
that name. tools/sweep_providers.py line 158 answers that question at
load time by printing one WARN line to stderr and dropping the rule
with `continue`. The report then lists only the rules that survived,
with no count of rules dropped, and exits 0.

Verified end to end on a copy: a ninth concept version-present.md,
naming "Structural: version-present (cmr-structural, the observatory
sweeper)" as the concept template does, plus a ninth seed rule
following it field for field. seed_check: PASS, 9 rules against 9
concepts, 0 disagreements, exit 0. The sweeper's selftest on that same
seed: "WARN: rule req-version binds unknown structural check
version-present" on stderr, a report listing five rules, PASS, exit 0.
A MUST rule that three artifacts (concept, seed, green CI) say the
observatory checks is not checked, and under --fail-on-must a rule
that never runs cannot fail.

Attack: none required, and the incentive shape is this PR's own. The
orphan check is the sync signal the PR body advertises: a new
requirement concept upstream turns CI red with "has no seed rule". The
shortest path back to green is a seed rule copied from the concept.
Nothing on that path implements the check, and once the rule is in the
seed, both gates are green.

Consequence: this is R12's row with "record" replaced by "rule". A
rule is dropped before it runs, the drop is disclosed only on stderr,
and the artifact reports over a set that silently shrank. R11 names
what that makes the new gate: a green that turns out hollow. R2 names
the false claim: the concept's own text says the observatory sweeper
checks this, and this PR makes that text the authority.

Scope, stated plainly: the WARN and continue in load_rules predate
this PR, and on main today all five structural ids resolve. I am
blocking on it here because this PR is what turns "the seed and the
concept agree on a binding" into a green signal, and because R12's
mitigation ("a run that skipped anything cannot exit 0") is the
standard this repository adopted for exactly this shape.

Fix direction, either of two: seed_check imports STRUCTURAL from
sweep_providers (same directory, same single pyyaml dependency, so
nothing new to pin) and reports a cmr-structural id the sweeper does
not implement as a disagreement; or load_rules exits 2 on an unknown
structural id instead of warning, which makes the sweeper's selftest
in the gates step red the moment the live seed carries one. The second
is one line and closes the class for every caller of load_rules; the
first keeps the knowledge inside the gate that is about bindings. The
steward may also want R12's wording widened from records to rules, a
one-line register edit.

## What was verified, so the builder need not redo it

- Statements. Independent of the tool's normalization, req-doi and
  req-abstract are byte-identical to their concept's first sentence
  and req-related-urls is byte-identical to its concept's title. The
  five unchanged statements match too, three of them (gcmd, links,
  consistency) differing from the title only by a trailing period,
  which norm() strips. The tool's first-sentence extraction returns
  the right sentence for all eight concepts; I read each.
- Statement strictness. A statement that merely starts with the title
  ("Related URLs present in the record"), a prefix of the first
  sentence, and the frontmatter description field are all rejected
  with the rule, the field, and both values printed.
- Class, sources, binding. A seed SHOULD against a concept MUST, a
  MUST with an attributed section, a concept that drops a cited source
  id, a concept that renames its Structural id, a concept that loses
  its Check binding paragraph, a concept whose type changes, a
  concept renamed upstream (reported twice, as not found and as
  orphaned), a concept added upstream with no rule, and a pyquarc id
  taken from a different concept's paragraph: each produces exactly
  the disagreement it should and nothing else.
- MUST on the merits. The UMM-C v1.18.4 schema, fetched from
  cdn.earthdata.nasa.gov with a Client-Id and no login, lists
  TemporalExtents and SpatialExtent in its top-level required array.
  The seed's `section: verified` on both MUST rules is true even
  though the concepts that now carry the citation are unsigned
  drafts; the R2 gate is about the citation, not the signature, and
  the citation holds.
- The sibling checkout. It is public (visibility confirmed via the
  API), the runner's token was Contents: read and Metadata: read in
  the job log, no `secrets.` reference exists in the workflow, and the
  local clone I compared against is at the same commit CI used
  (9224fe5). The R10 grep run over that tree matches in 14 files
  (tutorials, fetch tools, the connector concept), so the ci.yml
  comment's reason for a separate job is a fact, not caution.
- No network in seed_check: imports are argparse, re, sys, tempfile,
  pathlib, yaml; the only URL in the file is example.invalid in the
  selftest template.
- The sweeper is indifferent to the new keys. load_rules reads id,
  class, source.section, and check; `statement` is read by nothing
  outside seed_check, so the three statement changes alter no report.
- No em or en dash and no build-scaffolding label in the diff or the
  five changed files, checked by grep.

## Register walk

- R1: no publication surface changes; the new job writes nothing.
- R2: Findings 1 and 2. The claims in README.md and docs/USING.md are
  otherwise true as written: the concepts exist at the named path,
  CI does run the comparison on every push and pull request, the
  default local path is the sibling clone.
- R3: untouched; PINNED_VERSION and the ruleset hash path are not in
  this diff.
- R4: no CMR call anywhere in the new tool or job.
- R5: yaml.safe_load only; concept values printed in DISAGREE lines
  are repr-quoted; nothing from the sibling tree is executed. The
  concept text is same-org, not third-party metadata.
- R6: untouched.
- R7: the direction is right and the wording holds it. The seed is
  "held to" the concepts, the fix "starts in the concept", the job is
  named for agreement, and a red here obliges the observatory, never
  the knowledge repository. Nothing reads as the observatory ruling on
  nasa-daac-knowledge. The one enforcement-shaped sentence in the
  chain is upstream's own ("the observatory sweeper" in each concept's
  binding paragraph), and Finding 2 is what happens when that
  sentence is trusted without being checked.
- R8: read-only into the bundle; no dated finding flows upstream.
- R9: this file, reviews/pr-10-redteam-verdict.md, round 1 of two.
- R10: the credential grep, run verbatim from the repository root,
  exits 0. The job reads no secrets. Non-blocking: the sibling
  checkout inherits `persist-credentials: true`, which writes the
  runner's read-only token into nasa-daac-knowledge/.git/config for
  the life of the job; nothing reads it, but `persist-credentials:
  false` on that step would make the "no login" comment literally
  true of the checkout as well as the tool.
- R11: every gate command ci.yml runs, from the repository root, exit
  codes read directly and no pipe: sweep_providers selftest 0,
  quarc_attest selftest 0, make_badge selftest 0, fitness_attest
  selftest 0, seed_check selftest 0 (17 scenarios), live seed_check
  against ../nasa-daac-knowledge/knowledge/esdis 0 (8 rules, 8
  concepts, 0 disagreements). The selftest lands in the gates step in
  the same PR as the tool, as the row requires, and on GitHub the
  only red step is R9's verdict-file test, which this file closes.
  Coverage gap, not blocking: four branches of compare() have no
  selftest scenario (concept type not requirement, concept
  unreadable, no Check binding paragraph, placeholder against an
  Unmapped binding). I exercised three of them live and they work;
  the selftest does not pin them.
- R12: Finding 2.

## The judgment call the PR body asked about

Keep the live job coupled to nasa-daac-knowledge main. A pinned ref
would recreate on a schedule the exact drift R2 exists to catch, and
the red this coupling produces is self-describing (the job name says
what disagreed, the tool prints rule, field, and both values), so a
reviewer can tell it from a PR's own failure in one line. The cost
the PR body names, a red X on an unrelated PR the day a concept
moves, is the sync signal doing its job. Finding 1 is the reason to
widen what that signal listens to, not a reason to mute it.

## Notes, none blocking

- Two rules on one concept slip past the uniqueness check if the path
  is spelled differently: a ninth rule naming
  `requirements/./related-urls-present.md` passes, and the summary
  line reads "9 rules against 8 concepts, 0 disagreements", a PASS
  that contradicts its own count. Resolving the path before using it
  as the key closes it. The seed is maintained in this repository, so
  this is drift-shaped rather than adversarial.
- A seed whose rules list contains a non-mapping entry raises
  AttributeError at line 137 and exits 1 with a traceback, which is
  the finding code in this repository's exit-code contract
  (docs/USING.md), not the malfunction code the docstring promises.
  CI still goes red, so no gate is hollowed; the contract is
  imprecise.
- The first-sentence heuristic splits at the first period followed by
  whitespace. Fine for all eight concepts today; a future first
  sentence containing "et al." or "e.g." would truncate, which on the
  honest path is a visible false red, and on a dishonest path lets a
  fragment ending in "e.g." pass as the statement (verified). Not
  worth code until a concept actually does it.
- norm() folds case and strips one trailing period, so "exactly" in
  docs/USING.md means modulo those two; neither is paraphrase, and
  the trailing period is what lets three unchanged statements stand.
- source.cites is a subset check: req-doi can cite only
  ramapriyan-2017, the source the concept quotes as a plan rather than
  a mandate, and pass. The concept offers no per-claim source map, so
  the tool cannot do better than membership; worth knowing when
  reading a green.
- The placeholder co-build-map is accepted against
  collection-granule-consistency.md because "Unmapped in pyQuARC
  v1.3.0" contains the word pyQuARC. That is the right answer for the
  right reason by accident; the concept says no check exists yet and
  the placeholder says the same thing.
- A pyquarc id the concept names only to reject would pass: the
  consistency concept names granule_spatial_representation_check as
  "too narrow to propose", and a seed rule binding it would be
  reported as named in the paragraph. Same family as Finding 2 at a
  lower stake, since no pyquarc id is live until the co-build maps
  them.

## For the steward

Nothing on main today is in either failure state: all eight concepts
are drafts, none deprecated or disputed, the nearest stale_after is
2026-11-30, and all five structural ids are implemented. The PR is a
strict improvement over a seed with no sync at all, and if the steward
reads two coverage gaps in a new control as follow-up rather than
block, the correct disposition is to overrule this verdict and merge
with both findings filed. I am blocking because the register closes a
finding only by a designed-in control, because both gaps sit in the
file under review and cost a few lines each, and because a gate named
for agreement with an authority should notice when the authority
withdraws or when it names a check nobody runs.

Closest call: Finding 2, which rides on a pre-existing WARN in
load_rules rather than on any line this PR wrote, and which I block on
only because this PR is what makes that WARN the sole disclosure
between a green gate and an unrun MUST rule.

---

# Red-team verdict: PR 10 (requirements seed check), round 2

VERDICT: APPROVE

The fix commit is 5f893d2 (b236fd8 amended for its sign-off line; git
diff b236fd8 5f893d2 is empty). I replayed both round 1 attacks
against it on copies of the esdis bundle and the seed, and both are
now caught in the file under review and, for the second, in the
sweeper as well. The three non-blocking notes the builder picked up
are closed. The gates are green by exit code. What remains is listed
under notes; none of it is a hollow green, none of it was introduced
by the fix, and none of it was in round 1's fix direction.

## Finding 1 (R2): closed

Reproduced on copies of ../nasa-daac-knowledge/knowledge/esdis (clone
at fbb0797; requirements/ unchanged since 9224fe5, the commit round 1
compared against), each mutation on its own copy, the concept body
untouched each time, seed_check run with --concepts pointed at the
copy:

- temporal-extent.md with `status: deprecated` and `superseded_by:
  requirements/temporal-extent-v2.md`, rule still in the seed: one
  DISAGREE line naming req-temporal-extent, the field status, the
  concept path, and the successor; exit 1.
- The same copy with req-temporal-extent removed from a copy of the
  seed: PASS, 7 rules against 8 concepts, 0 disagreements, exit 0.
  The deprecated concept is not reported as an orphan.
- doi-registered.md with `disputed: <issue URL>`, seed not mirrored:
  DISAGREE req-doi, field disputed, seed None and the concept's URL,
  exit 1. Seed mirrored with the same URL: PASS, exit 0. Seed
  mirrored with a different URL: DISAGREE with both URLs printed,
  exit 1. `disputed` on the seed rule against the unmodified bundle:
  DISAGREE, seed URL and concept None, exit 1.
- spatial-extent.md with `status: retired` and links-resolve.md with
  the legacy `status: superseded`: two DISAGREE lines, each naming the
  rule, the field, the value found, and the three values OKF defines;
  exit 1. A concept with the status key deleted is reported the same
  way; that is correct here, since SPEC section 5.1 makes an explicit
  status an org requirement even though OKF's own default is stable.
- temporal-extent.md with `stale_after: 2020-01-01`: one STALE line
  naming the rule, the path, the date and the days elapsed; summary
  reads 1 stale; exit 0. The round 1 mutation verbatim (deprecated
  plus that date) produces the DISAGREE and the STALE line together,
  exit 1. `stale_after: soon` is a DISAGREE (not a date), exit 1.
- All eight concepts at `status: stable`: PASS, exit 0. The live
  bundle, all drafts: PASS, exit 0.

Each disagreement prints the rule id, the field, and the values on
both sides where both sides have one (status and stale_after exist
only on the concept, and the line prints that value). The selftest
pins one scenario per field: deprecated with a live rule, deprecated
with no rule and no orphan report, stable, an undefined status,
disputed unmirrored, disputed mirrored, disputed on the rule only,
stale_after passed, ahead, and not a date. R2's gap as stated in
round 1, a gate that could not hear the concept withdraw, is closed
by code in compare().

## Finding 2 (R12, with R11 and R2): closed

Reproduced two ways. First, abstract-informative.md's `Structural:`
id and the seed's matching check.id both renamed to version-present:
seed_check reports DISAGREE req-abstract, check.id 'version-present'
named by the concept but not implemented, with the five implemented
ids listed, exit 1. sweep_providers --selftest on that seed prints
one refusal naming the rule, the id, and the implemented set, exit 2,
no report. sweep_providers --files on a record that passes every
implemented check, with --fail-on-must and --out-dir: exit 2, nothing
written. A rule that never ran cannot be a green under --fail-on-must
because the seed never loads. Second, round 1's exact shape, a ninth
concept version-present.md written from the concept template plus a
ninth rule copied from it field for field: seed_check FAIL with the
same disagreement, exit 1; the sweeper selftest refuses, exit 2.

The pin: on a scratch copy of tools/sweep_providers.py I put the old
WARN-and-continue back in place of the raise and ran its selftest; it
prints the WARN and ends "selftest: FAIL", exit 1. So the gates step
in ci.yml now fails if the refusal is ever removed, and since
load_rules runs before the --selftest branch, the same step fails the
day the live seed binds an id the sweeper lacks. load_rules has no
caller outside the sweeper (grep), so the raise changes no other
tool's behaviour, and main() turns it into exit 2 with the message.
R12's row now names rules beside records, which matches the code.

## The stale_after choice: a STALE line, counted, exit 0

I read the ground the builder cites. marketplace/docs/SPECIFICATION.md
section 5.6 defines staleness as a date comparison, describes what
follows as a steward sweep of the concept, and in its migration table
maps the old `stale` status to `status: stable` plus `stale_after`,
so a stale concept is by construction still a stable one; withdrawal
is a different form (`deprecated`), and that form is a disagreement
here. nasa-daac-knowledge/tools/check_okf_v02.py files a passed date
as W5, a warning that fails only under --strict, and that repository
has no CI workflow invoking the checker at all. The ground holds, and
the choice is one of the two round 1 offered. It is not silence: the
line is printed and the summary counts it.

One boundary: the spec and the checker both call a concept stale once
today >= stale_after, and seed_check uses stale_after < today, so on
the day itself seed_check is quiet while the checker on the same copy
prints W5 (verified with today's date on a copy). One day, warning
class either way; noted below, not blocking.

## What was verified

Every gate command ci.yml runs, from the repository root, exit codes
read directly and no pipe: sweep_providers selftest 0; quarc_attest
selftest 0; make_badge selftest 0; fitness_attest selftest 0;
seed_check selftest 0 (32 scenarios: 29 through compare() with an
injected structural set and a fixed date, 3 through run() with the
sweeper's real STRUCTURAL); live seed_check against
../nasa-daac-knowledge/knowledge/esdis 0 (8 rules, 8 concepts, 0
disagreements, 0 stale); the R10 grep exactly as ci.yml writes it 0,
and grep's own exit read separately as 1 (no match) rather than the
2 the negation would also turn green.

Also verified: the sweeper's raise reaches no other tool; the sweep
workflow runs the sweeper under the default failing shell with no
masking, so exit 2 stops it; the seed_check import of sweep_providers
loads only stdlib modules and pyyaml (already pinned by seed_check's
own block), makes no network call at import (socket.connect and
urlopen were patched to raise during the import, and neither fired),
and the sys.path insert shadows no stdlib name since tools/ holds
five files, none a stdlib module name. No dependency was added.
Regression pass on the copy for round 1's live scenarios: statement
prefix, SHOULD against a MUST concept, concept renamed upstream,
unreadable concept, an extra concept with unterminated frontmatter
(reported as an orphan, not treated as deprecated), a pyquarc id
from another concept's paragraph, a concept whose type changed; each
still produces exactly its disagreement. Path normalization: a ninth
rule naming requirements/./related-urls-present.md,
./requirements/related-urls-present.md, or
requirements/../requirements/related-urls-present.md is reported as
already the concept of req-related-urls, exit 1. A rule entry that is
a string, a rules key that is not a list, and an empty seed each exit
2 with one message and no traceback. `persist-credentials: false` is
on the sibling checkout at ci.yml line 42. No em or en dash in any
changed file; no build-scaffolding label in any added line; the
STALE and refusal messages and the USING.md paragraph read as this
repository's obligations, not as rulings on the knowledge repository
(R7).

## Register walk, rows the fix touches

- R2: Finding 1 closed; the gate now reads status, superseded_by,
  disputed and stale_after and acts on each as described above. The
  USING.md sentences added by the fix are each true of the code I
  ran.
- R5: the new import executes module-level code of a file in this
  repository only; nothing from the sibling tree is imported or
  executed, and concept values in the new DISAGREE lines are
  repr-quoted as before.
- R7: new user-facing text checked; see above.
- R10: the sibling checkout keeps no token in its config; the grep
  passes.
- R11: the refusal is pinned by the sweeper's own selftest in the
  gates step, demonstrated by regressing a copy; the new seed_check
  scenarios run in the same step.
- R12: Finding 2 closed on both paths; the row's wording now covers
  rules, and the code matches the row.

## Notes, none blocking

- The mirrored `disputed` key is a declaration, not yet a hold-out.
  Nothing in tools/ outside seed_check reads `disputed` (grep), so a
  rule carrying it is swept, tallied, printed in the aggregate, and
  counts toward --fail-on-must exactly as before. README.md and
  docs/publication-policy.md promise that a disputed rule is held
  out of publication until resolved; today that promise is
  convention. Round 1's fix direction asked for the mirror and said
  the sweeper "can then" hold the rule out, so this is not a
  reopening; it is the next line to write, and R12's shape applies
  (skip the rule, count and name the skip in the artifact, refuse a
  green under --fail-on-must over it). Exposure today is nil: no
  concept is disputed and no optin/ directory exists.
- The boundary day described above: seed_check reports a concept
  stale one day after the spec and the bundle checker do. Changing
  `<` to `<=` in compare() aligns the three.
- The summary line counts every requirements/*.md as a concept, so a
  correct run over a bundle with one deprecated concept reads "7
  rules against 8 concepts, 0 disagreements"; a deprecated count
  beside the stale count would make the line self-consistent.
- The scheduled sweep (sweep.yml) does not run seed_check before it
  sweeps, so between a concept withdrawing upstream and the next push
  to this repository, the monthly run would use the seed as it stands.
  The CI red on the next push is the only signal. Pre-existing, and
  moot until an opt-in exists.
- The R10 step's `!` negation turns a grep error (exit 2, for example
  an unreadable directory) into a pass as well as a no-match. I read
  grep's own exit code. Pre-existing and not touched by this PR.
- A STALE line inside a green job is visible only to someone reading
  the log. Three concepts carry stale_after 2026-11-30 and will cross
  it in under three months with CI still green; if the steward wants
  a nudge, a flag that promotes stale to exit 1, or a scheduled issue,
  is the place, and neither belongs in this PR.

## For the steward

Both round 1 findings are closed by code in the files under review,
each with a selftest scenario in the gates step, and I reproduced
every attack round 1 described against the fixed tree rather than
reading the diff for it. The stale_after choice is the one round 1
offered as a printed warning, and the builder's stated ground for it
is what the spec and the bundle checker actually say. Nothing in the
notes is a green over unexamined content; the largest open item, the
sweeper's indifference to the `disputed` key, predates this PR and is
worth a follow-up issue rather than a third round the contract does
not allow. Closest call: whether to treat that indifference as a
reopening of Finding 1, and I do not, because round 1 asked for the
gate to hear the dispute and it now does, while holding the rule out
of a sweep is a change to a different tool that round 1 named as the
next step rather than as the fix.
