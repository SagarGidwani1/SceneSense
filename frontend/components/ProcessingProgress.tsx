'use client';
import React from 'react';
import { CheckCircle2, Loader2, AlertCircle, Circle } from 'lucide-react';
import { AnalysisStatus, Providers } from '../lib/types';

interface ProcessingProgressProps {
  status: AnalysisStatus;
  providers?: Providers | null;
}

const STEPS: Array<{ key: string; label: string }> = [
  { key: 'EXTRACTING', label: 'Extracting audio' },
  { key: 'TRANSCRIBING', label: 'Transcribing' },
  { key: 'SEGMENTING', label: 'Segmenting scenes' },
  { key: 'UNDERSTANDING', label: 'Understanding scenes' },
  { key: 'GENERATING_CANDIDATES', label: 'Generating candidates' },
  { key: 'SCORING_WHERE', label: 'Scoring WHERE' },
  { key: 'MATCHING_BRANDS', label: 'Matching brands' },
  { key: 'APPLYING_PACING', label: 'Applying pacing' },
  { key: 'GENERATING_VMAP', label: 'Generating VMAP' },
];

function isFallback(value: string): boolean {
  return /heuristic|fallback/i.test(value);
}

export const ProcessingProgress: React.FC<ProcessingProgressProps> = ({ status, providers }) => {
  const stepIdx = STEPS.findIndex((s) => s.key === status.status);
  const failed = status.status === 'FAILED';

  return (
    <div className="rounded-md border border-line bg-surface p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-medium text-ink">{status.current_step}</h2>
        <span className="text-xs font-mono text-muted">{Math.round(status.progress_percent)}%</span>
      </div>

      <div className="h-1 rounded-full bg-surface2 overflow-hidden mb-5">
        <div
          className={`h-full transition-all ${failed ? 'bg-rejected' : 'bg-accent'}`}
          style={{ width: `${status.progress_percent}%` }}
        />
      </div>

      {failed ? (
        <div className="flex items-start gap-2 rounded border border-rejected/40 bg-rejected/10 p-3">
          <AlertCircle size={14} className="text-rejected shrink-0 mt-0.5" />
          <p className="text-xs text-rejected">{status.error || 'Analysis failed.'}</p>
        </div>
      ) : (
        <ol className="flex flex-col gap-2">
          {STEPS.map((step, i) => {
            const done = stepIdx > i;
            const current = stepIdx === i;
            return (
              <li key={step.key} className="flex items-center gap-2">
                {done ? (
                  <CheckCircle2 size={14} className="text-accepted shrink-0" />
                ) : current ? (
                  <Loader2 size={14} className="text-accent shrink-0 animate-spin-slow" />
                ) : (
                  <Circle size={14} className="text-line shrink-0" />
                )}
                <span className={`text-xs ${current ? 'text-ink font-medium' : done ? 'text-muted' : 'text-muted/60'}`}>
                  {step.label}
                </span>
              </li>
            );
          })}
        </ol>
      )}

      {providers && (
        <div className="mt-5 pt-4 border-t border-line flex flex-col gap-1.5">
          <span className="text-[10px] uppercase tracking-wide text-muted">Providers</span>
          {(['asr', 'scene_ai', 'brand_ai'] as const).map((key) => (
            <div key={key} className={`text-[11px] font-mono ${isFallback(providers[key]) ? 'text-warn' : 'text-muted'}`}>
              {key}: {providers[key]}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
