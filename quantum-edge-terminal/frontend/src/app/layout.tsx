import type { Metadata } from 'next';
import type { ReactNode } from 'react';
// Order matters: tokens define the variables, components use them, Tailwind utilities come last so they win.
import '@/design-system/tokens.css';
import '@/design-system/components.css';
import './globals.css';

export const metadata: Metadata = {
  title: 'Quantum Edge Terminal',
  description: 'Trading research and decision-support terminal',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" data-theme="dark">
      <body>{children}</body>
    </html>
  );
}
