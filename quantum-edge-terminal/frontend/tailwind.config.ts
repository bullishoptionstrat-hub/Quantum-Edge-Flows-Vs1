import type { Config } from 'tailwindcss';
import tokens from './src/design-system/tokens.json';

// Themed colors resolve to the design system's CSS variables (src/design-system/tokens.css), so utilities
// follow <html data-theme="dark" | "light">. The qt-* brand primitives are constant in every theme and keep
// their literal values from tokens.json, so opacity modifiers such as border-qt-accent/20 still work.
function primitive(name: string): string {
  const token = tokens.color.tokens.find((t) => t.name === name);
  if (!token || typeof token.value !== 'string') {
    throw new Error(`tokens.json has no constant color "${name}"`);
  }
  return token.value;
}
const themed = (name: string) => `var(--${name})`;

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        'qt-dark': primitive('qt-dark'),
        'qt-darker': primitive('qt-darker'),
        'qt-accent': primitive('qt-accent'),
        'qt-accent-alt': primitive('qt-accent-alt'),
        'qt-buy': primitive('qt-buy'),
        'qt-sell': primitive('qt-sell'),
        surface: {
          DEFAULT: themed('surface'),
          raised: themed('surface-raised'),
          overlay: themed('surface-overlay'),
          hover: themed('surface-hover'),
          selected: themed('surface-selected'),
        },
        line: { DEFAULT: themed('line'), strong: themed('line-strong'), control: themed('line-control') },
        ink: { DEFAULT: themed('ink'), muted: themed('ink-muted'), disabled: themed('ink-disabled') },
        accent: { DEFAULT: themed('accent'), hover: themed('accent-hover'), soft: themed('accent-soft'), alt: themed('accent-alt') },
        bull: themed('bull'),
        bear: themed('bear'),
        ok: themed('ok'),
        danger: themed('danger'),
        warning: themed('warning'),
        info: themed('info'),
      },
      fontFamily: { mono: [themed('font-mono')], sans: [themed('font-sans')] },
      borderRadius: { DEFAULT: themed('radius') },
    },
  },
  plugins: [],
};

export default config;
