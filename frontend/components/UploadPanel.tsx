'use client';

import React, { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, FolderPlus, CheckCircle2, AlertCircle, RefreshCw, Layers, HardDrive, BookOpen } from 'lucide-react';

interface DocumentSummary {
  id: string;
  filename: string;
  category: string;
  chunk_count: number;
  total_pages: number;
  created_at: string;
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

  const fetchConfig = async () => {
    try {
      const res = await fetch('/api/backend/config/');
      if (!res.ok) return;
      const config = await res.json();
      setCategories(config.categories || []);
      setSupportedExtensions(config.supported_extensions || []);
      setMaxFileSizeMb(config.max_file_size_mb || 50);
      setSelectedCategory((current) => current || config.default_category || '');
    } catch (err) {
      console.error('Failed to fetch backend configuration:', err);
    }
  };

  const fetchDocuments = async () => {
    setIsLoadingDocs(true);
    try {
      const res = await fetch('/api/backend/docs');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchConfig();
    fetchDocuments();
  }, []);

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

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Upload failed');
      }

      const result = await res.json();
      setUploadMessage({
        type: 'success',
        text: `Successfully processed and indexed ${result.length} document(s) under category '${selectedCategory}'.`,
      });
      setFiles(null);
      fetchDocuments();
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

  const filteredDocs = documents.filter(
    (doc) =>
      doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPagesSum = documents.reduce((acc, d) => acc + d.total_pages, 0);
  const totalChunksSum = documents.reduce((acc, d) => acc + d.chunk_count, 0);

  return (
    <div className="space-y-8">
      
      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card p-5 rounded-2xl border border-gray-800 flex items-center gap-4">
          <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium">Total Documents</p>
            <h3 className="text-2xl font-bold text-white">{documents.length}</h3>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-gray-800 flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium">Indexed Chunks</p>
            <h3 className="text-2xl font-bold text-white">{totalChunksSum}</h3>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-gray-800 flex items-center gap-4">
          <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl border border-cyan-500/20">
            <HardDrive className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium">Total Document Pages</p>
            <h3 className="text-2xl font-bold text-white">{totalPagesSum}</h3>
          </div>
        </div>
      </div>

      {/* Upload Dropzone Form */}
      <div className="glass-panel p-6 rounded-2xl border border-gray-800 shadow-xl">
        <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-1">
          <FolderPlus className="w-5 h-5 text-indigo-400" />
          <span>Upload & Index Documents</span>
        </h2>
        <p className="text-xs text-gray-400 mb-6">
          Documents are extracted, chunked, embedded locally, and saved into the configured knowledge store.
        </p>

        <form onSubmit={handleUpload} className="space-y-5">
          {/* Category Selector */}
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
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
                      ? 'bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-600/30'
                      : 'bg-gray-900/60 border-gray-800 text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* File Input Box */}
          <div className="border-2 border-dashed border-gray-700 hover:border-indigo-500/60 rounded-2xl p-8 text-center bg-gray-950/40 transition-colors">
            <input
              type="file"
              accept={supportedExtensions.join(',')}
              multiple
              onChange={(e) => setFiles(e.target.files)}
              className="hidden"
              id="file-upload-input"
            />
            <label htmlFor="file-upload-input" className="cursor-pointer flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                <Upload className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-200">
                  {files && files.length > 0
                    ? `${files.length} file(s) selected`
                    : `Click or drag supported files here to upload`}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Supports {supportedExtensions.join(', ') || 'configured file types'} up to {maxFileSizeMb}MB each
                </p>
              </div>
            </label>

            {/* Selected File Names */}
            {files && files.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-800 flex flex-wrap justify-center gap-2">
                {Array.from(files).map((f, i) => (
                  <span key={i} className="text-xs bg-gray-800 text-indigo-300 px-3 py-1 rounded-md flex items-center gap-1.5 border border-gray-700">
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
              className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all"
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
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                : 'bg-red-500/10 text-red-300 border-red-500/20'
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
      <div className="glass-panel p-6 rounded-2xl border border-gray-800 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-bold text-white">Indexed Knowledge Base</h3>
            <p className="text-xs text-gray-400">Manage uploaded PDF documents and active vector embeddings</p>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-gray-950 px-3.5 py-1.5 text-xs text-gray-200 placeholder-gray-500 rounded-xl border border-gray-800 focus:outline-none focus:border-indigo-500"
            />
            <button
              onClick={fetchDocuments}
              className="p-2 rounded-xl bg-gray-900 text-gray-400 hover:text-white border border-gray-800 transition-colors"
              title="Refresh Document List"
            >
              <RefreshCw className={`w-4 h-4 ${isLoadingDocs ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Table View */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-300 border-collapse">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/50 text-gray-400 uppercase text-[10px] tracking-wider">
                <th className="p-3">Document Name</th>
                <th className="p-3">Category</th>
                <th className="p-3">Total Pages</th>
                <th className="p-3">Chunks</th>
                <th className="p-3">Date Added</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {filteredDocs.length > 0 ? (
                filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-800/30 transition-colors">
                    <td className="p-3 font-medium text-white flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                      <span className="truncate max-w-xs">{doc.filename}</span>
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                        {doc.category}
                      </span>
                    </td>
                    <td className="p-3">{doc.total_pages} pages</td>
                    <td className="p-3">{doc.chunk_count} chunks</td>
                    <td className="p-3 text-gray-400">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Recent'}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        title="Delete document embeddings"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="text-center p-8 text-gray-500">
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
