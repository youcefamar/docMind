import React from 'react';
import UploadPanel from '@/components/UploadPanel';

export default function AdminPage() {
  return (
    <div className="mx-auto max-w-6xl py-1 sm:py-2">
      <div className="mb-7">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Workspace</p>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-950">Knowledge base</h1>
        <p className="mt-1 text-sm text-slate-500">
          Upload supported documents, organize them with configured categories, and manage local indexes.
        </p>
      </div>

      <UploadPanel />
    </div>
  );
}
