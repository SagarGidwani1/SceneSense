'use client';
import React, { useEffect, useState } from 'react';
import { Rules, AnalysisResult } from '../../lib/types';
import { fetchRules, updateRules, rematchVideo, ApiError } from '../../lib/api';

interface RulesTabProps {
  videoId: string | null;
  currentRules: Rules | null;
  onRematched: (result: AnalysisResult) => void;
}

const FIELDS: Array<{ key: keyof Rules; label: string; step?: number }> = [
  { key: 'max_breaks_per_hour', label: 'Max breaks per hour' },
  { key: 'min_gap_seconds', label: 'Min gap (seconds)' },
  { key: 'max_ad_load_percent', label: 'Max ad load (%)', step: 0.1 },
  { key: 'ad_duration_seconds', label: 'Ad duration (seconds)' },
  { key: 'edge_buffer_seconds', label: 'Edge buffer (seconds)' },
  { key: 'min_where_score', label: 'Min WHERE score' },
];

export const RulesTab: React.FC<RulesTabProps> = ({ videoId, currentRules, onRematched }) => {
  const [rules, setRules] = useState<Rules | null>(currentRules);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (currentRules) { setRules(currentRules); return; }
    fetchRules().then(setRules).catch((e) => setError(e instanceof ApiError ? e.message : 'Failed to load rules'));
  }, [currentRules]);

  if (!rules) return <p className="text-xs text-muted">Loading rules…</p>;

  const handleSave = async () => {
    setBusy(true);
    setError('');
    try {
      const saved = await updateRules(rules);
      setRules(saved);
      if (videoId) onRematched(await rematchVideo(videoId));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to save rules');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-md flex flex-col gap-3">
      {FIELDS.map(({ key, label, step }) => (
        <label key={key} className="flex items-center justify-between gap-3">
          <span className="text-xs text-muted">{label}</span>
          <input
            type="number"
            step={step ?? 1}
            value={rules[key]}
            onChange={(e) => setRules({ ...rules, [key]: Number(e.target.value) })}
            className="w-28 bg-surface2 border border-line rounded px-2 py-1 text-xs text-ink font-mono focus:outline-none focus:border-accent"
          />
        </label>
      ))}
      <button
        onClick={handleSave}
        disabled={busy}
        className="self-start rounded bg-accent text-base font-medium text-sm px-4 py-1.5 mt-1 disabled:opacity-50"
      >
        Save & rematch
      </button>
      {error && <p className="text-[11px] text-rejected">{error}</p>}
    </div>
  );
};
