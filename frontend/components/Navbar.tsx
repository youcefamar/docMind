'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BrainCircuit, FileText, MessageSquare, ShieldCheck, Cpu } from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-gray-800/80 px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <BrainCircuit className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-xl tracking-tight text-white group-hover:text-indigo-300 transition-colors">
                DocMind
              </span>
              <span className="text-[10px] uppercase font-semibold tracking-wider bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-500/30">
                v1.0
              </span>
            </div>
            <p className="text-xs text-gray-400 hidden sm:block">Internal Knowledge Assistant</p>
          </div>
        </Link>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-2 bg-gray-900/60 p-1 rounded-xl border border-gray-800">
          <Link
            href="/"
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              pathname === '/'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Chat</span>
          </Link>

          <Link
            href="/admin"
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              pathname === '/admin'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Document Admin</span>
          </Link>
        </nav>

        {/* Status Badge & Stack Meta */}
        <div className="hidden md:flex items-center gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-medium">Groq & ChromaDB Connected</span>
          </div>

          <div className="flex items-center gap-1.5 text-gray-500 bg-gray-900/80 px-2.5 py-1 rounded-md border border-gray-800">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span>Llama 3.1 8B</span>
          </div>
        </div>

      </div>
    </header>
  );
}
