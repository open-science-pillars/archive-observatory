# Red-team verdict: PR 8 (label rendering fix), independent pass

VERDICT: BLOCK

Scope: commit 55c8c14 only, not the whole PR. This is a steward
convened independent pass; the contract's two round budget was spent at
round 2, so this verdict is a third opinion for the steward rather than
a round 3 under agents/red-team.md. Every claim below was produced by
running the shipped command against crafted files in a temporary
directory with --out-dir and inspecting or rendering what landed, never
by reading the builder's account.

## What the commit genuinely closes, re-attacked and confirmed

Verified against a 19 record hostile corpus rendered through both a
CommonMark renderer and cmark-gfm, which is what GitHub uses:

- Round 1's break out is dead. The backtick, newline, forged heading
  and the agent addressed HTML comment all render as one inert quoted
  line of escapes. Zero forged headings, zero comment markers, zero
  backticks in the rendered HTML.
- Round 2's beacon is dead. The image and link vectors produce zero
  img elements and zero bracket syntax links. Bang, bracket, paren,
  colon and slash are all escaped. There is no auto loading image
  vector left, which was the sharpest edge of the round 2 finding.
- Homoglyphs are closed as a side effect and worth the credit: a
  Cyrillic imitation renders as visible escapes, not the Latin name it
  imitates.
- The escaping is injective, because backslash is itself outside
  LABEL_SAFE, so a label cannot forge another label's escape form.
- Truncation cannot split an escape: the bound is applied to raw code
  points before escaping.
- Real ShortNames pass through unchanged and readable.

The direction of travel is right and the allowlist is the correct
shape. What follows is what the allowlist still lets through and what
the second half of the commit broke.

## Finding 7 (R5): a live link still forms from allowlisted characters alone

LABEL_SAFE permits space, letters, digits, dot and hyphen. GFM's
extended www autolink needs nothing more. Verified on cmark-gfm,
GitHub's own renderer, at default options: a ShortName of
"PODAAC www.podaac-security-notice.com" renders with an anchor element
pointing at the attacker's host. Under markdown-it with linkify
enabled, which is what many document viewers use, even a bare
"contact.us.evil.com" autolinks with no space and no www at all. The
literal double quotes around the label do not protect it; they are
prose, not a code span.

Attack: a record whose ShortName ends in a space and a domain the
attacker controls, chosen to read as a NASA or PO.DAAC notice. The
private detail file the observatory delivers then carries a clickable
link to that host, inside a document that opens with the OSP non
affiliation line, in front of an archive contact.

Consequence: the class round 2 blocked on, an attacker chosen
destination rendering as markup in a privately delivered report, is
open again. The commit's own docstring states that no markdown or HTML
construct can be formed at all. That is false on the renderer GitHub
uses, and the recurrence of a fix whose description overstates it is
worth naming as much as the vector.

Fix direction: restore the code span wrapping around the already
allowlisted label. Verified on both renderers that the wrap makes it
inert; the backtick is already escaped by the allowlist, so nothing
can break out of the span.

## Finding 8 (R5): underscore emphasis at the quote boundary rewrites the label

The wrapping quote is punctuation, which is what CommonMark's
intraword underscore rule needs to let a delimiter run open and close.
A leading and trailing underscore renders the label in emphasis with
the underscores consumed, so the rendered label is not the record's
ShortName. Interior underscores in real ShortNames stay inert. Lower
severity than Finding 7, and the same code span fix closes it.

## Finding 9 (R11, and proposed new register row R12): the phantom guard silently drops real records and turns the MUST gate green

The added skip catches the intended phantom case but cannot
distinguish it from a UMM-C draft that simply omits ShortName, which is
the most likely thing wrong with a producer's draft. Verified, same
file, both commits: the parent reported 2 swept, 50 percent, exit 1;
this commit reports 1 swept, 100.0 percent, exit 0. The only trace is
one line on stderr, in neither artifact.

Consequence, per R11's row: a gate that reports green over content it
did not examine is decoration, and this one does it while printing a
percentage that reads as authority. Trading a visible mislabeled entry
for an invisible omission that flips a gate is worse than the position
the round 2 note described.

Proposed register row:

    R12 | Silent input dropping: a crafted or malformed record is
        skipped before the rules run and the skip is disclosed only on
        stderr | The report states a swept count and a pass percentage
        over a set that silently shrank, and --fail-on-must exits 0
        over unchecked content | Skips are counted and named in the
        artifact itself, not only on stderr, and a run that skipped
        anything cannot exit 0 under --fail-on-must | A producer can
        still hand over a file with nothing in it; that is visible in
        the count

## Register walk

R1 unchanged and correct; LOCAL output still carries the PRIVATE suffix
on both files, which limits Findings 7 and 8 to the named provider
rather than the public tier. R2 touched by Finding 9: a percentage over
a shrunken set is the false authority failure mode, arriving through
the counting path. R4 not touched. R5 covers Findings 7, 8 and 9. R6
not touched. R7 clean, with one mirror quality note: a legitimate non
ASCII ShortName now renders as escape soup in a report delivered to the
provider who owns that name, which the code span fix would also
resolve. R9 satisfied. R10 clean, verified with ci.yml's exact grep.
R11: the selftest runs unmasked and four sabotages each failed it at
exit 1; the gap is what the assertions test, since asserting the
absence of specific characters cannot catch a construct built only from
allowed characters. A property level assertion is what would have
caught Finding 7.

## Notes, none blocking

The length bound is on input code points, not rendered width, so the
bound is looser than the commit message implies though still a bound.
The truncation marker is forgeable and collides with a label ending in
the same literal text. The phantom class is narrowed, not closed: an
empty umm envelope is still counted as one failing collection.

## For the steward, both positions

The case for shipping: the allowlist is the right shape, the auto
loading beacon is genuinely gone, round 1's injection is gone, and the
remaining rendering vectors land only in a file delivered privately to
one named provider.

The case for holding, which is the red team's position: Finding 7 puts
an attacker chosen clickable destination back into that same file using
only letters, a dot and a space, and Finding 9 is a gate going green
over unchecked content, which under R11 is the one failure this project
has already decided it will not accept.

Closest call: Finding 8 alone would not have blocked and Finding 7
alone would have been arguable given the beacon is closed and the file
is private, but Finding 9 is a gate regression introduced by this
commit.
