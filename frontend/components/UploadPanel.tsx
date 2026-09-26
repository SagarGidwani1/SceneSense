'use client';
import React, { useRef, useState } from 'react';
import { UploadCloud, Loader2 } from 'lucide-react';
import { uploadVideo, analyzeVideo, ApiError } from '../lib/api';
import { UploadResult } from '../lib/types';

interface UploadPanelProps {
  onUploaded: (video: UploadResult) => void;
}

export const UploadPanel: React.FC<UploadPanelProps> = ({ onUploaded }) => {
  const [busy, setBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setBusy(true);
    setError('');
    try {
      const uploaded = await uploadVideo(file);
      onUploaded(uploaded);
      await analyzeVideo(uploaded.video_id);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Upload failed.');
    } finally {
      setBusy(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div>
      <label
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`flex flex-col items-center justify-center gap-2 rounded-md border border-dashed px-4 py-6 text-center cursor-pointer transition-colors ${
          dragOver ? 'border-accent bg-accent/5' : 'border-line hover:border-muted'
        }`}
      >
        {busy ? (
          <Loader2 size={18} className="text-accent animate-spin-slow" />
        ) : (
          <UploadCloud size={18} className="text-muted" />
        )}
        <div className="text-xs text-ink font-medium">
          {busy ? 'Uploading…' : dragOver ? 'Drop to upload' : 'Drag video here'}
        </div>
        <div className="text-[11px] text-muted">or click to browse</div>
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          disabled={busy}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = '';
          }}
        />
      </label>
      {error && <p className="mt-2 text-[11px] text-rejected">{error}</p>}
    </div>
  );
};
