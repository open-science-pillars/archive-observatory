# Red-team verdict: PR 2 (seed classes), round 1

VERDICT: APPROVE

Register IDs checked against the seed-classes diff (commit 26a5946), which touches only data/requirements-seed.yaml and the sweeper selftest:

R2: req-doi drops to SHOULD with the librarian evidence pointer naming the failed MUST promotion and the concept path; the temporal and spatial MUSTs upgrade their sources to the fetched UMM-C v1.18.4 citation, which I verified independently by refetching the schema (TemporalExtents and SpatialExtent are in the top-level required array). The round 1 demotion gate in load_rules stays exercised: the selftest constructs a synthetic MUST rule with an unverified source section and asserts it loads as SHOULD*, while asserting req-doi loads as plain SHOULD. Selftest run under uv run: PASS, with req-doi printing as SHOULD and no held-at-SHOULD footnote, which is correct since no pending MUST remains in the real seed.

R7: the new req-doi statement explains the MissingReason ground honestly and the aggregate output retains the non-affiliation line, verified in the selftest output.

R10: the exact CI grep re-run on this branch exits clean; the new seed text introduces no credential patterns.

R1, R3, R4, R5, R6, R8: untouched by this diff (no changes to workflows, pins, network paths, counting, receipts, or publication surfaces), confirmed against the full diff. R9: satisfied by this file landing at reviews/pr-2-redteam-verdict.md per the bound gate.

Closest call: the seed's evidence pointer names esdis/requirements/doi-registered.md, which exists today only on the esdis-bundle branch of nasa-daac-knowledge (PR 60), so this PR should merge together with or after that one to keep the pointer from dangling; a trivial tidiness note, not a finding, is that the selftest's synthetic rule file is written with delete=False and never removed.
