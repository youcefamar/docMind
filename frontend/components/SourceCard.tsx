'use client';

import React, { useState } from 'react';
import { FileText, Bookmark, ChevronDown, ChevronUp, ExternalLink, Sparkles } from 'lucide-react';

export interface Source {
  doc_id: string;
  filename: string;
  category: string;
  page_number: number;
  total_pages: number;
  excerpt: string;
  similarity: number;
}

interface SourceCardProps {
  sources: Source[];
}

export default function SourceCard({ sources }: SourceCardProps) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(0);

  if (!sources || sources.length === 0) return null;

  const getCategoryColor = (category: string) => {
    const palette = [
      'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
      'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
      'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      'bg-amber-500/10 text-amber-400 border-amber-500/20',
      'bg-pink-500/10 text-pink-400 border-pink-500/20',
    ];
    const hash = Array.from(category || '').reduce((sum, character) => sum + character.charCodeAt(0), 0);
    return palette[hash % palette.length];
  };

  return (
    <div className="mt-4 pt-3 border-t border-gray-800/80">
      <div className="flex items-center gap-2 mb-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
        <span>Verified Sources ({sources.length})</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {sources.map((src, idx) => {
          const isExpanded = expandedIdx === idx;
          const matchPercent = Math.round((src.similarity || 0) * 100);

          return (
            <div
              key={`${src.doc_id}-${idx}`}
              className="glass-card rounded-xl p-3 text-left transition-all border border-gray-800 hover:border-indigo-500/40"
            >
              <div
                className="flex items-start justify-between cursor-pointer gap-2"
                onClick={() => setExpandedIdx(isExpanded ? null : idx)}
              >
                <div className="flex items-center gap-2 overflow-hidden">
                  <div className="p-1.5 rounded-lg bg-gray-800 text-indigo-400 flex-shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="truncate">
                    <h4 className="text-xs font-medium text-gray-200 truncate" title={src.filename}>
                      {src.filename}
                    </h4>
                    <div className="flex items-center gap-2 mt-0.5 text-[11px]">
                      <span className={`px-1.5 py-0.2 rounded border font-medium ${getCategoryColor(src.category)}`}>
                        {src.category}
                      </span>
                      <span className="text-gray-400">
                        Page {src.page_number} of {src.total_pages}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <span
                    className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      matchPercent >= 75
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : matchPercent >= 50
                        ? 'bg-amber-500/20 text-amber-300'
                        : 'bg-gray-700 text-gray-300'
                    }`}
                  >
                    {matchPercent}% Match
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  )}
                </div>
              </div>

              {/* Collapsible Chunk Excerpt */}
              {isExpanded && (
                <div className="mt-3 pt-2 border-t border-gray-800/60 text-xs text-gray-300 bg-gray-950/40 p-2.5 rounded-lg leading-relaxed font-mono">
                  <p className="italic text-gray-300">"{src.excerpt}"</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
