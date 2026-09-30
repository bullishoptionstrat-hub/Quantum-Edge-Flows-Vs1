#!/usr/bin/env node
// Compile src/design-system/tokens.json into src/design-system/tokens.css: the same CSS the Quantum Edge
// Design System artifact generates (theme blocks on data-theme, :root lengths and fonts, one class per
// text style, @font-face per font). `--check` exits 1 when tokens.css is out of date.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const dir = fileURLToPath(new URL('../src/design-system/', import.meta.url));
const tokens = JSON.parse(readFileSync(dir + 'tokens.json', 'utf8'));
const FONT_URL_PREFIX = '/'; // tokens.json lists fonts as fonts/<file>; Next serves them from public/fonts

const esc = (name) => {
  let s = name.replace(/\./g, '\\.');
  if (/^[0-9]/.test(s)) {
    s = '\\3' + s[0] + ' ' + s.slice(1);
  }
  return s;
};
const alias = (v) => (typeof v === 'string' ? /^\{([A-Za-z0-9][A-Za-z0-9_.-]{0,63})\}$/.exec(v)?.[1] : undefined);

const themes = tokens.color.themes;
const first = themes[0].id;
const byTheme = (t) => ({ name: t.name, value: typeof t.value === 'string' ? { [first]: t.value } : t.value });
const colors = tokens.color.tokens.map(byTheme);
const shadows = (tokens.shadow?.tokens ?? []).map(byTheme);
const colorDecl = (name, v) => {
  const a = alias(v);
  return `  --${esc(name)}: ${a ? `var(--${esc(a)})` : v};`;
};

const out = ['/* Generated from tokens.json by scripts/build-tokens.mjs. Edit tokens.json, then run `npm run tokens`. */'];
out.push(
  `:root, [data-theme="${first}"] {`,
  ...colors.map((c) => colorDecl(c.name, c.value[first])),
  ...shadows.map((s) => `  --${esc(s.name)}: ${s.value[first]};`),
  '}',
);
for (const theme of themes.slice(1)) {
  // A later theme re-declares its own values, plus every alias, so aliases resolve against that theme.
  const block = [
    ...colors.filter((c) => theme.id in c.value || alias(c.value[first])).map((c) => colorDecl(c.name, c.value[theme.id] ?? c.value[first])),
    ...shadows.filter((s) => theme.id in s.value).map((s) => `  --${esc(s.name)}: ${s.value[theme.id]};`),
  ];
  if (block.length) {
    out.push(`[data-theme="${theme.id}"] {`, ...block, '}');
  }
}

const root = [];
for (const family of ['spacing', 'radius']) {
  for (const t of tokens[family]?.tokens ?? []) {
    root.push(`  --${esc(t.name)}: ${t.value};`);
  }
}
const handled = new Set(['name', 'version', 'meta', 'color', 'type', 'spacing', 'radius', 'shadow']);
for (const [family, body] of Object.entries(tokens)) {
  if (handled.has(family) || !body || !Array.isArray(body.tokens)) {
    continue;
  }
  for (const t of body.tokens) {
    root.push(`  --${esc(t.name)}: ${t.value};`);
  }
}
for (const [key, stack] of Object.entries(tokens.type.families)) {
  if (typeof stack !== 'string') {
    throw new Error(`tokens.json type.families.${key} must be a font stack string`);
  }
  root.push(`  --font-${esc(key)}: ${stack};`);
}
const colorNames = new Set(colors.map((c) => esc(c.name)));
for (const group of tokens.type.groups) {
  for (const s of group.styles) {
    const name = 'text-' + esc(s.name);
    if (colorNames.has(name)) {
      continue;
    }
    const family = s.family || group.family || '';
    const style = s.fontStyle ?? 'normal';
    root.push(`  --${name}: ${style === 'normal' ? '' : style + ' '}${s.fontWeight} ${s.fontSize}/${s.lineHeight}${family ? ` var(--font-${esc(family)})` : ' inherit'};`);
  }
}
out.push(':root {', ...root, '}');

for (const group of tokens.type.groups) {
  for (const s of group.styles) {
    const family = s.family || group.family || '';
    out.push(
      `.${esc(s.name)} {`,
      ...(family ? [`  font-family: var(--font-${esc(family)});`] : []),
      `  font-size: ${s.fontSize};`,
      `  line-height: ${s.lineHeight};`,
      `  font-weight: ${s.fontWeight};`,
      `  letter-spacing: ${s.letterSpacing ?? 'normal'};`,
      '}',
    );
  }
}

const FORMAT = { woff2: 'woff2', woff: 'woff', ttf: 'truetype', otf: 'opentype' };
for (const font of tokens.type.fonts) {
  const ext = font.file.split('.').pop().toLowerCase();
  out.push(
    '@font-face {',
    `  font-family: "${font.family}";`,
    `  src: url("${FONT_URL_PREFIX}${font.file}") format("${FORMAT[ext] ?? ext}");`,
    `  font-weight: ${font.weight};`,
    `  font-style: ${font.style ?? 'normal'};`,
    '  font-display: swap;',
    '}',
  );
}

const css = out.join('\n') + '\n';
const target = dir + 'tokens.css';
if (process.argv.includes('--check')) {
  let current = '';
  try {
    current = readFileSync(target, 'utf8');
  } catch {
    // missing file: reported below
  }
  if (current !== css) {
    console.error('src/design-system/tokens.css is out of date. Run `npm run tokens`.');
    process.exit(1);
  }
  console.log('tokens.css is up to date.');
} else {
  writeFileSync(target, css);
  console.log('Wrote src/design-system/tokens.css');
}
