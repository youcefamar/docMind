'use client';

import React, { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, FolderPlus, CheckCircle2, AlertCircle, RefreshCw, Layers, HardDrive, BookOpen } from 'lucide-react';
import { getApiErrorMessage, readApiPayload } from '../lib/api';

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

interface SyncStatus {
  status: string;
  source_dir: string;
  discovered: number;
  indexed: number;
  unchanged: number;
  removed: number;
  failed: number;
  queued?: number;
  rebuild_queued?: boolean;
  last_sync_at?: string | null;
  error?: string | null;
  failures?: Array<{ path: string; error: string }>;
  warnings?: string[];
}

export default function UploadPanel() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [supportedExtensions, setSupportedExtensions] = useState<string[]>([]);
  const [maxFileSizeMb, setMaxFileSizeMb] = useState(50);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  const fetchConfig = async () => {
    try {
      const res = await fetch('/api/backend/config/');
      if (!res.ok) return;
      const config = await readApiPayload<Record<string, any>>(res);
      if (!config) return;
      setCategories(config.categories || []);
      setSupportedExtensions(config.supported_extensions || []);
      setMaxFileSizeMb(config.max_file_size_mb || 50);
      setSelectedCategory((current) => current || config.default_category || '');
    } catch (err) {
      console.error('Failed to fetch backend configuration:', err);
    }
  };

  const fetchDocuments = async (): Promise<DocumentSummary[]> => {
    setIsLoadingDocs(true);
    try {
      const res = await fetch('/api/backend/docs');
      if (res.ok) {
        const data = await readApiPayload<unknown>(res);
        if (Array.isArray(data)) {
          const nextDocuments = data as DocumentSummary[];
          setDocuments(nextDocuments);
          return nextDocuments;
        }
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setIsLoadingDocs(false);
    }
    return [];
  };

  const refreshDocumentsUntilSettled = async () => {
    const latest = await fetchDocuments();
    if (latest.some((document) => document.status === 'processing' || document.status === 'queued')) {
      window.setTimeout(refreshDocumentsUntilSettled, 1500);
    }
  };

  const fetchSyncStatus = async (): Promise<SyncStatus | null> => {
    try {
      const res = await fetch('/api/backend/sources/status');
      if (res.ok) {
        const data = await readApiPayload<SyncStatus>(res);
        if (data && typeof data === 'object') {
          setSyncStatus(data);
          return data;
        }
      }
    } catch (err) {
      console.error('Failed to fetch knowledge-folder status:', err);
    }
    return null;
  };

  useEffect(() => {
    fetchConfig();
    fetchDocuments();
    fetchSyncStatus();
  }, []);

  const handleSync = async () => {
    setIsSyncing(true);
    setUploadMessage(null);
    try {
      const res = await fetch('/api/backend/sources/sync', { method: 'POST' });
      const payload = await readApiPayload<{ status?: SyncStatus }>(res);
      if (!res.ok) throw new Error(getApiErrorMessage(payload, 'Knowledge-folder sync failed'));
      if (!payload?.status) throw new Error('Knowledge-folder sync returned an invalid response.');
      setSyncStatus(payload.status);
      const poll = async () => {
        const latest = await fetchSyncStatus();
        if (latest?.status === 'queued' || latest?.status === 'syncing') {
          window.setTimeout(poll, 750);
        } else {
          setIsSyncing(false);
          await fetchDocuments();
          refreshDocumentsUntilSettled();
        }
      };
      window.setTimeout(poll, 250);
    } catch (err: any) {
      setIsSyncing(false);
      setUploadMessage({ type: 'error', text: err.message || 'Knowledge-folder sync failed.' });
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadMessage(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    formData.append('category', selectedCategory);

    try {
      const res = await fetch('/api/backend/upload', {
        method: 'POST',
        body: formData,
      });

      const payload = await readApiPayload<unknown>(res);
      if (!res.ok) throw new Error(getApiErrorMessage(payload, `Upload failed (HTTP ${res.status})`));
      if (!Array.isArray(payload)) throw new Error('Upload returned an invalid response.');
      const result = payload as DocumentSummary[];
      const indexedCount = result.filter((item: DocumentSummary) => item.status === 'indexed').length;
      const pendingCount = result.length - indexedCount;
      setUploadMessage({
        type: 'success',
        text: `Processed ${result.length} document(s): ${indexedCount} indexed${pendingCount ? `, ${pendingCount} awaiting indexing` : ''}.`,
      });
      setFiles(null);
      refreshDocumentsUntilSettled();
    } catch (err: any) {
      setUploadMessage({
        type: 'error',
        text: err.message || 'Error processing document upload.',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete '${filename}' and remove its local index entries?`)) {
      return;
    }

    try {
      const res = await fetch(`/api/backend/doc/${docId}`, {
        method: 'DELETE',
      });

      if (res.ok) {
        setDocuments((prev) => prev.filter((d) => d.id !== docId));
      } else {
        alert('Failed to delete document');
      }
    } catch (err) {
      console.error('Delete error:', err);
    }
  };

  const handleReindex = async (docId: string, filename: string) => {
    try {
      const res = await fetch(`/api/backend/doc/${docId}/reindex`, { method: 'POST' });
      const payload = await readApiPayload<unknown>(res);
      if (!res.ok) {
        throw new Error(getApiErrorMessage(payload, `Re-index failed (HTTP ${res.status})`));
      }
      setUploadMessage({ type: 'success', text: `Re-indexed '${filename}'.` });
      refreshDocumentsUntilSettled();
    } catch (err: any) {
      setUploadMessage({ type: 'error', text: err.message || `Could not re-index '${filename}'.` });
    }
  };

  const statusClass = (status: string) => {
    if (status === 'indexed') return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    if (status === 'failed') return 'border-rose-200 bg-rose-50 text-rose-700';
    return 'border-amber-200 bg-amber-50 text-amber-700';
  };

  const filteredDocs = documents.filter(
    (doc) =>
      doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPagesSum = documents.reduce((acc, d) => acc + d.total_pages, 0);
  const totalChunksSum = documents.reduce((acc, d) => acc + d.chunk_count, 0);

  return (
    <div className="space-y-6">
      
      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="flex items-center gap-4 rounded-2xl border border-[#e8e8e5] bg-white p-5 shadow-[0_6px_20px_rgba(32,33,36,0.03)]">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-slate-600">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Total documents</p>
            <h3 className="text-2xl font-semibold tracking-tight text-slate-900">{documents.length}</h3>
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-2xl border border-[#e8e8e5] bg-white p-5 shadow-[0_6px_20px_rgba(32,33,36,0.03)]">
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-emerald-600">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Indexed chunks</p>
            <h3 className="text-2xl font-semibold tracking-tight text-slate-900">{totalChunksSum}</h3>
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-2xl border border-[#e8e8e5] bg-white p-5 shadow-[0_6px_20px_rgba(32,33,36,0.03)]">
          <div className="rounded-xl border border-sky-200 bg-sky-50 p-3 text-sky-600">
            <HardDrive className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Document pages</p>
            <h3 className="text-2xl font-semibold tracking-tight text-slate-900">{totalPagesSum}</h3>
          </div>
        </div>
      </div>

      {/* Upload Dropzone Form */}
      <div className="rounded-2xl border border-[#e8e8e5] bg-white p-5 shadow-[0_10px_30px_rgba(32,33,36,0.035)] sm:p-6">
        <h2 className="mb-1 flex items-center gap-2 text-lg font-semibold tracking-tight text-slate-900">
          <FolderPlus className="h-5 w-5 text-slate-500" />
          <span>Upload & Index Documents</span>
        </h2>
        <p className="mb-6 text-xs text-slate-500">
          Documents are extracted, chunked, embedded locally, and saved into the configured knowledge store.
        </p>

        <form onSubmit={handleUpload} className="space-y-5">
          {/* Category Selector */}
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-slate-500">
              Assign Category Tag
            </label>
            <div className="flex flex-wrap gap-2">
              {categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                    selectedCategory === cat
                      ? 'border-slate-900 bg-slate-900 text-white shadow-sm'
                      : 'border-[#e3e3e0] bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* File Input Box */}
          <div className="rounded-2xl border-2 border-dashed border-[#dfe0dc] bg-[#fafaf9] p-8 text-center transition-colors hover:border-slate-400 hover:bg-white">
            <input
              type="file"
              accept={supportedExtensions.join(',')}
              multiple
              onChange={(e) => setFiles(e.target.files)}
              className="hidden"
              id="file-upload-input"
            />
            <label htmlFor="file-upload-input" className="cursor-pointer flex flex-col items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm">
                <Upload className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-700">
                  {files && files.length > 0
                    ? `${files.length} file(s) selected`
                    : `Click or drag supported files here to upload`}
                </p>
                <p className="mt-1 text-xs text-slate-400">
                  Supports {supportedExtensions.join(', ') || 'configured file types'} up to {maxFileSizeMb}MB each
                </p>
              </div>
            </label>

            {/* Selected File Names */}
            {files && files.length > 0 && (
              <div className="mt-4 flex flex-wrap justify-center gap-2 border-t border-[#e7e7e4] pt-4">
                {Array.from(files).map((f, i) => (
                  <span key={i} className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600">
                    <FileText className="w-3.5 h-3.5" />
                    {f.name}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div className="flex items-center justify-end">
            <button
              type="submit"
              disabled={isUploading || !files || files.length === 0}
              className="flex items-center gap-2 rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-slate-700 disabled:opacity-40"
            >
              {isUploading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Processing & Embedding...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Upload to Vector Database</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Upload Status Banner */}
        {uploadMessage && (
          <div
            className={`mt-4 p-4 rounded-xl flex items-center gap-3 text-xs border ${
              uploadMessage.type === 'success'
                ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                : 'border-rose-200 bg-rose-50 text-rose-700'
            }`}
          >
            {uploadMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
            )}
            <span>{uploadMessage.text}</span>
          </div>
        )}
      </div>

      {/* Document Catalog Table */}
      <div className="rounded-2xl border border-[#e8e8e5] bg-white p-5 shadow-[0_10px_30px_rgba(32,33,36,0.035)] sm:p-6">
        <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h3 className="text-lg font-semibold tracking-tight text-slate-900">Indexed knowledge base</h3>
            <p className="text-xs text-slate-500">Manage uploads or synchronize the configured knowledge folder</p>
            {syncStatus && (
              <p className="mt-1 text-[10px] text-slate-400" title={syncStatus.source_dir}>
                Folder sync: <span className="text-slate-600">{syncStatus.status}</span>
                {syncStatus.last_sync_at ? ` · ${new Date(syncStatus.last_sync_at).toLocaleString()}` : ''}
                {syncStatus.queued ? ` · ${syncStatus.queued} document(s) queued for indexing` : ''}
                {syncStatus.rebuild_queued ? ' · safe rebuild queued' : ''}
              </p>
            )}
            {syncStatus?.warnings?.map((warning) => (
              <p key={warning} className="mt-1 max-w-xl truncate text-[10px] text-amber-700" title={warning}>
                {warning}
              </p>
            ))}
            {syncStatus && syncStatus.failures && syncStatus.failures.length > 0 && (
              <p
                className="mt-1 max-w-xl truncate text-[10px] text-amber-700"
                title={syncStatus.failures.map((failure) => `${failure.path}: ${failure.error}`).join('\n')}
              >
                {syncStatus.failures.length} source file(s) need attention.
              </p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSync}
              disabled={isSyncing}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300 hover:text-slate-950 disabled:opacity-50"
              title={syncStatus?.source_dir || 'Synchronize configured knowledge folder'}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              {isSyncing ? 'Syncing…' : 'Sync folder'}
            </button>
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="rounded-xl border border-[#e3e3e0] bg-[#fafaf9] px-3.5 py-1.5 text-xs text-slate-700 placeholder:text-slate-400 focus:border-slate-400 focus:bg-white focus:outline-none"
            />
            <button
              onClick={fetchDocuments}
              className="rounded-xl border border-[#e3e3e0] bg-white p-2 text-slate-500 transition-colors hover:border-slate-300 hover:text-slate-900"
              title="Refresh Document List"
            >
              <RefreshCw className={`w-4 h-4 ${isLoadingDocs ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Table View */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-xs text-slate-600">
            <thead>
              <tr className="border-b border-[#e8e8e5] bg-[#fafaf9] text-[10px] uppercase tracking-wider text-slate-400">
                <th className="p-3">Document Name</th>
                <th className="p-3">Category</th>
                <th className="p-3">Total Pages</th>
                <th className="p-3">Chunks</th>
                <th className="p-3">Status</th>
                <th className="p-3">Date Added</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#eeeeeb]">
              {filteredDocs.length > 0 ? (
                filteredDocs.map((doc) => (
                  <tr key={doc.id} className="transition-colors hover:bg-[#fafaf9]">
                    <td className="flex items-center gap-2 p-3 font-medium text-slate-700">
                      <FileText className="h-4 w-4 flex-shrink-0 text-slate-400" />
                      <span className="truncate max-w-xs">{doc.filename}</span>
                    </td>
                    <td className="p-3">
                      <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                        {doc.category}
                      </span>
                    </td>
                    <td className="p-3">{doc.total_pages} pages</td>
                    <td className="p-3">{doc.chunk_count} chunks</td>
                    <td className="p-3">
                      <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${statusClass(doc.status)}`}>
                        {doc.status.replaceAll('_', ' ')}
                      </span>
                      {doc.error_detail && (
                        <p className="mt-1 max-w-xs truncate text-[10px] text-rose-600" title={doc.error_detail}>
                          {doc.error_detail}
                        </p>
                      )}
                    </td>
                    <td className="p-3 text-slate-400">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Recent'}
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex justify-end gap-1">
                        {doc.status !== 'indexed' && (
                          <button
                            onClick={() => handleReindex(doc.id, doc.filename)}
                            className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-800"
                            title="Re-index document"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-600"
                          title="Delete document and local index entries"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    {isLoadingDocs ? 'Loading document catalog...' : 'No documents uploaded yet. Upload a supported file to get started!'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
