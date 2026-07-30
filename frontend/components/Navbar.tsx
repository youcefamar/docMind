'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Bot,
  BrainCircuit,
  Database,
  LayoutDashboard,
  MessageSquare,
  MoreHorizontal,
  PanelLeftClose,
  Settings,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface NavigationItem {
  href?: string;
  label: string;
  icon: LucideIcon;
}

interface StoredChatMessage {
  id?: string;
  sender?: string;
  content?: string;
  timestamp?: string;
}

interface RecentQuestion {
  id: string;
  content: string;
}

const primaryNavigation: NavigationItem[] = [
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/', label: 'Overview', icon: LayoutDashboard },
  { href: '/admin', label: 'Sources', icon: Database },
  { label: 'Agents', icon: Bot },
  { label: 'Settings', icon: Settings },
];

function isActivePath(pathname: string, href: string) {
  return href === '/' ? pathname === '/' : pathname.startsWith(href);
}

function NavigationLink({ item, compact = false }: { item: NavigationItem; compact?: boolean }) {
  const pathname = usePathname();
  const Icon = item.icon;

  if (!item.href) {
    return (
      <span
        aria-disabled="true"
        title={`${item.label} is not available yet`}
        className={
          compact
            ? 'inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-300'
            : 'flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium text-slate-300'
        }
      >
        <Icon className="h-4 w-4" strokeWidth={1.8} />
        {!compact && <span>{item.label}</span>}
      </span>
    );
  }

  const active = isActivePath(pathname, item.href);

  return (
    <Link
      href={item.href}
      aria-current={active ? 'page' : undefined}
      className={
        compact
          ? `inline-flex h-9 w-9 items-center justify-center rounded-lg transition-colors ${
              active ? 'bg-slate-100 text-slate-950' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-950'
            }`
          : `flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors ${
              active
                ? 'bg-[#f1f3f4] text-[#16191c]'
                : 'text-[#646b72] hover:bg-[#f6f7f8] hover:text-[#16191c]'
            }`
      }
      title={compact ? item.label : undefined}
    >
      <Icon className="h-4 w-4" strokeWidth={1.8} />
      {!compact && <span>{item.label}</span>}
    </Link>
  );
}

function useRecentQuestions() {
  const [questions, setQuestions] = useState<RecentQuestion[]>([]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem('docmind.chat-session.v1');
      if (!raw) return;
      const session = JSON.parse(raw) as { messages?: StoredChatMessage[] };
      const recent = (session.messages ?? [])
        .filter((message) => message.sender === 'user' && typeof message.content === 'string')
        .map((message) => ({
          id: message.id ?? `${message.timestamp ?? 'recent'}-${message.content}`,
          content: message.content?.trim() ?? '',
        }))
        .filter((question) => Boolean(question.content))
        .slice(-6)
        .reverse();
      setQuestions(recent);
    } catch {
      setQuestions([]);
    }
  }, []);

  return questions;
}

export default function Navbar() {
  const recentQuestions = useRecentQuestions();
  const mobileNavigation = primaryNavigation.filter((item) => item.href);

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 flex h-16 items-center justify-between border-b border-[#e8ebed] bg-white/95 px-4 backdrop-blur lg:hidden">
        <Link href="/" className="flex items-center gap-2.5" aria-label="DocMind overview">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#171a1d] text-white">
            <BrainCircuit className="h-4 w-4" strokeWidth={1.8} />
          </span>
          <span className="text-sm font-semibold tracking-tight text-[#171a1d]">DocMind</span>
        </Link>

        <nav className="flex items-center gap-1" aria-label="Main navigation">
          {mobileNavigation.map((item) => (
            <NavigationLink item={item} compact key={item.label} />
          ))}
        </nav>
      </header>

      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[220px] flex-col border-r border-[#e6e9eb] bg-white lg:flex">
        <div className="flex h-[58px] items-center justify-between border-b border-[#eef0f2] px-5">
          <Link href="/" className="flex items-center gap-2.5" aria-label="DocMind overview">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[#171a1d] text-white shadow-sm">
              <BrainCircuit className="h-4 w-4" strokeWidth={1.8} />
            </span>
            <span className="text-[15px] font-semibold tracking-[-0.02em] text-[#171a1d]">DocMind</span>
          </Link>
          <button
            type="button"
            aria-label="Collapse navigation"
            disabled
            title="Collapsible navigation is not available yet"
            className="rounded-md p-1.5 text-slate-400 disabled:cursor-not-allowed"
          >
            <PanelLeftClose className="h-4 w-4" strokeWidth={1.7} />
          </button>
        </div>

        <div className="flex min-h-0 flex-1 flex-col px-4 py-4">
          <nav className="space-y-1" aria-label="Main navigation">
            {primaryNavigation.map((item) => (
              <NavigationLink item={item} key={item.label} />
            ))}
          </nav>

          <section className="mt-8 min-h-0" aria-labelledby="recent-questions-heading">
            <h2
              id="recent-questions-heading"
              className="mb-2 px-3 text-[9px] font-semibold uppercase tracking-[0.16em] text-[#9aa1a8]"
            >
              Recent
            </h2>
            {recentQuestions.length > 0 ? (
              <ul className="space-y-0.5">
                {recentQuestions.map((question) => (
                  <li key={question.id}>
                    <Link
                      href="/chat"
                      className="block truncate rounded-md px-3 py-1.5 text-[11px] leading-4 text-[#646b72] transition-colors hover:bg-[#f6f7f8] hover:text-[#171a1d]"
                      title={question.content}
                    >
                      {question.content}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="px-3 text-[11px] leading-[1.55] text-[#a0a6ac]">
                Your latest questions will appear here.
              </p>
            )}
          </section>

          <div className="mt-auto border-t border-[#eef0f2] pt-3">
            <div className="flex items-center gap-3 rounded-lg px-2 py-2">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#e7f1ff] text-[11px] font-semibold text-[#4774a7]">
                DM
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-[12px] font-medium text-[#31363b]">Local user</span>
                <span className="block text-[10px] text-[#8a9299]">Private workspace</span>
              </span>
              <MoreHorizontal className="h-4 w-4 text-[#92999f]" strokeWidth={1.8} />
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
