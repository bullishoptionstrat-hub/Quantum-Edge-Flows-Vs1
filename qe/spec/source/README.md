# God's Plan source material

## Status: the source document is missing

Decision A2-00 (option 1, approved 2026-10-07) says the God's Plan source document is committed here **as-is** and formalized into `gp-1.0.0`. That document is the "uploaded design" that the two original master prompts and the design review were written from. **It is not in this repository and was never supplied to the agent.** It cannot be reconstructed from memory, and nothing here pretends to be it.

**Operator action:** add the original file to this folder unchanged (for example `qe/spec/source/GODS_PLAN_SOURCE.md`) and record its sha256 in `qe/DECISIONS.md`. Every `AMB-*` entry in `qe/spec/AMBIGUITY_REGISTER.csv` then gets re-checked against it. Where the document and the draft disagree, the document wins and the spec version is bumped (directive A5.10).

## What the draft was built from instead

`GP_SOURCE_EXCERPTS.md` quotes, verbatim, the statements about God's Plan semantics in the operator-supplied material in this session: the design review and the two earlier master prompts that the user pasted on 2026-09-23. These are second-hand descriptions of the source document, not the document itself. Evidence level: L0/L1 claims about the intended design (directive A3).

The excerpts contain **no numeric thresholds**: no tick counts, bar counts, ATR multiples, or time windows. Every number in `qe/spec/params/gp-1.0.0-draft.1.json` is therefore a proposal, recorded as an ambiguity awaiting approval.
