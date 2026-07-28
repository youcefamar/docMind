import React from 'react';
import UploadPanel from '@/components/UploadPanel';

export default function AdminPage() {
  return (
    <div className="max-w-6xl mx-auto py-2">
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Document Administration</h1>
        <p className="text-sm text-gray-400">
          Upload supported documents, organize them with configured categories, and manage local indexes.
        </p>
      </div>

      <UploadPanel />
    </div>
  );
}
