'use client';
import React from 'react';
import { Candidate } from '../../lib/types';
import { formatTime } from '../../lib/format';

interface CandidatesTabProps {
  candidates: Candidate[];
  onSeek: (t: number) => void;
}

const Check: React.FC<{ ok: boolean }> = ({ ok }) => (
  <span className={ok ? 'text-accepted' : 'text-muted/40'}>{ok ? '✓' : '–'}</span>
);

export const CandidatesTab: React.FC<CandidatesTabProps> = ({ candidates, onSeek }) => (
  <div className="overflow-x-auto">
    <table className="w-full text-[11px] border-collapse">
      <thead>
        <tr className="text-left text-muted border-b border-line">
          <th className="py-2 pr-3 font-normal">Time</th>
          <th className="py-2 pr-3 font-normal">Scene before → after</th>
          <th className="py-2 pr-2 font-normal">Speech</th>
          <th className="py-2 pr-2 font-normal">Silence b/a</th>
          <th className="py-2 pr-2 font-normal">Sentence</th>
          <th className="py-2 pr-2 font-normal">Shot cut</th>
          <th className="py-2 pr-2 font-normal">Convo cont.</th>
          <th className="py-2 pr-3 font-normal">WHERE</th>
          <th className="py-2 pr-3 font-normal">Status</th>
        </tr>
      </thead>
      <tbody>
        {candidates.map((c) => (
          <tr key={c.candidate_id} className="border-b border-line/60 hover:bg-surface2/60">
            <td className="py-2 pr-3">
              <button onClick={() => onSeek(c.timestamp)} className="font-mono text-accent hover:underline">
                {formatTime(c.timestamp)}
              </button>
            </td>
            <td className="py-2 pr-3 text-muted max-w-xs truncate">{c.scene_before} → {c.scene_after}</td>
            <td className="py-2 pr-2"><Check ok={c.features.in_speech} /></td>
            <td className="py-2 pr-2 font-mono text-muted">
              {c.features.silence_before.toFixed(1)}/{c.features.silence_after.toFixed(1)}
            </td>
            <td className="py-2 pr-2"><Check ok={c.features.sentence_complete} /></td>
            <td className="py-2 pr-2"><Check ok={c.features.shot_cut_aligned} /></td>
            <td className="py-2 pr-2"><Check ok={c.features.conversation_continues} /></td>
            <td className="py-2 pr-3 font-mono text-ink">{Math.round(c.where_score)}</td>
            <td className="py-2 pr-3">
              {c.status === 'accepted' ? (
                <span className="text-accepted">accepted</span>
              ) : (
                <span className="text-rejected" title={c.rejection_reason ?? undefined}>
                  rejected{c.rejection_code ? ` · ${c.rejection_code}` : ''}
                </span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
