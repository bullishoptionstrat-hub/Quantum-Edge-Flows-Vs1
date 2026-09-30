// Quantum Edge design system: components, formatters and the trade-ticket math.
// Styles load once from src/app/layout.tsx: tokens.css (generated from tokens.json), then components.css.
export { Icon, Button, IconButton, ToggleGroup } from './controls';
export type { IconProps, ButtonProps, IconButtonProps, ToggleGroupProps, ToggleOption } from './controls';
export { TerminalHeader, Panel, Badge, Direction, FeedStatus, PanelState } from './status';
export type { TerminalHeaderProps, PanelProps, BadgeProps, DirectionProps, FeedState, FeedStatusProps, PanelStateProps } from './status';
export { SignalCard, AlertItem, GateChecklist } from './signals';
export type { SignalCardProps, AlertItemProps, Severity, Gate, GateStatus, GateChecklistProps } from './signals';
export { TradeTicket } from './ticket';
export type { TradeTicketProps, TradeTarget, SmtStatus } from './ticket';
export { computeTicket } from './ticket-math';
export type { TicketInput, TicketMath, TicketRow, TicketTarget } from './ticket-math';
export { RiskMeter, ApprovalBar, KillSwitch } from './risk';
export type { RiskMeterProps, ApprovalBarProps, KillSwitchProps } from './risk';
export { PriceChart, StatTile } from './charts';
export type { PricePoint, PriceLevel, PriceMarker, PriceChartProps, StatTileProps } from './charts';
export { formatPrice, formatPoints, formatUsd, formatR, decimalsFor, stateMeta } from './util';
export type { AnyState, DecisionState, SignalStatus, Side, Tone, StateMeta } from './util';
export type { IconName } from './icons';
