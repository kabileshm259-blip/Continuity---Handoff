import type { Metadata } from 'next';
import './globals.css';
import { Navbar } from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'CONTINUITY — Workplace Handoff Intelligence',
  description: 'Turn messy handoff notes into structured, accountable work with AI fact extraction and deterministic policy enforcement.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full bg-slate-50">
      <body className="h-full flex flex-col font-sans antialiased text-slate-900 selection:bg-slate-900 selection:text-white">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>
              CONTINUITY MVP — Workplace Handoff Intelligence
            </span>
            <span className="text-slate-400 font-mono text-[11px]">
              AI Extracts Facts • Code Decides & Enforces Policy
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
