import React from 'react';
import UploadPanel from '@/components/UploadPanel';

export default function AdminPage() {
  return (
    <div className="px-4 py-5 sm:px-6 lg:px-7 lg:py-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-7">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Workspace</p>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950">Knowledge base</h1>
          <p className="mt-1 text-sm text-slate-500">
            Upload supported documents, organize them with configured categories, and manage local indexes.
          </p>
        </div>

        <UploadPanel />
      </div>
    </div>
  );
}
