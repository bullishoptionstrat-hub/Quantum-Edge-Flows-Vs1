# God's Plan specification: `gp-1.0.0-draft.1`

**Status: DRAFT. Not frozen. Not authoritative.** Every parameter and every definition choice below is **PROPOSED**. The spec becomes `gp-1.0.0` only when the operator approves each open entry in `AMBIGUITY_REGISTER.csv` (directive B3, tier A2). Until then, no code may treat it as production authority.

- Parameters: `qe/spec/params/gp-1.0.0-draft.1.json` (values cited here as `P-…`).
- Reason codes: `qe/spec/REASON_CODES.yaml` (closed enumeration, directive D5).
- Golden fixtures: `qe/spec/fixtures/GF-*.json` (directive E2), written from this text, not from code.
- Requirement trace: `qe/spec/GP_REQUIREMENTS_TRACE.csv`.

## 0. Source basis and its limits

The operator chose option 1 for A2-00: formalize from the God's Plan source document. **That document is not in this repository and was not supplied in the session.** `qe/spec/source/README.md` records what is missing and where it must go. This draft is built from three inputs, in this order of authority:

1. **The God's Plan sequence as quoted in operator-supplied material** (`qe/spec/source/GP_SOURCE_EXCERPTS.md`, items S-01 to S-14): context → liquidity → sweep → reclaim → displacement → retest → confirmation → SMT → risk/invalidation → ≥2R → one attempt; plus the qualitative rules ("a touch is not a sweep", "retest must occur after displacement", and so on).
2. **The directive** (QEGP-MASTER-4.0 D3–D8): event model, the two state machines, reason codes, decision record, fail-closed rules.
3. **Prior art in this repository** (`qe/audit/GODS_PLAN_RULE_DIVERGENCE_MATRIX.csv`), used only as candidate definitions in the ambiguity register, never as authority.

Every place where (1) gives a word but no number, this draft proposes a number and records the choice as an ambiguity. When the source document arrives, each `AMB-*` entry is re-checked against it. Where the document disagrees, the document wins and the spec version is bumped.

## 1. Conventions

- **GP-REQ-001** Prices are integer ticks of the traded contract (`qe/core/ticks.py`). Floats are rejected.
- **GP-REQ-002** The strategy evaluates only `BarClosed` events of the setup timeframe `P-TF-SETUP-S`, plus `ClockTick` events for staleness. Nothing is decided inside a forming bar.
- **GP-REQ-003** A fact derived from bar `b` may influence a decision only at a time ≥ `b.available_at_ns`. A liquidity object is eligible only for bars with `bar_start_ns ≥ object.available_at_ns`.
- **GP-REQ-004** All ratios are exact rationals (`fractions.Fraction`). No threshold comparison may be decided by floating-point rounding.
- **GP-REQ-005** Bearish rules are the exact mirror of bullish rules. The mirror transform maps a price `p` to `M − p` for a constant `M`, and a bar `(o, h, l, c)` to `(M−o, M−l, M−h, M−c)`. It swaps sell-side ↔ buy-side, `low` ↔ `high`, `min` ↔ `max`, `<` ↔ `>`, and LONG ↔ SHORT. The reducer must be mirror-equivariant: mirroring every input mirrors every output and leaves reason codes and bar indices unchanged. Sections 7–15 are written for the bullish (LONG) case only.
- **GP-REQ-006** Per-bar evaluation order for an active lineage: (1) data-quality and contract checks, (2) session-end and news-blackout checks, (3) invalidation checks, (4) progress checks. Several progress transitions may happen on one bar when each stage's eligibility window allows it (sections 8–15 state which).
- **GP-REQ-007** Control flow never branches on free text. Every terminal or blocking outcome carries exactly one reason code from `REASON_CODES.yaml`.

## 2. Inputs

| Input | Content |
|---|---|
| Primary feed | `BarClosed` events for one contract of the traded instrument |
| Pair feed | `BarClosed` events for the SMT pair (section 14) |
| Liquidity objects | `LiquidityCreated` events (section 6) |
| Session calendar | setup window per session date, timezone `P-SESSION-TZ` |
| News calendar | list of scheduled events; **absence of the calendar is a blocking condition** (GP-REQ-014) |
| Roll metadata | per contract: `roll_date`; **absence is a blocking condition** (GP-REQ-013) |
| Lineage store | prior lineages and attempt counts (section 16) |
| Instrument registry | `qe/config/instruments.json` |
| Cost model | `P-COST-*` per instrument |
| `ClockTick` | the current time, so staleness is detectable when bars stop arriving |

## 3. Context

- **GP-REQ-010** Context is valid at bar `b` only if all the following hold. When a sweep (section 7) happens while context is invalid, no lineage opens. A rejection is recorded with the first failing code in this order, and the liquidity object becomes `CONSUMED`:
  1. the instrument is in `P-AUTHORIZED-INSTRUMENTS`, else `GP_BLOCK_INSTRUMENT_NOT_AUTHORIZED`;
  2. roll metadata exists for `b.contract_id`, else `GP_BLOCK_ROLL_METADATA_MISSING`;
  3. the session date is not inside the roll blackout (GP-REQ-013), else `GP_BLOCK_ROLL_WINDOW`;
  4. a news calendar is present, else `GP_BLOCK_NEWS_CALENDAR_MISSING`;
  5. `[b.bar_start, b.event_time)` does not intersect any `[event − P-NEWS-BLACKOUT-MIN, event + P-NEWS-BLACKOUT-MIN]`, else `GP_BLOCK_NEWS_BLACKOUT`;
  6. `b.bar_start` falls inside the session's setup window `P-SETUP-WINDOW` (start inclusive, end exclusive, local time `P-SESSION-TZ`), else `GP_WAIT_OUTSIDE_SETUP_WINDOW`;
  7. at least `P-ATR-N` closed bars of the same contract precede `b`, else `GP_WAIT_INSUFFICIENT_HISTORY`;
  8. the primary feed health is `HEALTHY` (`qe/core/data_quality.py`, policy `P-DQ-*`), else `DQ_BLOCK_PRIMARY_<GAPPED|STALE|UNKNOWN>`.
- **GP-REQ-011** A liquidity object penetrated while context is invalid is consumed. It can never seed a lineage later in the session.
- **GP-REQ-012** Setup window `P-SETUP-WINDOW` and timezone `P-SESSION-TZ` come from the parameters. Session dates are evaluated in `P-SESSION-TZ`.
- **GP-REQ-013** Roll blackout: blocked if `session_date ≥ roll_date`, or if `roll_date` falls within the next `P-ROLL-BLACKOUT-SESSIONS` weekday sessions after `session_date`. An exchange-holiday calendar that refines "weekday sessions" is an open item (AMB-031).
- **GP-REQ-014** A missing news calendar blocks every setup. "No events today" must be expressed as an empty calendar, never as a missing one.
- **GP-REQ-015** An active lineage is `BLOCKED` with `GP_BLOCK_NEWS_BLACKOUT` at the first bar that intersects a blackout interval.
- **GP-REQ-016** An active lineage that has not reached `STRATEGY_AUTHORIZED` is `EXPIRED` with `GP_EXPIRED_SESSION_END` at the first bar whose `bar_start` is at or after the setup-window end.

## 4. Average true range

- **GP-REQ-020** `TR(x) = max(high − low, |high − prev_close|, |low − prev_close|)`, where `prev_close` is the close of the bar immediately before `x` in the same contract's feed. If there is no such bar, `TR(x) = high − low`.
- **GP-REQ-021** `ATR(b) = (1/N) · Σ TR(x)` over the `N = P-ATR-N` closed bars immediately preceding `b` in the same contract (bar `b` itself is excluded). It is an exact `Fraction` in ticks. If fewer than `N` bars precede `b`, ATR is undefined and context is invalid (GP-REQ-010 item 7).

## 5. Swings

- **GP-REQ-030** Bar `i` is a swing high with strength `k = P-SWING-K` iff `high[i] > high[j]` for every `j` in `[i−k, i−1]` and `high[i] ≥ high[j]` for every `j` in `[i+1, i+k]`. The left side is strict and the right side is not, so among equal highs the earliest bar is the pivot. A swing low is the mirror.
- **GP-REQ-031** A swing's `formed_at` is `event_time(i)`. Its `available_at` is `available_at(i+k)`, the close of the k-th confirming bar.
- **GP-REQ-032** No swing is formed if any bar in `[i−k, i+k]` is missing, or if the feed was not `HEALTHY` for any of them.

## 6. Liquidity objects

- **GP-REQ-040** A liquidity object is a stateful record: `liquidity_id, instrument_root, contract_id, type, side (BUY_SIDE | SELL_SIDE), level (ticks), session_date, formed_at_ns, available_at_ns, state (ACTIVE | CONSUMED | EXPIRED), consumed_cause, evidence_ids`. It is never a bare price.
- **GP-REQ-041** Eligible types in this draft (`P-LIQ-TYPES`):
  - `PRIOR_RTH_HIGH` / `PRIOR_RTH_LOW`: the extreme of the previous session's regular-hours bars. It becomes available at the `available_at` of that session's last regular-hours bar.
  - `OVERNIGHT_HIGH` / `OVERNIGHT_LOW`: the extreme of the bars from the previous regular-hours close to the current regular-hours open. It becomes available at the `available_at` of the last bar before the open.
  - `SWING_K_HIGH` / `SWING_K_LOW`: swings from section 5 formed in the current session.

  `liquidity_id = "<root>:<type>:<session_date>"` for session types, and `"<root>:<type>:<pivot bar_start_ns>"` for swings.
- **GP-REQ-042** A liquidity object stays `ACTIVE` until it is consumed (section 7) or the setup window of its session ends (`EXPIRED`).
- **GP-REQ-043** Equal highs/lows, internal versus external liquidity, and "engineered" liquidity are not separate types in this draft (AMB-008).

## 7. Sweep (LONG case: sell-side level `L`)

For each `ACTIVE` sell-side object `L` and each closed bar `b` with `b.bar_start ≥ L.available_at`:

- **GP-REQ-050** `pen(b) = L.level − low(b)`. If `pen ≤ 0`, nothing happens. **A touch (`pen = 0`) is not a sweep.**
- **GP-REQ-051** If `0 < pen < P-SWEEP-MIN-PEN-TICKS`, nothing happens and `L` stays `ACTIVE` (insufficient penetration).
- **GP-REQ-052** If `pen ≥ P-SWEEP-MIN-PEN-TICKS`, `L` becomes `CONSUMED` whatever happens next. Then:
  - if context is invalid (GP-REQ-010), record the rejection and stop;
  - otherwise snapshot `ATR_sweep = ATR(b)`. If `pen > P-SWEEP-MAX-PEN-ATR · ATR_sweep`, record the rejection `GP_INVALID_SWEEP_TOO_DEEP` and open no lineage;
  - otherwise open a lineage (section 16) in state `SWEPT` with `sweep_bar = b` and `sweep_extreme = low(b)`.
- **GP-REQ-053** If one bar sweeps several sell-side objects, one lineage opens, keyed to the object with the highest type priority `PRIOR_RTH > OVERNIGHT > SWING_K` (ties go to the lowest level). The others become `CONSUMED` with cause `SUBSUMED` (AMB-011).

## 8. Reclaim

While a lineage is `SWEPT`, for each bar `j` with `j − s < P-RECLAIM-MAX-BARS` (where `s` is the sweep bar; the sweep bar itself is `j = s`):

- **GP-REQ-060** `sweep_extreme ← min(sweep_extreme, low(j))`. If `L.level − sweep_extreme > P-SWEEP-MAX-PEN-ATR · ATR_sweep`, the lineage becomes `INVALIDATED` with `GP_INVALID_SWEEP_TOO_DEEP`.
- **GP-REQ-061** If `close(j) ≥ L.level + P-RECLAIM-MIN-TICKS`, the lineage becomes `RECLAIMED` (classification `CONFIRMED`) at `j`. The sweep bar itself may reclaim.
- **GP-REQ-062** Otherwise, if `close(j) < L.level`, increment `below_count`; else reset it to 0. When `below_count ≥ P-ACCEPT-CLOSES`, the lineage becomes `INVALIDATED` with `GP_INVALID_ACCEPTED_BEYOND` (classification `ACCEPTED_BEYOND_LEVEL`).
- **GP-REQ-063** If `j − s = P-RECLAIM-MAX-BARS − 1` and none of the above fired, the lineage becomes `EXPIRED` with `GP_EXPIRED_RECLAIM_WINDOW` (classification `FAILED`).
- **GP-REQ-064** **A failed or invalidated bullish reclaim never creates a bearish lineage.** A bearish lineage can only come from its own buy-side sweep.
- **GP-REQ-065** When the lineage reaches `RECLAIMED`, `sweep_extreme` is frozen.

## 9. Displacement

While `RECLAIMED` (reclaim bar `r`), each bar `d` with `r ≤ d ≤ r + P-DISP-MAX-BARS` is measured, and its raw measurements are retained whether or not it qualifies:

- **GP-REQ-070** `range = high − low`, `body = close − open`, `ATR_d = ATR(d)`.
- **GP-REQ-071** `d` qualifies iff all four gates pass:
  - `RANGE`: `range ≥ P-DISP-RANGE-ATR · ATR_d`;
  - `BODY`: `body > 0` and `body / range ≥ P-DISP-BODY-RATIO`;
  - `CLOSE_LOCATION`: `(close − low) / range ≥ P-DISP-CLOSE-LOC`;
  - `STRUCTURE_BREAK`: `close(d) > max(high)` over the bars `[s − P-DISP-STRUCT-LOOKBACK, d − 1]` of the same contract (clipped to the bars that exist).

  A bar with `range = 0` fails every gate.
- **GP-REQ-072** The first qualifying bar makes the lineage `DISPLACED` at `d`. The reclaim bar may itself be the displacement bar.
- **GP-REQ-073** If no bar qualifies by `d = r + P-DISP-MAX-BARS`, the lineage becomes `EXPIRED` with `GP_EXPIRED_DISPLACEMENT_WINDOW`. Each rejected candidate's failed gates are recorded.

## 10. Zone

- **GP-REQ-080** The only zone family in this draft is the fair-value gap created by the displacement bar (AMB-018). On bar `d+1`, a bullish FVG exists iff `low(d+1) − high(d−1) ≥ P-FVG-MIN-TICKS`. Then `zone.bottom = high(d−1)`, `zone.top = low(d+1)`, `formed_at = event_time(d+1)`, and `available_at = available_at(d+1)`.
- **GP-REQ-081** If there is no FVG on bar `d+1`, the lineage becomes `EXPIRED` with `GP_EXPIRED_NO_ZONE` at `d+1`. No later bar can create the zone.

## 11. Retest

- **GP-REQ-090** **The retest happens strictly after the zone exists.** Eligible bars are `t` with `d+2 ≤ t ≤ d+1+P-RETEST-MAX-BARS`. Bar `t` is a retest iff `low(t) ≤ zone.top`. The first one makes the lineage `RETESTED`. Bar `d+1` can never be a retest, even if it reaches `zone.top`.
- **GP-REQ-091** If no retest happens by `t = d+1+P-RETEST-MAX-BARS`, the lineage becomes `EXPIRED` with `GP_EXPIRED_RETEST_WINDOW`.

## 12. Confirmation

- **GP-REQ-100** Eligible bars are `c` with `t ≤ c ≤ t + P-CONF-MAX-BARS − 1`. Bar `c` confirms iff `close(c) > zone.top` and `close(c) > open(c)`. The retest bar may confirm. The first confirming bar makes the lineage `CONFIRMED`.
- **GP-REQ-101** If nothing confirms by `c = t + P-CONF-MAX-BARS − 1`, the lineage becomes `EXPIRED` with `GP_EXPIRED_CONFIRMATION_WINDOW`.
- **GP-REQ-102** Words such as "strong", "clean", or "obvious" have no meaning here. Confirmation is exactly GP-REQ-100.

## 13. Pre-authorization invalidation

These are checked on every bar of an active lineage before progress checks (GP-REQ-006):

- **GP-REQ-110** If the primary bar's `contract_id` differs from the lineage's, the lineage becomes `INVALIDATED` with `GP_INVALID_CONTRACT_CHANGED`. This takes precedence over the resulting data-quality state.
- **GP-REQ-111** If the primary feed health is not `HEALTHY` (gap, staleness at a `ClockTick`, or a conflicting duplicate), the lineage becomes `BLOCKED` with `DQ_BLOCK_PRIMARY_GAPPED`, `DQ_BLOCK_PRIMARY_STALE`, or `DQ_BLOCK_PRIMARY_UNKNOWN`. A blocked lineage never resumes, because its evidence chain has a hole.
- **GP-REQ-112** After `RECLAIMED`, any bar with `low < sweep_extreme` makes the lineage `INVALIDATED` with `GP_INVALID_SWEEP_EXTREME_BREACHED`.
- **GP-REQ-113** From bar `d+2` onward, any bar with `close < zone.bottom` makes the lineage `INVALIDATED` with `GP_INVALID_ZONE_MITIGATED`. This is checked before retest and confirmation on the same bar.

## 14. SMT (inter-market divergence)

- **GP-REQ-120** SMT is mandatory when `P-SMT-REQUIRED` is true. Pairs come from `P-SMT-PAIRS` (ES↔NQ, MES↔MNQ). The outcome is an enum. **It is never a score.**
- **GP-REQ-121** SMT is evaluated on the confirmation bar `c`, with decision time `τ = available_at(c) + P-SMT-MAX-WAIT-S`. The SMT window is the primary bars from the sweep bar `s` through the reclaim bar `r`.
- **GP-REQ-122** The paired reference is the pair instrument's liquidity object with the same `type` and `session_date` as `L` (for swing types, see AMB-024).
- **GP-REQ-123** The outcome is the first matching state in this order:
  1. `UNAVAILABLE`: no pair is configured, no paired reference exists, or pair feed health at `τ` is not `HEALTHY`;
  2. `MISALIGNED`: a pair bar available by `τ` with `bar_start` in `[bar_start(s), bar_start(c)]` has a `bar_start` that is not the `bar_start` of a primary bar, or has a different timeframe;
  3. `STALE`: the pair bar with `bar_start = bar_start(c)` is not available by `τ`;
  4. `DENIED`: `min(low)` of the pair bars in the SMT window `< paired_ref.level` (the pair also swept, so there is no divergence);
  5. `UNCLEAR`: `paired_ref.level ≤ min(low) < paired_ref.level + P-SMT-MARGIN-TICKS[pair root]`;
  6. `CONFIRMED`.
- **GP-REQ-124** `CONFIRMED` makes the lineage `SMT_CONFIRMED`. Any other outcome makes it `BLOCKED` with `SMT_BLOCK_<state>`.
- **GP-REQ-125** The traded instrument is the one that swept (the primary). Trading the instrument that held is out of scope for this draft (AMB-025).

## 15. Entry, stop, target, net R

These are evaluated on the confirmation bar `c` after SMT, in this order: one-attempt (GP-REQ-131), target, net R.

- **GP-REQ-140** `entry_limit = close(c) + P-ENTRY-LIMIT-OFFSET-TICKS`. The entry order is a limit order valid for the next bar only; that order lifecycle belongs to the order state machine, not this reducer.
- **GP-REQ-141** `stop = sweep_extreme − P-STOP-BUFFER-TICKS`.
- **GP-REQ-142** Target: among `ACTIVE` buy-side liquidity objects with `available_at ≤ available_at(c)` and `level > entry_limit + P-TARGET-FRONTRUN-TICKS`, take the one with the lowest level. Then `target = level − P-TARGET-FRONTRUN-TICKS`. Only the nearest qualifying level may be used; choosing a further level to pass the R test is forbidden. If there is none, the lineage becomes `BLOCKED` with `GP_BLOCK_NO_TARGET`.
- **GP-REQ-143** `net_R = qe.core.instruments.net_r(spec, LONG, entry_limit, stop, target, CostModel(P-COST-COMMISSION-RT-MINOR, entry_slippage_ticks=0, stop_slippage_ticks=P-COST-STOP-SLIP-TICKS, target_slippage_ticks=0))`. Entry slippage is 0 because the limit price is already the worst accepted entry.
- **GP-REQ-144** If `net_R < P-MIN-NET-R`, the lineage becomes `BLOCKED` with `GP_BLOCK_R_BELOW_MIN`. The ≥2R rule is evaluated **after costs** (AMB-028).
- **GP-REQ-145** If every check passes, the lineage becomes `STRATEGY_AUTHORIZED` with reason `GP_AUTHORIZED`. It emits a decision record (directive D6) carrying `entry_ticks, invalidation_ticks (= stop), target_ticks, net_R, smt_state, evidence_ids`. Risk approval, sizing, and order intent are separate authorities (directive B1).

## 16. Lineage and one attempt

- **GP-REQ-130** `lineage_id = sha256_hex(canonical(...))` (`qe/core/serialization.py`) of `{spec_version, instrument_root, contract_id, direction, setup_family: "GP_REVERSAL", liquidity_id, sweep_bar_start_ns, session_id}`. `session_id = "<root>:RTH:<session_date>"`. A new process, alert, score, or bar cannot mint a different identity for the same sweep.
- **GP-REQ-131** If the lineage store holds this `lineage_id` with `attempt_count ≥ 1`, the lineage becomes `BLOCKED` with `GP_BLOCK_ONE_ATTEMPT_USED`. Reaching `STRATEGY_AUTHORIZED` sets `attempt_count = 1`.
- **GP-REQ-132** If the lineage store is unavailable (missing, unreadable), authorization is `BLOCKED` with `GP_BLOCK_LINEAGE_STORE_UNAVAILABLE`.
- **GP-REQ-133** A consumed liquidity object can never seed another lineage, so each liquidity object yields at most one attempt.

## 17. States and transitions

Per-lineage states follow directive D4: `SWEPT → RECLAIMED → DISPLACED → RETESTED → CONFIRMED → SMT_CONFIRMED → STRATEGY_AUTHORIZED`. A pre-authorization state can exit to `BLOCKED`, `INVALIDATED`, or `EXPIRED`. `CONTEXT_VALID` and `LIQUIDITY_ARMED` are properties of the instrument and its liquidity objects, not of a lineage, because a lineage is born at the sweep.

- **GP-REQ-150** Every transition record contains the fields required by directive D4, including a transition hash chained to the previous record (`qe/core/serialization.py chain_hash`).
- **GP-REQ-151** No state may be skipped. A score, confidence value, AI output, or alert cannot move a lineage.

## 18. Replay fill policy (informative, for Phase 4)

When one bar contains both a stop and a target, the stop is assumed first. A gap through the stop fills at that bar's open, never at the stop price. An entry limit fills only if a later bar trades at or through the limit. These choices are recorded as AMB-034 and AMB-035.

## 19. Excluded from this draft

These are excluded until the source document says otherwise. Each one is an ambiguity entry with the recommendation "exclude from 1.0.0; candidate experimental overlay (directive F10)":

- premium/discount and the dealing range;
- BOS/CHoCH labels;
- iFVG, order blocks, breaker blocks;
- lower-timeframe confirmation;
- volume and relative volume;
- equal highs/lows as a distinct liquidity type;
- macro filters;
- any score, confidence value, or AI input.
