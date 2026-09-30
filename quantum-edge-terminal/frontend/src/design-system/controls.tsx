'use client';

import * as React from 'react';
import { ICONS, type IconName } from './icons';
import { cx } from './util';

// ── Icon ────────────────────────────────────────────────────────────────────────────────
export interface IconProps {
  /** One of the system's 21 lucide icons (paths from lucide-static 0.292.0). */
  name: IconName;
  /** sm 14px (rows, badges) · md 20px (icon buttons) · lg 24px (header mark), or a pixel number. */
  size?: 'sm' | 'md' | 'lg' | number;
  /** Accessible name. Omit for decorative icons beside a visible word (they are then aria-hidden). */
  label?: string;
  className?: string;
}

const ICON_PX = { sm: 14, md: 20, lg: 24 } as const;

export function Icon({ name, size = 'sm', label, className }: IconProps) {
  const px = typeof size === 'number' ? size : ICON_PX[size];
  const nodes = ICONS[name] ?? [];
  return (
    <svg
      className={cx('qe-icon', typeof size === 'string' && 'qe-icon-' + size, className)}
      viewBox="0 0 24 24" width={px} height={px} fill="none" stroke="currentColor"
      strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" focusable="false"
      role={label ? 'img' : undefined} aria-label={label} aria-hidden={label ? undefined : true}
    >
      {nodes.map(([tag, attrs], i) => React.createElement(tag, { key: i, ...attrs }))}
    </svg>
  );
}

// ── Button ──────────────────────────────────────────────────────────────────────────────
export interface ButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'disabled'> {
  /** primary: the one action a view is for (accent fill) · secondary: everything else · danger: halting or destructive · ghost: low-emphasis. */
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'md' | 'sm';
  /** Leading icon. */
  icon?: IconName;
  /** Disables the button but keeps it focusable, so the reason can be read. */
  disabled?: boolean;
  /** Why it is disabled — exposed as the accessible description and tooltip. Setting it disables the button. */
  disabledReason?: string;
}

export function Button({ variant = 'secondary', size = 'md', icon, disabled, disabledReason, className, children, type = 'button', onClick, ...rest }: ButtonProps) {
  const reasonId = React.useId();
  const off = disabled || Boolean(disabledReason);
  return (
    <>
      <button
        {...rest}
        type={type}
        aria-disabled={off || undefined}
        aria-describedby={disabledReason ? reasonId : rest['aria-describedby']}
        title={disabledReason ?? rest.title}
        onClick={off ? (e) => e.preventDefault() : onClick}
        className={cx('qe-button', 'qe-button-' + variant, 'qe-button-' + size, 'qe-control-sm', off && 'is-disabled', className)}
      >
        {icon ? <Icon name={icon} size="sm" /> : null}
        <span>{children}</span>
      </button>
      {disabledReason ? <span id={reasonId} className="qe-sr-only">{disabledReason}</span> : null}
    </>
  );
}

// ── IconButton ──────────────────────────────────────────────────────────────────────────
export interface IconButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  icon: IconName;
  /** Required accessible name, also shown as the tooltip. */
  label: string;
  /** md: 20px icon, 38px target (header) · sm: 14px icon, 24px target (rows). */
  size?: 'md' | 'sm';
  /** For toggles: renders aria-pressed and the selected fill. */
  pressed?: boolean;
}

export function IconButton({ icon, label, size = 'md', pressed, className, type = 'button', ...rest }: IconButtonProps) {
  return (
    <button
      {...rest}
      type={type}
      aria-label={label}
      title={rest.title ?? label}
      aria-pressed={pressed}
      className={cx('qe-icon-button', 'qe-icon-button-' + size, pressed && 'is-pressed', className)}
    >
      <Icon name={icon} size={size === 'md' ? 'md' : 'sm'} />
    </button>
  );
}

// ── ToggleGroup (symbol and timeframe selectors) ────────────────────────────────────────
export interface ToggleOption { value: string; label?: string; disabled?: boolean }

export interface ToggleGroupProps {
  /** Accessible name of the group, e.g. "Symbol". */
  label: string;
  options: Array<string | ToggleOption>;
  /** Controlled value. Omit it (and pass defaultValue) for an uncontrolled group. */
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  /** accent: symbols (cyan) · alt: timeframes (violet). */
  tone?: 'accent' | 'alt';
  /** md: symbol chips (16px, 8/16 padding) · sm: timeframe chips (14px, 4/12 padding). */
  size?: 'md' | 'sm';
  className?: string;
}

export function ToggleGroup({ label, options, value, defaultValue, onChange, tone = 'accent', size = 'md', className }: ToggleGroupProps) {
  const opts: ToggleOption[] = options.map((o) => (typeof o === 'string' ? { value: o } : o));
  const [inner, setInner] = React.useState(defaultValue ?? opts[0]?.value);
  const current = value ?? inner;
  const refs = React.useRef<Array<HTMLButtonElement | null>>([]);
  const select = (v: string) => { if (value === undefined) setInner(v); onChange?.(v); };
  const step = (from: number, dir: number) => {
    for (let k = 1; k <= opts.length; k++) {
      const i = (from + dir * k + opts.length) % opts.length;
      if (!opts[i].disabled) { refs.current[i]?.focus(); select(opts[i].value); return; }
    }
  };
  const selectedIndex = opts.findIndex((o) => o.value === current);
  return (
    <div role="radiogroup" aria-label={label} className={cx('qe-toggle-group', className)}>
      {opts.map((o, i) => {
        const on = o.value === current;
        return (
          <button
            key={o.value}
            ref={(el) => { refs.current[i] = el; }}
            type="button" role="radio" aria-checked={on} disabled={o.disabled}
            tabIndex={on || (selectedIndex < 0 && i === 0) ? 0 : -1}
            onClick={() => select(o.value)}
            onKeyDown={(e) => {
              if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); step(i, 1); }
              else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); step(i, -1); }
              else if (e.key === 'Home') { e.preventDefault(); step(-1, 1); }
              else if (e.key === 'End') { e.preventDefault(); step(opts.length, -1); }
            }}
            className={cx('qe-toggle', 'qe-toggle-' + tone, 'qe-toggle-' + size, size === 'md' ? 'qe-control' : 'qe-control-sm', on && 'is-selected')}
          >
            {o.label ?? o.value}
          </button>
        );
      })}
    </div>
  );
}
