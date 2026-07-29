'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BookOpen, BrainCircuit, FolderOpen, MessageSquare, Settings } from 'lucide-react';

const navigation = [
  { href: '/', label: 'Chat', icon: MessageSquare },
  { href: '/admin', label: 'Knowledge base', icon: FolderOpen },
];

function NavigationLinks({ compact = false }: { compact?: boolean }) {
  const pathname = usePathname();

  return (
    <nav className={compact ? 'flex items-center gap-1' : 'space-y-1'} aria-label="Main navigation">
      {navigation.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            href={href}
            key={href}
            className={
              compact
                ? `inline-flex items-center rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                    active ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'
                  }`
                : `flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-medium transition-colors ${
                    active ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'
                  }`
            }
          >
            <Icon className={compact ? 'h-4 w-4' : 'h-4 w-4'} />
            <span className={compact ? 'hidden sm:inline' : ''}>{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export default function Navbar() {
  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 flex h-16 items-center justify-between border-b border-[#e8e8e5] bg-white/95 px-4 backdrop-blur lg:hidden">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-white">
            <BrainCircuit className="h-4.5 w-4.5" />
          </span>
          <span className="text-sm font-semibold tracking-tight text-slate-950">DocMind</span>
        </Link>
        <NavigationLinks compact />
      </header>

      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-[#e8e8e5] bg-white px-4 py-5 lg:flex">
        <Link href="/" className="flex items-center gap-3 px-2 py-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
            <BrainCircuit className="h-5 w-5" />
          </span>
          <span>
            <span className="block text-base font-semibold tracking-tight text-slate-950">DocMind</span>
            <span className="block text-[11px] font-medium text-slate-400">PRIVATE KNOWLEDGE</span>
          </span>
        </Link>

        <div className="mt-10">
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">Workspace</p>
          <NavigationLinks />
        </div>

        <div className="mt-9">
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">Knowledge</p>
          <div className="rounded-xl border border-[#eeeeeb] bg-[#fafaf9] px-3.5 py-3.5">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
              <BookOpen className="h-4 w-4 text-slate-500" />
              Local workspace
            </div>
            <p className="mt-1.5 text-xs leading-5 text-slate-500">Your files stay on this machine.</p>
          </div>
        </div>

        <div className="mt-auto border-t border-[#eeeeeb] pt-4">
          <div className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-500">
            <Settings className="h-4 w-4" />
            Settings
          </div>
          <div className="mt-3 flex items-center gap-3 rounded-xl bg-[#fafaf9] p-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-xs font-semibold text-slate-600">DM</span>
            <span className="min-w-0">
              <span className="block truncate text-xs font-semibold text-slate-700">Local user</span>
              <span className="block text-[11px] text-emerald-600">● Offline workspace</span>
            </span>
          </div>
        </div>
      </aside>
    </>
  );
}
