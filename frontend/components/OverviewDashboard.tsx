'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  Download,
  File,
  FileCheck2,
  FileSpreadsheet,
  FileText,
  FolderSync,
  Presentation,
  RefreshCw,
  Search,
  Sparkles,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface DocumentSummary {
  id: string;
  filename: string;
  category: string;
  chunk_count: number;
  total_pages: number;
  created_at: string;
  status: string;
  error_detail?: string | null;
}

interface RuntimeStatus {
  embedding_ready: boolean;
  dense_index_ready: boolean;
  bm25_index_ready: boolean;
  quality_ready: boolean;
  llm_ready: boolean;
  llm_backend: string;
  llm_model: string;
  document_count: number;
  indexed_document_count: number;
  indexing_queue?: {
    active_document_id?: string | null;
    pending_count?: number;
    last_error?: string | null;
  };
}

interface SourceStatus {
  status: string;
  discovered: number;
  indexed: number;
  unchanged: number;
  removed: number;
  failed: number;
  queued?: number;
  last_sync_at?: string | null;
}

interface PublicConfiguration {
  categories: string[];
  supported_extensions: string[];
  retrieval_profiles: string[];
}

interface OverviewData {
  documents: DocumentSummary[];
  runtime: RuntimeStatus | null;
  sources: SourceStatus | null;
  config: PublicConfiguration | null;
}

interface ActivityItem {
  id: string;
  title: string;
  meta: string;
  timestamp: number;
  icon: LucideIcon;
  tone: 'blue' | 'green' | 'purple' | 'red';
}

interface SourceGroup {
  label: string;
  extensions: string[];
  icon: LucideIcon;
  tone: string;
  bar: string;
}

const sourceGroups: SourceGroup[] = [
  {
    label: 'PDF documents',
    extensions: ['pdf'],
    icon: FileText,
    tone: 'bg-blue-50 text-blue-600',
    bar: 'bg-blue-500',
  },
  {
    label: 'Presentations',
    extensions: ['ppt', 'pptx'],
    icon: Presentation,
    tone: 'bg-violet-50 text-violet-600',
    bar: 'bg-violet-500',
  },
  {
    label: 'Word documents',
    extensions: ['doc', 'docx'],
    icon: File,
    tone: 'bg-emerald-50 text-emerald-600',
    bar: 'bg-emerald-500',
  },
  {
    label: 'Spreadsheets',
    extensions: ['xls', 'xlsx', 'csv'],
    icon: FileSpreadsheet,
    tone: 'bg-rose-50 text-rose-600',
    bar: 'bg-rose-500',
  },
];

const emptyData: OverviewData = {
  documents: [],
  runtime: null,
  sources: null,
  config: null,
};

async function readEndpoint<T>(url: string, signal?: AbortSignal): Promise<T | null> {
  try {
    const response = await fetch(url, { signal });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    return null;
  }
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('en-US').format(value);
}

function relativeTime(timestamp: number) {
  const deltaSeconds = Math.round((timestamp - Date.now()) / 1000);
  const formatter = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  const ranges: Array<[Intl.RelativeTimeFormatUnit, number]> = [
    ['year', 31_536_000],
    ['month', 2_592_000],
    ['week', 604_800],
    ['day', 86_400],
    ['hour', 3_600],
    ['minute', 60],
  ];

  for (const [unit, seconds] of ranges) {
    if (Math.abs(deltaSeconds) >= seconds) {
      return formatter.format(Math.round(deltaSeconds / seconds), unit);
    }
  }

  return 'just now';
}

function extensionOf(filename: string) {
  const extension = filename.split('.').pop();
  return extension?.toLowerCase() ?? '';
}

function ActivityIcon({ icon: Icon, tone }: Pick<ActivityItem, 'icon' | 'tone'>) {
  const toneClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-emerald-50 text-emerald-600',
    purple: 'bg-violet-50 text-violet-600',
    red: 'bg-rose-50 text-rose-600',
  };

  return (
    <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${toneClasses[tone]}`}>
      <Icon className="h-4 w-4" strokeWidth={1.8} />
    </span>
  );
}

function StatusCard({
  label,
  value,
  detail,
  positive = false,
}: {
  label: string;
  value: string;
  detail: string;
  positive?: boolean;
}) {
  return (
    <article className="min-h-[108px] rounded-xl border border-[#e5e9eb] bg-white px-5 py-[18px] shadow-[0_1px_2px_rgba(15,23,42,0.018)]">
      <p className="text-[11px] font-medium text-[#737b82]">{label}</p>
      <p className="mt-1 text-[25px] font-semibold leading-none tracking-[-0.035em] text-[#171a1d]">{value}</p>
      <p className={`mt-2 text-[10px] font-medium ${positive ? 'text-emerald-600' : 'text-[#8c949a]'}`}>{detail}</p>
    </article>
  );
}

function Panel({
  title,
  icon: Icon,
  children,
  className = '',
}: {
  title: string;
  icon?: LucideIcon;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-xl border border-[#e4e8ea] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.02)] ${className}`}>
      <div className="flex h-[56px] items-center gap-2 border-b border-[#edf0f1] px-5">
        {Icon && <Icon className="h-4 w-4 text-[#7d858c]" strokeWidth={1.8} />}
        <h2 className="text-[13px] font-semibold tracking-[-0.01em] text-[#24282c]">{title}</h2>
      </div>
      {children}
    </section>
  );
}

export default function OverviewDashboard() {
  const [data, setData] = useState<OverviewData>(emptyData);
  const [isLoading, setIsLoading] = useState(true);
  const [hasLiveData, setHasLiveData] = useState(true);
  const [activityWindow, setActivityWindow] = useState('7');

  const loadOverview = useCallback(async (signal?: AbortSignal) => {
    const [documents, runtime, sources, config] = await Promise.all([
      readEndpoint<DocumentSummary[]>('/api/backend/docs', signal),
      readEndpoint<RuntimeStatus>('/api/backend/runtime/status', signal),
      readEndpoint<SourceStatus>('/api/backend/sources/status', signal),
      readEndpoint<PublicConfiguration>('/api/backend/config/', signal),
    ]);

    setData({
      documents: Array.isArray(documents) ? documents : [],
      runtime,
      sources,
      config,
    });
    setHasLiveData(Boolean(documents || runtime || sources || config));
    setIsLoading(false);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadOverview(controller.signal);
    return () => controller.abort();
  }, [loadOverview]);

  const totalChunks = useMemo(
    () => data.documents.reduce((total, document) => total + document.chunk_count, 0),
    [data.documents],
  );
  const totalPages = useMemo(
    () => data.documents.reduce((total, document) => total + document.total_pages, 0),
    [data.documents],
  );
  const indexedDocuments = data.runtime?.indexed_document_count
    ?? data.documents.filter((document) => document.status === 'indexed').length;
  const activeFormats = new Set(data.documents.map((document) => extensionOf(document.filename)).filter(Boolean)).size;
  const configuredFormats = data.config?.supported_extensions.length ?? 0;
  const retrievalProfiles = data.config?.retrieval_profiles.length ?? 0;

  const activities = useMemo<ActivityItem[]>(() => {
    const windowInDays = activityWindow === 'all' ? Number.POSITIVE_INFINITY : Number(activityWindow);
    const cutoff = Date.now() - windowInDays * 86_400_000;

    return data.documents
      .map((document): ActivityItem => {
        const timestamp = new Date(document.created_at).getTime();
        const failed = document.status === 'failed';
        const pending = document.status === 'processing' || document.status === 'queued';

        return {
          id: document.id,
          title: failed
            ? `Indexing failed for ${document.filename}`
            : pending
              ? `Indexing ${document.filename}`
              : `${document.filename} indexed`,
          meta: `${document.category} · ${formatNumber(document.chunk_count)} chunks`,
          timestamp: Number.isFinite(timestamp) ? timestamp : 0,
          icon: failed ? AlertTriangle : pending ? RefreshCw : FileCheck2,
          tone: failed ? 'red' : pending ? 'purple' : 'blue',
        };
      })
      .filter((activity) => activityWindow === 'all' || activity.timestamp >= cutoff)
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, 5);
  }, [activityWindow, data.documents]);

  const sourceUsage = useMemo(() => {
    const maximum = Math.max(
      1,
      ...sourceGroups.map((group) =>
        data.documents.filter((document) => group.extensions.includes(extensionOf(document.filename))).length,
      ),
    );

    return sourceGroups.map((group) => {
      const count = data.documents.filter((document) => group.extensions.includes(extensionOf(document.filename))).length;
      return { ...group, count, percentage: Math.round((count / maximum) * 100) };
    });
  }, [data.documents]);

  const runtimeRows = [
    { label: 'Embedding model', ready: data.runtime?.embedding_ready ?? false },
    { label: 'Fast retrieval', ready: data.runtime?.dense_index_ready ?? false },
    { label: 'Quality retrieval', ready: data.runtime?.quality_ready ?? false },
  ];

  const exportSnapshot = () => {
    const snapshot = {
      generated_at: new Date().toISOString(),
      document_count: data.documents.length,
      indexed_document_count: indexedDocuments,
      chunk_count: totalChunks,
      page_count: totalPages,
      runtime: data.runtime,
      source_sync: data.sources,
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `docmind-overview-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const displayValue = (value: number) => (isLoading ? '—' : formatNumber(value));

  return (
    <div className="min-h-screen bg-[#f7f9fa]">
      <header className="flex h-[58px] items-center justify-between border-b border-[#e6e9eb] bg-white px-4 sm:px-6 lg:px-7">
        <div>
          <h1 className="text-[15px] font-semibold tracking-[-0.02em] text-[#202428]">Overview</h1>
          <p className="sr-only">DocMind workspace overview</p>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="activity-window" className="sr-only">Activity period</label>
          <select
            id="activity-window"
            value={activityWindow}
            onChange={(event) => setActivityWindow(event.target.value)}
            className="h-8 rounded-lg border border-[#e4e8ea] bg-white px-3 text-[11px] font-medium text-[#4d555c] shadow-[0_1px_2px_rgba(15,23,42,0.02)] outline-none transition-colors focus:border-[#aab1b7]"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="all">All time</option>
          </select>
          <button
            type="button"
            onClick={exportSnapshot}
            aria-label="Download overview snapshot"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-[#e4e8ea] bg-white text-[#6e767d] transition-colors hover:border-[#cdd2d6] hover:text-[#252a2e]"
          >
            <Download className="h-3.5 w-3.5" strokeWidth={1.8} />
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-[1220px] px-4 py-5 sm:px-6 lg:px-7 lg:py-6">
        {!hasLiveData && !isLoading && (
          <div className="mb-4 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-800">
            <AlertTriangle className="h-3.5 w-3.5" />
            Live workspace data is unavailable. Start the FastAPI service, then refresh this page.
          </div>
        )}

        <section aria-label="Workspace statistics" className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
          <StatusCard
            label="Total documents"
            value={displayValue(data.documents.length)}
            detail={`${formatNumber(indexedDocuments)} indexed locally`}
            positive={indexedDocuments > 0}
          />
          <StatusCard
            label="Indexed chunks"
            value={displayValue(totalChunks)}
            detail={`${formatNumber(totalPages)} source pages`}
            positive={totalChunks > 0}
          />
          <StatusCard
            label="Source formats"
            value={displayValue(activeFormats)}
            detail={`of ${formatNumber(configuredFormats)} supported`}
          />
          <StatusCard
            label="Retrieval profiles"
            value={displayValue(retrievalProfiles)}
            detail={data.runtime?.quality_ready ? 'Fast and Quality ready' : 'Fast mode available'}
            positive={Boolean(data.runtime?.quality_ready)}
          />
        </section>

        <div className="mt-[18px] grid grid-cols-1 gap-[18px] lg:grid-cols-[minmax(0,2.05fr)_minmax(260px,0.95fr)]">
          <Panel title="Recent activity" icon={Sparkles} className="min-h-[360px] overflow-hidden">
            {activities.length > 0 ? (
              <ul className="divide-y divide-[#edf0f1]">
                {activities.map((activity) => (
                  <li key={activity.id} className="flex min-h-[60px] items-center gap-3 px-5 py-2.5">
                    <ActivityIcon icon={activity.icon} tone={activity.tone} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[12px] font-semibold text-[#30353a]" title={activity.title}>
                        {activity.title}
                      </p>
                      <p className="mt-0.5 truncate text-[10px] text-[#8b9399]">{activity.meta}</p>
                    </div>
                    <time
                      dateTime={new Date(activity.timestamp).toISOString()}
                      className="shrink-0 text-[10px] text-[#a0a7ac]"
                    >
                      {relativeTime(activity.timestamp)}
                    </time>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="flex min-h-[300px] flex-col items-center justify-center px-6 text-center">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f2f4f5] text-[#8a9298]">
                  <Search className="h-4 w-4" strokeWidth={1.8} />
                </span>
                <p className="mt-3 text-[12px] font-medium text-[#4e555b]">No activity in this period</p>
                <p className="mt-1 max-w-[240px] text-[10px] leading-4 text-[#969da3]">
                  Upload or synchronize a document to start building your knowledge history.
                </p>
              </div>
            )}
          </Panel>

          <div className="grid content-start gap-[18px]">
            <Panel title="Source usage" icon={Database}>
              <ul className="space-y-[15px] p-5">
                {sourceUsage.map((source) => {
                  const Icon = source.icon;
                  return (
                    <li key={source.label}>
                      <div className="flex items-center gap-2.5">
                        <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${source.tone}`}>
                          <Icon className="h-3.5 w-3.5" strokeWidth={1.8} />
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-3">
                            <span className="truncate text-[11px] font-semibold text-[#3b4146]">{source.label}</span>
                            <span className="shrink-0 text-[9px] text-[#8d959b]">
                              {formatNumber(source.count)} {source.count === 1 ? 'document' : 'documents'}
                            </span>
                          </div>
                          <div className="mt-2 h-[3px] overflow-hidden rounded-full bg-[#edf0f1]">
                            <div
                              className={`h-full rounded-full ${source.bar}`}
                              style={{ width: `${source.count === 0 ? 0 : Math.max(12, source.percentage)}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </Panel>

            <Panel title="Runtime status" icon={FolderSync}>
              <div className="space-y-4 p-5">
                {runtimeRows.map((row) => (
                  <div key={row.label}>
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-[10px] font-medium text-[#626a71]">{row.label}</span>
                      <span className={`flex items-center gap-1 text-[9px] font-semibold ${row.ready ? 'text-emerald-600' : 'text-amber-600'}`}>
                        {row.ready ? <CheckCircle2 className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
                        {row.ready ? 'Ready' : 'Not ready'}
                      </span>
                    </div>
                    <div className="mt-2 h-[3px] overflow-hidden rounded-full bg-[#edf0f1]">
                      <div className={`h-full rounded-full ${row.ready ? 'w-full bg-emerald-500' : 'w-1/4 bg-amber-400'}`} />
                    </div>
                  </div>
                ))}

                <div className="border-t border-[#edf0f1] pt-3">
                  <p className="truncate text-[9px] text-[#939aa0]" title={data.runtime?.llm_model || 'No local model loaded'}>
                    {data.runtime?.llm_ready ? data.runtime.llm_model : 'Local model not loaded'}
                  </p>
                </div>
              </div>
            </Panel>
          </div>
        </div>
      </div>
    </div>
  );
}
