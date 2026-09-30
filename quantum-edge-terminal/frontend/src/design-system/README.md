# Quantum Edge design system

The terminal's copy of the Quantum Edge Design System: tokens, component styles and React components. The published system — brand book, live previews in both themes, cover — is at <https://claude.ai/artifact/7sUBxx9A6prHTEsBKVpYPd> (private to its owner until shared).

## Files

- `tokens.json` — the source of truth: colors for the Dark and Light themes, type, spacing, radii, shadows, sizes and chart strokes.
- `tokens.css` — generated from `tokens.json` by `npm run tokens`. Never edit it by hand; `npm run tokens:check` fails when it is stale.
- `components.css` — component styles. Every color, space, radius and stroke is a token variable.
- `index.ts` — exports the components (`TerminalHeader`, `Panel`, `ToggleGroup`, `SignalCard`, `AlertItem`, `PriceChart`, `TradeTicket`, `GateChecklist`, `RiskMeter`, `ApprovalBar`, `KillSwitch`, …), the formatters and `computeTicket`.
- Fonts (IBM Plex Mono and Sans, SIL OFL) are served from `public/fonts`.

## Using it

- Set the theme on the root element: `<html data-theme="dark">` (the default) or `"light"`.
- Import from `@/design-system`. Styles are loaded once in `src/app/layout.tsx`.
- Tailwind utilities read the same tokens: `bg-surface-raised`, `text-ink-muted`, `border-line`, `text-accent`, `text-bull`, `text-danger`, `font-mono`. The `qt-*` colors are the constant brand primitives.
- Content rules the components assume: prices are points (`formatPrice`), money is USD (`formatUsd`), times are New York time with "ET" (`src/lib/time.ts`), scores rank and are never shown as a confidence percentage, and futures size is whole contracts, rounded down (`computeTicket`).

## Changing it

Edit `tokens.json`, run `npm run tokens`, and re-sync the published system from this folder so both stay identical.
