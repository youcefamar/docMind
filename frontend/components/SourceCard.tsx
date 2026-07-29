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

export interface Citation {
  source_id: string;
  filename: string;
  location_type: string;
  location_value: string;
  supported: boolean;
}

interface SourceCardProps {
  sources: Source[];
  citations?: Citation[];
}

export default function SourceCard({ sources, citations = [] }: SourceCardProps) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(0);

  if (!sources || sources.length === 0) return null;

  const getCategoryColor = (category: string) => {
    const palette = [
      'border-slate-200 bg-slate-50 text-slate-600',
      'border-sky-200 bg-sky-50 text-sky-700',
      'border-emerald-200 bg-emerald-50 text-emerald-700',
      'border-amber-200 bg-amber-50 text-amber-700',
      'border-rose-200 bg-rose-50 text-rose-700',
    ];
    const hash = Array.from(category || '').reduce((sum, character) => sum + character.charCodeAt(0), 0);
    return palette[hash % palette.length];
  };

  return (
    <div className="mt-4 border-t border-[#eeeeeb] pt-3">
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
        <Sparkles className="h-3.5 w-3.5 text-slate-400" />
        <span>Verified Sources ({sources.length})</span>
      </div>
      {citations.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2 text-[10px]">
          {citations.map((citation) => (
            <span
              key={citation.source_id}
              className={`rounded-full border px-2 py-0.5 ${
                citation.supported
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                  : 'border-amber-200 bg-amber-50 text-amber-700'
              }`}
            >
              {citation.source_id} · {citation.supported ? 'supported' : 'needs review'}
            </span>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {sources.map((src, idx) => {
          const isExpanded = expandedIdx === idx;
          const matchPercent = Math.round((src.similarity || 0) * 100);

          return (
            <div
              key={`${src.doc_id}-${idx}`}
              className="rounded-xl border border-[#e8e8e5] bg-[#fcfcfb] p-3 text-left transition-all hover:border-slate-300"
            >
              <div
                className="flex items-start justify-between cursor-pointer gap-2"
                onClick={() => setExpandedIdx(isExpanded ? null : idx)}
              >
                <div className="flex items-center gap-2 overflow-hidden">
                  <div className="flex-shrink-0 rounded-lg bg-slate-100 p-1.5 text-slate-500">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="truncate">
                    <h4 className="truncate text-xs font-medium text-slate-700" title={src.filename}>
                      {src.filename}
                    </h4>
                    <div className="flex items-center gap-2 mt-0.5 text-[11px]">
                      <span className={`px-1.5 py-0.2 rounded border font-medium ${getCategoryColor(src.category)}`}>
                        {src.category}
                      </span>
                      <span className="text-slate-400">
                        Page {src.page_number} of {src.total_pages}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <span
                    className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      matchPercent >= 75
                        ? 'bg-emerald-50 text-emerald-700'
                        : matchPercent >= 50
                        ? 'bg-amber-50 text-amber-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {matchPercent}% Match
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                  )}
                </div>
              </div>

              {/* Collapsible Chunk Excerpt */}
              {isExpanded && (
                <div className="mt-3 rounded-lg border-t border-[#eeeeeb] bg-white p-2.5 pt-3 text-xs leading-relaxed text-slate-600">
                  <p className="italic">"{src.excerpt}"</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
