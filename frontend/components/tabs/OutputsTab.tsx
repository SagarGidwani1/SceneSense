'use client';
import React, { useMemo, useState } from 'react';
import { Download } from 'lucide-react';
import { AuditRecord, AuditEngine, AuditStatus } from '../../lib/types';
import { formatTime } from '../../lib/format';
import { debugUrl } from '../../lib/api';
import { VmapViewer } from '../VmapViewer';

interface OutputsTabProps {
  videoId: string;
  vmapXml: string;
  auditLogs: AuditRecord[];
}

const ENGINES: Array<AuditEngine | 'ALL'> = ['ALL', 'WHERE', 'WHETHER', 'WHAT'];
const STATUSES: Array<AuditStatus | 'ALL'> = ['ALL', 'ACCEPTED', 'REJECTED', 'BLOCKED'];

const STATUS_COLOR: Record<AuditStatus, string> = {
  ACCEPTED: 'text-accepted',
  REJECTED: 'text-warn',
  BLOCKED: 'text-rejected',
};

export const OutputsTab: React.FC<OutputsTabProps> = ({ videoId, vmapXml, auditLogs }) => {
  const [engine, setEngine] = useState<AuditEngine | 'ALL'>('ALL');
  const [status, setStatus] = useState<AuditStatus | 'ALL'>('ALL');

  const filtered = useMemo(
    () => auditLogs.filter((r) => (engine === 'ALL' || r.engine === engine) && (status === 'ALL' || r.status === status)),
    [auditLogs, engine, status]
  );

  return (
    <div className="flex flex-col gap-6">
      <VmapViewer vmapXml={vmapXml} />

      <a
        href={debugUrl(videoId)}
        download
        className="inline-flex items-center gap-1.5 self-start text-[11px] text-muted hover:text-ink rounded border border-line px-2.5 py-1.5"
      >
        <Download size={12} /> Download debug JSON
      </a>

      <div>
        <div className="flex items-center gap-3 mb-2">
          <span className="text-xs font-medium text-ink">Audit log</span>
          <select value={engine} onChange={(e) => setEngine(e.target.value as AuditEngine | 'ALL')} className="bg-surface2 border border-line rounded text-[11px] text-ink px-1.5 py-1">
            {ENGINES.map((e) => <option key={e} value={e}>{e}</option>)}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value as AuditStatus | 'ALL')} className="bg-surface2 border border-line rounded text-[11px] text-ink px-1.5 py-1">
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <table className="w-full text-[11px] border-collapse">
          <thead>
            <tr className="text-left text-muted border-b border-line">
              <th className="py-2 pr-3 font-normal">Time</th>
              <th className="py-2 pr-3 font-normal">Engine</th>
              <th className="py-2 pr-3 font-normal">Status</th>
              <th className="py-2 pr-3 font-normal">Reason</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r, i) => (
              <tr key={i} className="border-b border-line/60">
                <td className="py-2 pr-3 font-mono text-muted">{formatTime(r.timestamp)}</td>
                <td className="py-2 pr-3 text-muted">{r.engine}</td>
                <td className={`py-2 pr-3 ${STATUS_COLOR[r.status]}`}>{r.status}</td>
                <td className="py-2 pr-3 text-ink">{r.reason} <span className="text-muted">({r.reason_code})</span></td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={4} className="py-3 text-muted">No matching audit entries.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
