import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';

// Next 16 removed `next lint`; `npm run lint` runs the ESLint CLI with Next's flat config.
export default defineConfig([
  ...nextVitals,
  globalIgnores(['.next/**', 'out/**', 'coverage/**', 'next-env.d.ts']),
]);
