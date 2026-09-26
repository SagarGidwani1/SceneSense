'use client';
import React, { useState } from 'react';
import { ChevronDown, ChevronRight, ShieldX } from 'lucide-react';
import { FinalBreak, Candidate } from '../../lib/types';
import { formatTime } from '../../lib/format';

interface BreaksTabProps {
  finalBreaks: FinalBreak[];
  candidates: Candidate[];
  onSeek: (t: number) => void;
}

function nearestCandidate(b: FinalBreak, candidates: Candidate[]): Candidate | undefined {
  return candidates.reduce<Candidate | undefined>((best, c) => {
    const diff = Math.abs(c.timestamp - b.timestamp);
    if (diff > 1.5) return best;
    if (!best || diff < Math.abs(best.timestamp - b.timestamp)) return c;
    return best;
  }, undefined);
}

export const BreaksTab: React.FC<BreaksTabProps> = ({ finalBreaks, candidates, onSeek }) => {
  const [open, setOpen] = useState<string | null>(null);

  if (finalBreaks.length === 0) {
    return <p className="text-xs text-muted">No breaks were selected for this video.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {finalBreaks.map((b) => {
        const candidate = nearestCandidate(b, candidates);
        const blocked = candidate?.brand_evaluations.filter((e) => e.blocked) ?? [];
        const isOpen = open === b.break_id;
        return (
          <div key={b.break_id} className="rounded-md border border-line bg-surface p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => onSeek(b.timestamp)}
                  className="font-mono text-sm text-accent hover:underline"
                >
                  {formatTime(b.timestamp)}
                </button>
                <span className="text-[11px] text-muted">WHERE {Math.round(b.where_score)}</span>
              </div>
              <div className="text-right">
                <div className="text-sm text-ink font-medium">{b.brand.brand_name}</div>
                <div className="text-[11px] text-muted">match {Math.round(b.brand.match_score)}%</div>
              </div>
            </div>

            <p className="text-xs text-muted mt-2">{b.scene_before} → {b.scene_after}</p>
            <p className="text-xs text-ink mt-1">{b.brand.reason}</p>

            {b.reasons.length > 0 && (
              <ul className="mt-2 flex flex-wrap gap-1.5">
                {b.reasons.map((r, i) => (
                  <li key={i} className="text-[10px] rounded bg-surface2 border border-line px-1.5 py-0.5 text-muted">
                    {r}
                  </li>
                ))}
              </ul>
            )}

            {candidate && candidate.brand_evaluations.length > 0 && (
              <div className="mt-3 pt-3 border-t border-line">
                <button
                  onClick={() => setOpen(isOpen ? null : b.break_id)}
                  className="flex items-center gap-1 text-[11px] text-muted hover:text-ink"
                >
                  {isOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                  All brand evaluations ({candidate.brand_evaluations.length}) · {blocked.length} blocked
                </button>
                {isOpen && (
                  <ul className="mt-2 flex flex-col gap-1.5">
                    {candidate.brand_evaluations.map((ev) => (
                      <li
                        key={ev.brand_id}
                        className={`rounded border px-2.5 py-1.5 text-[11px] ${
                          ev.blocked ? 'border-rejected/40 bg-rejected/10' : 'border-line bg-surface2'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`font-medium ${ev.blocked ? 'text-rejected' : 'text-ink'}`}>
                            {ev.blocked && <ShieldX size={11} className="inline mr-1 -mt-0.5" />}
                            {ev.brand_name}
                          </span>
                          <span className="text-muted">relevance {Math.round(ev.relevance)}</span>
                        </div>
                        <p className={`mt-0.5 ${ev.blocked ? 'text-rejected' : 'text-muted'}`}>
                          {ev.blocked ? `Blocked by: ${ev.blocked_by.join(', ')}` : ev.reason}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
