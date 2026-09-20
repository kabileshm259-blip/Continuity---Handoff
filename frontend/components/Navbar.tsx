'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  ArrowRightLeft, 
  Layers, 
  PlusCircle, 
  UserCheck, 
  Cpu
} from 'lucide-react';
import { fetchHealth } from '@/lib/api';

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const [health, setHealth] = useState<{ status: string; ai_provider: string } | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => {
      setHealth({ status: 'offline', ai_provider: 'offline' });
    });
  }, []);

  const navItems = [
    { label: 'Dashboard', href: '/', icon: Layers },
    { label: 'Create Handoff', href: '/handoff/new', icon: PlusCircle },
    { label: 'Continuity Queue', href: '/queue', icon: ArrowRightLeft },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200/90 bg-white/95 backdrop-blur-xs shadow-2xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Tagline */}
          <div className="flex items-center gap-3 shrink-0">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-extrabold tracking-wider text-sm shadow-xs group-hover:bg-slate-800 transition-colors">
                C
              </div>
              <div className="flex flex-col">
                <span className="font-extrabold text-slate-900 tracking-tight text-base leading-none">
                  CONTINUITY
                </span>
                <span className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase mt-1">
                  Handoff Intelligence
                </span>
              </div>
            </Link>
          </div>

          {/* Navigation Items (Centered, exactly matched h-9 height) */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`h-9 inline-flex items-center gap-2 px-3.5 rounded-lg text-xs font-semibold transition-colors ${
                    isActive
                      ? 'bg-slate-100 text-slate-900 shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-slate-900' : 'text-slate-500'}`} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* System Status & Active Persona Badges (Matched h-9 height) */}
          <div className="flex items-center gap-2.5 shrink-0">
            {/* Real Bedrock Nova 2 Lite Status Indicator */}
            <div className="hidden sm:inline-flex items-center gap-2 h-9 px-3 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 text-xs font-mono">
              <Cpu className="w-3.5 h-3.5 text-slate-500" />
              <span className="font-bold tracking-tight">BEDROCK NOVA 2 LITE</span>
              <span 
                className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-500' : 'bg-amber-400'}`} 
                title="Amazon Bedrock Online"
              />
            </div>

            {/* Active Persona indicator */}
            <div className="inline-flex items-center gap-2 h-9 px-3.5 rounded-lg bg-slate-900 text-white text-xs font-medium shadow-2xs">
              <UserCheck className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span className="hidden sm:inline text-slate-300">Active:</span>
              <span className="font-bold">
                {pathname.includes('/queue') ? 'Priya Sharma (Incoming)' : 'Arun Kumar (Outgoing)'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
