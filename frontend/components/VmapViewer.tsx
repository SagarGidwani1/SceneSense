'use client';
import React, { useState } from 'react';
import { Copy, Download, Check } from 'lucide-react';

interface VmapViewerProps {
  vmapXml: string;
}

export const VmapViewer: React.FC<VmapViewerProps> = ({ vmapXml }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(vmapXml).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  const handleDownload = () => {
    const blob = new Blob([vmapXml], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'manifest.vmap.xml';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!vmapXml) return <p className="text-xs text-muted">No VMAP generated yet.</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-medium text-ink flex-1">VMAP manifest</span>
        <button onClick={handleCopy} className="flex items-center gap-1 text-[11px] text-muted hover:text-ink rounded border border-line px-2 py-1">
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
        <button onClick={handleDownload} className="flex items-center gap-1 text-[11px] text-base bg-accent rounded px-2 py-1">
          <Download size={12} />
          Download
        </button>
      </div>
      <pre className="rounded border border-line bg-surface2 p-3 text-[11px] font-mono text-muted overflow-auto max-h-96 whitespace-pre-wrap break-all">
        {vmapXml}
      </pre>
    </div>
  );
};
