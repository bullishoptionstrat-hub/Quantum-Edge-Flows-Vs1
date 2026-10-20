# God's Plan semantics as described in operator-supplied material

Verbatim excerpts from the material the operator pasted into the session on 2026-09-23: a design review of the original God's Plan document plus two master prompts written from it. **These describe the source document; they are not the source document** (see `README.md`). Line numbers refer to that pasted message. The material is kept out of the repository in full because most of it is process instruction, not strategy semantics.

The spec cites these as `S-xx`. None of them contains a numeric threshold.

## S-01: The sequence and the fail-closed principle (lines 5–5)

> The strongest part of the uploaded design is its core philosophy: God’s Plan is a sequential, fail-closed decision process, not a confluence score. The intended chain is explicit: context → liquidity → sweep → reclaim → displacement → retest → confirmation → SMT → risk/invalidation → ≥2R → one attempt. Missing mandatory evidence means WAIT or BLOCKED, not “lower confidence.”

## S-02: Liquidity is a stateful object (lines 1320–1333)

> Liquidity must be represented as a stateful domain object, not merely a price.
>
> It must include:
>
> liquidity_id
> origin
> timeframe
> lower/upper boundary
> tolerance
> formation event
> formed_at
> available_at
> active/swept/reclaimed/consumed/expired state
> evidence references.

## S-03: Sweep (lines 1336–1345)

> A touch is not a sweep.
>
> Define:
>
> required excursion through boundary;
> tick-based tolerance;
> permissible duration;
> post-sweep classification;
> session restrictions;
> data-health requirements.

## S-04: Reclaim classes; a failed reclaim is not a reversal (lines 1348–1357)

> Classify:
>
> CONFIRMED
> FAILED
> AMBIGUOUS
> ACCEPTED_BEYOND_LEVEL
>
> Do not convert a failed bullish reclaim automatically into a bearish trade.
>
> A bearish sequence must independently form.

## S-05: Reclaim must be measurable (second master prompt) (lines 3681–3697)

> Reclaim definition must be measurable.
>
> Possible ingredients:
>
> close back through liquidity boundary;
> number of bars/events;
> percentage/tick recovery;
> maximum elapsed time;
> structure reference.
>
> A failed bullish reclaim is:
>
> not automatically a short.
>
> It invalidates or terminates the bullish lineage.
>
> A new bearish thesis requires new canonical evidence.

## S-06: Displacement (lines 1361–1373)

> Define using measurable evidence such as:
>
> range multiple;
> body/range ratio;
> close location;
> structural break;
> imbalance creation where required;
> relative volume where supported;
> immediate-failure rules.
>
> Retain raw measurements.
>
> Do not store only a label.

## S-07: Zones (lines 1377–1384)

> Version the definitions of:
>
> FVG
> iFVG
> order block
> breaker block
> displacement origin
> reclaimed liquidity zone.

## S-08: Retest (lines 1387–1398)

> Retest must occur after displacement.
>
> No first-touch trade.
>
> Define:
>
> eligible zone;
> depth;
> timeout;
> invalidation;
> minimum elapsed events;
> mitigation semantics.

## S-09: Retest is not permission (second master prompt) (lines 3793–3795)

> Retest itself is not permission.
>
> Confirmation still follows.

## S-10: Confirmation (lines 1401–1408)

> Define testable confirmation families:
>
> engulfing;
> rejection;
> lower-timeframe structure shift;
> permitted order-flow reversal.
>
> No phrase such as “looks strong” is legal in the deterministic engine.

## S-11: Fail-closed invariant (lines 1456–1476)

> Mandatory uncertainty cannot authorize risk.
>
> If mandatory evidence is:
>
> absent;
> stale;
> corrupt;
> ambiguous;
> inconsistent;
> misaligned;
> unavailable;
>
> the result is not reduced confidence.
>
> The result is:
>
> BLOCKED
>
> or, where the sequence has not yet completed:
>
> WAIT.

## S-12: SMT (lines 1490–1528)

> Create a dedicated SMT module.
>
> Primary pairs initially:
>
> ES ↔ NQ
> SPY ↔ QQQ where explicitly enabled
>
> Do not reuse reference levels blindly across markets.
>
> SMT must carry:
>
> primary instrument;
> paired instrument;
> primary reference;
> paired reference;
> reference formation times;
> event timestamps;
> feed timestamps;
> freshness;
> alignment delta;
> primary break state;
> paired break state;
> divergence direction;
> reason code.
>
> Canonical states:
>
> CONFIRMED
> DENIED
> UNCLEAR
> UNAVAILABLE
> STALE
> MISALIGNED
>
> For SMT-dependent setups:
>
> anything other than CONFIRMED blocks authorization.
>
> Do not replace this enum with a probability score.

## S-13: SMT must compare structurally comparable references (second master prompt) (lines 3830–3830)

> Never compare unrelated swing IDs merely because timestamps are near each other.

## S-14: Setup lineage and one attempt (lines 1532–1560)

> A trade UUID is not a setup lineage.
>
> Implement:
>
> SetupLineage
>
> with deterministic identity derived from canonical fields such as:
>
> ruleset;
> instrument;
> direction;
> setup family;
> liquidity object;
> sweep event;
> session.
>
> Persist:
>
> lineage ID;
> attempt count;
> status;
> terminal outcome.
>
> Invariant:
>
> attempt_count >= 1
> → another authorization from the same lineage is forbidden.
>
> Restarting the process, receiving a new Pine alert, recalculating a score, changing AI confidence or receiving a new candle must not circumvent one-attempt policy.
