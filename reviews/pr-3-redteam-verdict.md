# Red-team verdict: PR 3 (sweep window entry), round 1

VERDICT: BLOCK

Verified before findings: the report's numbers match the aggregate exactly (req-doi 975 of 982, the other four rules unanimous at 982); all 7 DOI misses were re-verified live against CMR umm_json during this review and every one is a conformant MissingReason "Not Applicable" declaration with an explanation, so the report's zero-fixes stance is factually sound; the aggregate carries the non-affiliation line; and holding the provider-named aggregate until optin/POCLOUD.md exists is the policy-true call, consistent with the publication policy's opt-in tier, with PR 1 round 1 finding 3, and with sweep.yml's own gate (I confirmed optin/ still does not exist). Tone across both drafts holds the mirror frame: offers not findings, the leading offer is that nothing needs fixing, the queued refinement is aimed at our own sweeper, and the interim delivery to the OSP steward is disclosed honestly.

Findings:

1. R1. docs/policy-log.md, the one artifact this session publishes, ends its entry with "Finding class summary, rule level only: one SHOULD rule short of unanimity, every miss a conformant schema declaration, zero fixes requested of the provider". That sentence is provider-named result content published during the 30-day window and before any recorded opt-in; the policy's only default-public tier is cross-archive statistics, and the aggregate is being held precisely because provider-named results await opt-in, so publishing a coarse summary of the held content is the same leak at lower resolution. The pattern hazard is worse than this instance: if window entries carry a favorable summary when results are good, a future entry without one discloses bad results by omission, so the log must record event metadata only (sweep ran, scale, private delivery, window dates, aggregate held and why, observatory-side work queued). Strike or generalize the sentence through "zero fixes requested of the provider"; the sweeper-refinement clause may stay, since it is about our side.

2. R1. sweeps/POCLOUD-2026-08-30-report-PRIVATE.md's header reads "[PRIVATE until the policy window closes]", inherited from templates/provider-report.md. The window governs when public reference to per-provider detail may begin; it never converts this report to public wholesale, because the report contains per-collection content (the seven named collections with their declared reasons, the ECCO exemplar receipt detail) that the policy gates on written opt-in regardless of the window. The header should say the report is private and publishes only under recorded opt-in; the template carries the same wording and should be corrected in the same pass so the next report does not inherit the hazard.

Notes, not findings: one of the seven explanations differs from the report's parenthetical (ASCATA-L2-Coastal declares "Native record does not contain a DOI." rather than producer ownership), so soften the parenthetical to "with explanations, chiefly data producer DOI ownership"; and the referenced pyQuARC receipt 8eec9055 is not in the tree, so make sure the receipt file travels with the private delivery package the way footnote r1 promises the aggregate and detail do.

Cleared and held, explicitly:
- docs/policy-log.md: NOT cleared for commit until finding 1 is fixed; it is the only file intended to go public and the only blocker.
- sweeps/POCLOUD-2026-08-30-report-PRIVATE.md: cleared for private delivery to the provider side once the finding 2 header is corrected; tone and content otherwise pass R7.
- sweeps/POCLOUD-2026-08-30-detail-PRIVATE.md: cleared for private delivery as the machine output accompanying the report; its "failing" section heading is acceptable in the private tier and is already addressed by the queued three-state doi-present refinement.
- sweeps/POCLOUD-2026-08-30-aggregate.txt: correctly held; keep it out of git and unpublished until optin/POCLOUD.md lands, at which point it publishes as-is.

Round 2 verifies the two fixes; both are single-line wording changes.

# Red-team verdict: PR 3 (sweep window entry), round 2

VERDICT: APPROVE

Both round 1 findings verified fixed in the working tree, plus both notes:

Finding 1 (R1): the finding-summary sentence is struck from docs/policy-log.md and replaced with an explicit format rule stating the log records event metadata only (what ran, at what scale, what was delivered privately, the window dates, what is held and why) with result content of any resolution waiting for the tier that covers it. The entry now carries no provider-named result content, and the format rule closes the omission channel for future entries. The observatory-side clause remains, as round 1 allowed.

Finding 2 (R1): the report header now reads "[PRIVATE; publishes only under recorded provider opt-in]" and templates/provider-report.md carries the identical correction, so no future report inherits the window-close publication hazard.

Note 1: the parenthetical is softened to "chiefly data producer DOI ownership" with the one native-record wording acknowledged, matching what I verified live against CMR in round 1.

Note 2: the exemplar receipt now travels in the package as sweeps/POCLOUD-2026-08-30-receipt-8eec9055-PRIVATE.json and footnote r1 names it. I attested it end to end during this round: PASS with the pinned version, the ruleset hash verified against this environment, the record revision (C1991543732-POCLOUD revision 23) confirmed still current at CMR via check A4, and errors 9 at the stated bound. Its PRIVATE filename keeps it behind both publishing belts.

Cleared for commit: docs/policy-log.md, templates/provider-report.md, and this verdict file (reviews/pr-3-redteam-verdict.md). Cleared for private delivery only, never committed: sweeps/POCLOUD-2026-08-30-report-PRIVATE.md, sweeps/POCLOUD-2026-08-30-detail-PRIVATE.md, sweeps/POCLOUD-2026-08-30-receipt-8eec9055-PRIVATE.json. Held: sweeps/POCLOUD-2026-08-30-aggregate.txt stays out of git and unpublished until optin/POCLOUD.md lands, then publishes as-is.

Non-blocking note: the repo has no .gitignore, so keeping the private files out of git is procedural rather than structural; an entry ignoring sweeps/ (with the scheduled workflow force-adding the aggregate it is allowed to publish) would make the private tier hold by construction.

Closest call: the log entry's work-queue clause names the three-state doi-present refinement, which permits a weak inference that this sweep encountered DOI missing-reason states at the named provider, acceptable here because the inferable state is a conformant schema declaration and the clause records the observatory's own queue, with the standing convention that future work-queue clauses stay generic whenever the inferable state would be a deficiency rather than a conformant declaration.
