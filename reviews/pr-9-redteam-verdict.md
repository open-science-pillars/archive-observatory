# Red-team verdict: PR 9 (readability cleanup), round 1

VERDICT: BLOCK

One finding, and it is not in the diff's own edits: every line this PR
changes verified clean, including both places the steward flagged. The
finding is a false claim left standing in README.md, three lines below
one of this PR's own edits, in the section that describes the very file
this PR also edits. A cleanup whose thesis is that artifacts read
correctly for outside readers is incomplete on its own terms while the
README miscounts the register it points at.

## Finding 1 (R2): the README miscounts the register it points at

README.md line 38, verbatim: "RED-TEAM.md is the standing adversarial
register: ten attacks, their consequences, and the designed-in
mitigations." RED-TEAM.md carries twelve rows, R1 through R12, counted
mechanically on the branch (grep -cE '^\| R[0-9]+ \|' returns 12). R11
landed with the masked-gate incident and R12 with the producer-workflows
PR, after that sentence was written.

Attack: none required, this is authoring staleness, the same class as
PR 6's finding and in the same file.

Consequence, per R2's family applied to OSP's own claims as the PR 6
verdict applied it: the README is the credibility surface a DAAC
manager reads before deciding whether this project is careful. It sells
receipts on everything and no claim without a citation, and then
miscounts its own twelve-row register in the one sentence that
introduces it. A skeptic who scrolls to RED-TEAM.md counts the rows in
five seconds. That is a free shot handed to exactly the reader R7 says
the frame has to survive, and R2 names the failure mode: one visibly
wrong statement gets the rest dismissed wholesale.

Scope, stated plainly so the steward can overrule me: this sentence is
not changed by the diff. I am blocking on it because README.md is under
review in this PR, because the PR's stated purpose is reader-facing
accuracy in these exact files, and because the fix is one word in a
file already open. If the steward reads that as scope creep, the
correct disposition is to overrule this verdict and merge; nothing the
PR itself does is wrong.

Fix direction (the builder fixes, not the red team): make the count
true, or drop the count. The same staleness sits in agents/red-team.md
("every review walks R1 through R10"), which is outside this diff and
is the reviewer's own contract rather than a public artifact, but it is
one commit away and the steward should know it is there.

## What the diff changes, verified

### No behavior change (the core question for a wording PR)

Stronger than a read of the diff: I parsed the main and branch versions
of all three touched tools, stripped docstrings, and compared the ASTs.
tools/make_badge.py and tools/quarc_attest.py are IDENTICAL after
docstring stripping, so both files' edits are provably confined to
comments and the module docstring; comments never reach the AST at all,
which settles the quarc_attest.py question about text sitting near the
pinned-version logic. PINNED_VERSION is untouched at "1.2.8", and the
CONTENT_TYPE_MAP rebinding at line 147 is unchanged.
tools/fitness_attest.py differs by exactly one string constant, the
refusal text, and by nothing else.

Selftests, run from the repository root with exit codes read directly
and no pipe anywhere (register R11's rule, and its founding incident):
sweep_providers 0, quarc_attest 0, make_badge 0, fitness_attest 0. All
four print PASS. The ci.yml gates step invokes them exactly as I did,
including the rules_seed positional the sweeper requires.

Nothing in the tree asserts on the changed refusal string, so no test
was silently coupled to the old wording; the fitness_attest selftest
checks for the error key, not its text.

### R2, the sentences that now carry claims

- tools/fitness_attest.py line 185, the refusal a producer sees:
  "capsule derivation is not built yet" is true on this branch. Nothing
  in the repository implements capsule derivation; grep for capsule
  returns only prose about its absence. The claim is weaker than the
  old one and correctly so: "arrives with kit 15" implied a scheduled
  delivery this repository cannot promise to an outsider, and the new
  text promises nothing.
- tools/make_badge.py lines 10 to 12, the closest call in the PR.
  "Badges follow the same shape as the budget-closure badge: a receipt
  is the only thing that can produce one." As a necessary condition
  that is exactly right: emit() takes a receipt and there is no other
  input path to a badge. Read alone it invites the sufficient reading,
  which is R6's gaming attack in one sentence, since a receipt in hand
  is nowhere near enough: emit() refuses without optin/PROVIDER.md,
  refuses a receipt with no concept_id in records, and refuses unless
  quarc_attest.attest passes with max_errors=0 and skip_env_checks
  False. The two bullets directly beneath state all of that, and
  argparse prints the docstring whole, so in context the claim is
  complete and I am not blocking on it. Tightening the sentence to say
  an attested receipt would close the gap.
- data/claim-classes.yaml lines 34 to 36: "not yet available, and the
  attester refuses the tier until it is" matches attest() exactly.
- data/claim-classes.yaml lines 1 and 2: the referent is now checkable.
  data/requirements-seed.yaml does sit beside it, and it is extended by
  steward PR with provenance, since every rule carries a source with a
  verified or attributed section and MUST is blocked until the citation
  is verified. Small imprecision worth knowing: the seed is
  provenance-gated but not closed in the sense claim-classes.yaml is
  closed, where free invention silences the attester. The comparison
  survives it.
- tools/quarc_attest.py lines 47 and 147: "Reported upstream" asserts a
  completed external action, which is a different kind of claim from
  the scheduling note it replaced, so I checked it rather than taking
  it. It is true. NASA-IMPACT/pyQuARC issues 370 (version.txt at v1.3.0
  still reads 1.2.8) and 369 (NameError on CONTENT_TYPE_MAP in library
  use) were both filed 2026-08-31 at 02:59Z, and the commit making the
  claim is 14:14Z the same day. Non-blocking suggestion: cite the issue
  numbers. In a repository where every other claim names its source, a
  bare "Reported upstream" is the one assertion a reader cannot check
  from the tree, and the numbers also let a future maintainer see when
  the workaround can come out.

### R6, the reworded residual

RED-TEAM.md line 17 now reads "Same trust root as the budget-closure
badge; acceptable". The row says the same thing: the referent is
unchanged, only its name moved from private numbering to a public
description, and the claim being made about it, that this badge
inherits a trust root already accepted elsewhere rather than minting a
new one, is intact. The mitigation column is byte-identical, so nothing
about how R6 is closed has shifted.

One observation, not a finding: "the budget-closure badge" is defined
nowhere in this repository, in either place it now appears. That is a
real improvement over an opaque token, since a reader can at least tell
what kind of thing it is, but it is still an external referent with no
pointer. Naming the repository once, in either spot, would finish the
job this PR started.

### R5 and R12, nothing removed that a user needed

No warning, caveat, exit-code note, or skip-disclosure sentence is
touched by this diff. The R12 language in docs/USING.md about skipped
records counting in both output files and forcing exit 1 is intact, and
its "(register R12)" citation survives. The R5 quarantine comments in
fitness_attest.py are untouched.

On the refusal specifically: it is still honest, and it is still as
actionable as it was, which is to say it tells the producer the tier is
unavailable and that no action of theirs will make it available, which
is the true and useful thing to say. Removing the forward reference
took away nothing the producer could act on, because a kit number was
never actionable to them; it took away a promise the repository could
not keep. Non-blocking, and pre-existing rather than introduced here:
attest() returns this capsule-worded refusal for any provenance that is
not exactly hand-declared, so a typo like hand_declared gets told about
capsule derivation, and the message never names the tier that does
work. The PR 6 verdict noticed the same asymmetry from the other side,
recording the code as stronger than the claim. Now that the message has
been rewritten for outside readers anyway, naming the accepted value
would make it actionable in the way the claim-class refusal already is,
which lists the governed vocabulary when it refuses.

### R7, tone

Better for a data engineer at a data producer, clearly. Three of the
four user-visible edits replace a token that reader cannot resolve with
a statement they can act on or verify, and the refusal message is the
sharpest win: a producer whose run is refused now learns a fact about
the tool instead of a fact about our calendar. Nothing in the new prose
shifts toward enforcement; the badge docstring's new first sentence
describes restraint, and the claim-classes header still frames a closed
vocabulary as design rather than as a rule imposed on anyone. The
branch carries zero em or en dashes across md, py, yaml and yml.

One editorial note, explicitly not a finding and citing no register
row, because dressing line wrapping as a register finding is the
theater R9 exists to stop: two rewrapped paragraphs left short lines
mid-paragraph, README.md lines 33 and 34 and tools/fitness_attest.py
line 26. The README one is invisible once rendered. The docstring one
is not, since fitness_attest.py uses RawDescriptionHelpFormatter, so
the ragged line shows in --help output, which is a reader-facing
artifact of this very PR. Worth a rewrap if the builder is touching the
file for Finding 1 anyway.

### R10 and R11

R10: I ran ci.yml's credential grep verbatim, tree-wide with the same
three exclusions, and the gate passes. This diff adds no netrc, token,
Authorization, api-key or EDL pattern; the only new external reference
is a public GitHub issue subject.

R11: no selftest coverage lost. No selftest body is touched, the
fitness_attest selftest still exercises the refused tier through the
changed code path, all four selftests remain listed in ci.yml's gates
step, and all four pass unmasked.

### R9

This file is reviews/pr-9-redteam-verdict.md, bound to PR 9, round 1 of
the two-round budget. reviews/ being untouched by the PR is right:
those verdicts are the review record written under the contract that
was in force, and rewriting them would edit history rather than fix an
artifact.

## The question you asked, answered as judgment rather than a finding

Keep the R-numbers, and keep the new line that explains them.

The guide repeatedly tells a producer that a behavior is deliberate:
the SHOULD* hold does not break your build, a skipped record forces
exit 1, exit 2 means malfunction rather than finding. Strip the
register references and those become bare assertions of intent from a
project the reader has no reason to trust yet. With them, each one
points at a written adversary and a designed control, which is the R7
posture exactly: a mirror that explains itself, not an authority
issuing rules. An operator's guide that says "this is deliberate" and
declines to say why reads more like enforcement, not less.

The explainer earns its place for the same reason the rest of this PR
exists. A producer meeting "(register R2)" cold reads internal
shorthand, which is the defect under repair; one sentence converts it
into an invitation to read the register, and the register is a genuinely
good advertisement for how this project thinks.

Two refinements, both optional. The guide contains exactly two
R-numbers, R2 at line 94 and R12 at line 112, so "throughout this
guide" oversells a set of two. And a reader who lands at line 112 from
a search never passes the explainer at 94, so it may sit better where
the guide first orients the reader, near the four-tool table, than
inside the paragraph about --fail-on-must. Also worth knowing that the
rewrite moved the R2 citation out of its load-bearing sentence and into
the meta-aside beside it; the aside recovers it, so no authority is
lost, but the sentence no longer carries its own receipt.

Closest call: tools/make_badge.py's "a receipt is the only thing that
can produce one", which is true as a necessary condition and false as a
sufficient one, and which survives only because argparse prints the two
R1 and R6 refusal bullets directly beneath it in the same breath.

Round 2 on a one-word count fix should be immediate.

# Red-team verdict: PR 9 (readability cleanup), round 2

VERDICT: BLOCK

The round 1 finding is closed, and closed better than the finding
asked for. Correcting "ten" to "twelve" would have reset the same trap
for row thirteen; removing the counts retires the class. The search
that found three instances where I had named two is the right instinct
and it found one I had not: docs/USING.md's "eleven-row adversarial
register", true the day it was written and stale within a day.

I am blocking anyway, on the same class one notch wider. The commit
retired count claims about the register and left two count claims about
the badge refusals, both of them wrong right now, one in the operator's
guide and one in the very docstring this commit was rewriting.

## Round 1 finding: verified closed

All three sites read accurately with no count:

- README.md: "the standing adversarial register: attacks, their
  consequences, and the designed-in mitigation for each" matches the
  table's Attack, Consequence unmitigated and Designed-in mitigation
  columns.
- agents/red-team.md: "every review walks every row" is both accurate
  and self-maintaining, and it is what I did.
- docs/USING.md: "RED-TEAM.md is the adversarial register every change
  is reviewed against" holds.

Swept the tree for survivors, all file types outside reviews/: no count
of rows, attacks, entries or findings about the register remains, and
RED-TEAM.md's own preamble never carried one. reviews/ carries several,
including my own round 1 "twelve rows" and PR 4's and PR 7's "eleven
rows", and that is correct: a verdict is a dated record of what was
true when the review ran, not a standing description that can go stale.
Leaving reviews/ untouched is right for the same reason.

## Finding 2 (R2): the badge refusals are counted, and the count is wrong

Two sites, one class, the class this commit just retired elsewhere:

- tools/make_badge.py line 14: "Two refusals bind it, register R1 and
  R6:" followed by two bullets. This sentence was rewritten by this
  commit; the stale count rode along into the new prose.
- docs/USING.md line 187: "Two refusals guard this, both proven by the
  selftest: no badge without a written opt-in at optin/POCLOUD.md, and
  no badge without a FULL attest PASS of the receipt in this
  environment."

emit() has three refusal branches, at lines 40, 48 and 54: no written
opt-in (R1), no registered records in the receipt (R6), and full attest
did not PASS (R6). I ran the selftest and it prints all three, so
USING.md's "both proven by the selftest" is doubly wrong: the selftest
proves three, and the one it omits is the one the selftest was extended
to cover.

Attack: none required, authoring staleness again. git log -S dates it
exactly: commit 6a9345f, the builder's response to PR 8 round 1, added
the registered-records refusal. Before that there were two, which is
why PR 4's verdict records "make_badge's two proven refusals" as
verified fact. It was true when written. It stopped being true when the
producer path landed, and nothing swept back over the prose that
counted it.

Consequence, and this is why it is worth a block rather than a note:
docs/USING.md now contradicts itself. Its capability table tells a
producer that a draft record on disk gets no badge, because badges bind
to a registered revision. Its badge section tells the same producer
that two refusals guard the path and neither of them is that one. A
producer with a clean local record reads the section, concludes that a
written opt-in plus a passing attest is all that stands between them
and a badge, and finds out otherwise from a refusal message. That is
the R2 failure mode aimed at our own guide: the artifact claims
something the code does not do, in the document whose whole purpose is
telling an outsider what the code does. It is also, precisely, a
statement that was accurate when written and went stale as the thing it
counted grew, which is the finding the steward just generalized into
doctrine two paragraphs of prose away.

Fix direction (the builder fixes, not the red team): the doctrine
adopted this round answers it. Describe the refusals instead of
counting them. USING.md additionally needs the third one named, because
its own table already promises that behavior and the badge section is
where a producer will look for it.

## The round 1 notes, each verified applied

- tools/quarc_attest.py: the two comments now name
  github.com/NASA-IMPACT/pyQuARC issues 370 and 369, and the mapping is
  right way round. I pulled both issue titles: 370 is "version.txt at
  tag v1.3.0 still reads 1.2.8", which is the comment on
  PINNED_VERSION, and 369 is the CONTENT_TYPE_MAP NameError, which is
  the comment on the rebinding in run(). The claim is now checkable
  from the tree, which was the point.
- tools/make_badge.py: the referent is named and it resolves. I checked
  github.com/open-science-pillars/ecco-budget-badge from here: public,
  and its description ("Checkable ECCO budget closure: the attested
  heat budget's portable attester, sanctioned computation, and CI
  badge") supports the shared-trust-root claim the R6 residual makes.
  A pointer that resolves is worth more than the one I asked for.
- "nothing but an attested receipt can produce one, and a receipt alone
  is not enough" kills the sufficient reading exactly. My round 1
  closest call is closed.
- docs/USING.md: "here and below" retires the oversell for a set of
  two, and the R12 gloss at line 111 now self-resolves for a reader who
  arrives there by search rather than by reading forward. Both notes
  closed.
- tools/fitness_attest.py: the docstring paragraph is rewrapped and I
  confirmed it in --help output, where the lines now run 64 to 68
  characters with no short line mid-paragraph.

## Editorial defect introduced by the fix, not a register finding

tools/quarc_attest.py line 149 sits at column 0, inside the body of
run(), where the continuation of an indented comment block should be:

    # pinned tag stays pinned. Reported upstream as
# github.com/NASA-IMPACT/pyQuARC issue 369.

It is the only column-0 comment inside any function body in the file. I
checked the consequences rather than assuming: Python exempts comment
lines from indentation entirely, the file parses, the AST is identical
to main after docstring stripping, and the selftest passes, so there is
no behavior risk whatsoever. Nothing in CI will ever catch it, since
the gates are selftests and greps, not a linter. It is a visible seam
in source, of the same family as the wrap I noted in round 1, in a
comment added to fix a readability note. Worth the one-line fix while
the file is open, and I am not counting it toward the block.

## Register walk, round 2

- R2: Finding 2 above. Every other claim touched by this commit
  verified against the running code: the three register descriptions,
  the two upstream issue references, the badge repo pointer, the badge
  necessity-and-insufficiency sentence.
- R5, R12: nothing removed. The R12 skip disclosure in USING.md is
  intact and its citation now carries its own gloss; the R5 quarantine
  comments in fitness_attest.py are untouched.
- R6: RED-TEAM.md is unchanged by this commit, so the residual verified
  in round 1 stands, and the badge docstring now points at the repo
  whose trust root the residual invokes.
- R7: better again. The register is now described by what it is rather
  than how big it is, which reads as an invitation rather than a
  credential, and agents/red-team.md's "every row" removes an internal
  range from the one artifact that defines how this project reviews
  itself.
- R9: this is round 2 of two, appended to reviews/pr-9-redteam-verdict.
  md, bound to PR 9.
- R10: ci.yml's credential grep run verbatim, tree-wide, exits clean.
  The new external references are two public issue numbers and one
  public repo path; none matches a pattern.
- R11: no selftest coverage lost, no selftest body touched. All four
  run unmasked with exit codes read directly: sweep_providers 0,
  quarc_attest 0, make_badge 0, fitness_attest 0. AST comparison
  against main, docstrings stripped: make_badge and quarc_attest
  identical, fitness_attest differing by the single refusal string. The
  wording PR remains a wording PR.

## Disposition, since the round budget is now spent

Per R9 this goes to the steward with both positions, and mine is
narrow. Everything under review is verified, twice, and the PR is a
clear improvement on what it set out to improve. One sentence in the
operator's guide currently tells a data producer something the code
will refuse, and one sentence in a docstring miscounts what it
enumerates. Both are two-line fixes and neither needs another red-team
round: the fix is verifiable by reading it against emit()'s three
REFUSED branches. My recommendation is to fix those two sentences and
merge on the steward's own signature rather than convening a round 3,
which the contract does not provide.

The steward's position, recorded fairly: the round 1 blocker was taken
rather than overruled, the class was searched rather than the instance
patched, and the fix chosen retires the trap instead of resetting it.
That is a better response than the finding deserved, and it is the
reason a second instance of the class was findable at all.

Closest call: whether to approve and note Finding 2 instead of
blocking. It blocks because it is the same class I blocked on in round
1, and applying that standard to a pre-existing README sentence but not
to a rewritten docstring and a self-contradicting operator's guide
would make round 1 arbitrary rather than principled.
