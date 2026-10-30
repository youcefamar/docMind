'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  Check,
  Clock,
  Copy,
  Cpu,
  FileText,
  Filter,
  GitCompare,
  Layers,
  RefreshCw,
  Sparkles,
  Zap,
} from 'lucide-react';

interface DocumentItem {
  id: string;
  filename: string;
  category: string;
  total_pages: number;
  chunk_count: number;
  status: string;
}

interface CompareDocumentInfo {
  document_id: string;
  filename: string;
  category: string;
  total_pages: number;
  chunk_count: number;
}

interface CompareTelemetry {
  model?: string;
  document_count?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  tokens_per_second?: number;
  elapsed_ms?: number;
  focus_aspect?: string;
}

interface CompareResponse {
  comparison_markdown: string;
  documents: CompareDocumentInfo[];
  focus_aspect?: string | null;
  telemetry?: CompareTelemetry | null;
}

const PRESET_TOPICS = [
  'Remote Work & Flexibility',
  'Termination & Liability Clauses',
  'Compensation, Benefits & PTO',
  'Compliance & Data Protection',
];

export default function ComparePage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [focusAspect, setFocusAspect] = useState<string>('');
  const [isLoadingDocs, setIsLoadingDocs] = useState<boolean>(true);
  const [isComparing, setIsComparing] = useState<boolean>(false);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const fetchDocuments = useCallback(async () => {
    setIsLoadingDocs(true);
    setErrorMessage(null);
    try {
      const res = await fetch('/api/backend/docs');
      if (!res.ok) {
        throw new Error(`Failed to load document catalog (status ${res.status})`);
      }
      const data = await res.json();
      const docs: DocumentItem[] = Array.isArray(data) ? data : [];
      setDocuments(docs);

      // Pre-select first 2 indexed documents if none selected yet
      if (docs.length >= 2 && selectedIds.length === 0) {
        setSelectedIds([docs[0].id, docs[1].id]);
      }
    } catch (err: unknown) {
      console.warn('Error fetching docs for comparison:', err);
      setErrorMessage(err instanceof Error ? err.message : 'Failed to load documents.');
    } finally {
      setIsLoadingDocs(false);
    }
  }, [selectedIds.length]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const toggleDocument = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleRunComparison = async () => {
    if (selectedIds.length < 2) {
      setErrorMessage('Please select at least 2 documents to compare.');
      return;
    }

    setIsComparing(true);
    setErrorMessage(null);
    setCompareResult(null);

    try {
      const res = await fetch('/api/backend/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_ids: selectedIds,
          focus_aspect: focusAspect.trim() || null,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        throw new Error(errorData?.detail || `Comparison failed with status ${res.status}`);
      }

      const data: CompareResponse = await res.json();
      setCompareResult(data);
    } catch (err: unknown) {
      console.error('Comparison error:', err);
      setErrorMessage(err instanceof Error ? err.message : 'Comparison request failed.');
    } finally {
      setIsComparing(false);
    }
  };

  const copyToClipboard = () => {
    if (!compareResult?.comparison_markdown) return;
    navigator.clipboard.writeText(compareResult.comparison_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
              <GitCompare className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
                Deep Document Comparison
              </h1>
              <p className="text-xs text-slate-500 sm:text-sm">
                Powered by NVIDIA Nemotron 3 Ultra on Nebius Token Factory
              </p>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={fetchDocuments}
          disabled={isLoadingDocs}
          className="inline-flex items-center gap-1.5 self-start rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isLoadingDocs ? 'animate-spin' : ''}`} />
          Refresh Catalog
        </button>
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-700">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Grid: Selection Left, Configuration/Results Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Document Catalog Selector (4 cols) */}
        <div className="lg:col-span-5 space-y-5">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-slate-600" />
                <h2 className="text-sm font-semibold text-slate-900">Select Documents</h2>
              </div>
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-700">
                {selectedIds.length} selected
              </span>
            </div>

            <p className="text-xs text-slate-500 mt-2">
              Select 2 or more files to synthesize cross-document matrices and risk analysis.
            </p>

            {/* Document list */}
            <div className="mt-4 max-h-[360px] space-y-2 overflow-y-auto pr-1">
              {isLoadingDocs ? (
                <div className="flex flex-col items-center justify-center py-12 text-slate-400 gap-2">
                  <RefreshCw className="h-5 w-5 animate-spin" />
                  <span className="text-xs">Loading document catalog...</span>
                </div>
              ) : documents.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-xs text-slate-500">
                  No indexed documents found. Upload files in the Sources tab first.
                </div>
              ) : (
                documents.map((doc) => {
                  const isChecked = selectedIds.includes(doc.id);
                  return (
                    <label
                      key={doc.id}
                      className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 text-xs transition-all ${
                        isChecked
                          ? 'border-emerald-500 bg-emerald-50/40 text-slate-900 shadow-sm'
                          : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleDocument(doc.id)}
                        className="mt-0.5 h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-medium text-slate-900">{doc.filename}</span>
                        <span className="mt-1 flex items-center gap-2 text-[11px] text-slate-500">
                          <span className="rounded bg-slate-100 px-1.5 py-0.5 font-medium text-slate-600">
                            {doc.category}
                          </span>
                          <span>{doc.total_pages} {doc.total_pages === 1 ? 'page' : 'pages'}</span>
                          <span>•</span>
                          <span>{doc.chunk_count} chunks</span>
                        </span>
                      </span>
                    </label>
                  );
                })
              )}
            </div>

            {/* Focus Aspect / Topic Input */}
            <div className="mt-5 pt-4 border-t border-slate-100 space-y-2.5">
              <label htmlFor="focus-aspect" className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                <Filter className="h-3.5 w-3.5 text-slate-500" />
                <span>Focus Clause or Topic (Optional)</span>
              </label>
              <input
                id="focus-aspect"
                type="text"
                value={focusAspect}
                onChange={(e) => setFocusAspect(e.target.value)}
                placeholder="e.g. Remote work, PTO, Liability limitations..."
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-slate-400 focus:bg-white focus:outline-none"
              />

              {/* Preset suggestion pills */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {PRESET_TOPICS.map((topic) => (
                  <button
                    key={topic}
                    type="button"
                    onClick={() => setFocusAspect(topic)}
                    className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-[10px] font-medium text-slate-600 hover:bg-slate-100 transition-colors"
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>

            {/* Compare Button */}
            <button
              type="button"
              onClick={handleRunComparison}
              disabled={isComparing || selectedIds.length < 2}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 py-3 text-xs font-semibold text-white shadow-md hover:bg-slate-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isComparing ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin text-emerald-400" />
                  <span>Synthesizing with Nemotron 3 Ultra...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 text-emerald-400" />
                  <span>Synthesize Cross-Document Matrix</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Comparative Synthesis Output (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {compareResult ? (
            <div className="space-y-4">
              {/* Telemetry Strip */}
              {compareResult.telemetry && (
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-[11px] text-slate-600 shadow-sm">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1.5 font-semibold text-slate-800">
                      <Cpu className="h-3.5 w-3.5 text-emerald-600" />
                      {compareResult.telemetry.model || 'nvidia/nemotron-3-ultra'}
                    </span>
                    {compareResult.telemetry.total_tokens ? (
                      <span className="flex items-center gap-1 text-slate-500">
                        <Zap className="h-3.5 w-3.5 text-amber-500" />
                        {compareResult.telemetry.total_tokens} tokens
                        {compareResult.telemetry.tokens_per_second
                          ? ` (${compareResult.telemetry.tokens_per_second} tps)`
                          : ''}
                      </span>
                    ) : null}
                  </div>

                  <div className="flex items-center gap-3">
                    {compareResult.telemetry.elapsed_ms ? (
                      <span className="flex items-center gap-1 text-slate-500">
                        <Clock className="h-3.5 w-3.5 text-slate-400" />
                        {(compareResult.telemetry.elapsed_ms / 1000).toFixed(2)}s
                      </span>
                    ) : null}

                    <button
                      type="button"
                      onClick={copyToClipboard}
                      className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 font-medium text-slate-700 shadow-sm hover:bg-slate-50"
                      title="Copy Markdown Report"
                    >
                      {copied ? (
                        <>
                          <Check className="h-3 w-3 text-emerald-600" />
                          <span className="text-emerald-600">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3 text-slate-500" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Rendered Markdown Card */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm">
                <div className="prose prose-slate max-w-none text-xs sm:text-sm leading-relaxed whitespace-pre-wrap font-sans">
                  {compareResult.comparison_markdown}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-[#fcfcfb] p-12 text-center text-slate-400 min-h-[460px]">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 mb-3">
                <Layers className="h-6 w-6" />
              </div>
              <h3 className="text-sm font-semibold text-slate-700">No Comparison Generated Yet</h3>
              <p className="mt-1 max-w-sm text-xs text-slate-500">
                Select 2 or more files on the left and click &quot;Synthesize Cross-Document Matrix&quot; to generate an executive comparison.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
