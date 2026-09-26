'use client';
import React, { useRef } from 'react';
import { Scene, Candidate, FinalBreak } from '../lib/types';
import { formatTime } from '../lib/format';

interface TimelineProps {
  duration: number;
  currentTime: number;
  scenes: Scene[];
  candidates: Candidate[];
  finalBreaks: FinalBreak[];
  onSeek: (t: number) => void;
}

export const Timeline: React.FC<TimelineProps> = ({
  duration, currentTime, scenes, candidates, finalBreaks, onSeek,
}) => {
  const trackRef = useRef<HTMLDivElement>(null);
  const total = Math.max(duration, 1);
  const pct = (t: number) => Math.min(100, Math.max(0, (t / total) * 100));
  const finalTimes = new Set(finalBreaks.map((b) => Math.round(b.timestamp)));

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = trackRef.current?.getBoundingClientRect();
    if (!rect) return;
    const ratio = (e.clientX - rect.left) / rect.width;
    onSeek(Math.max(0, ratio * duration));
  };

  return (
    <div className="rounded-md border border-line bg-surface p-3">
      <div
        ref={trackRef}
        onClick={handleClick}
        className="relative h-10 rounded bg-surface2 cursor-pointer overflow-hidden"
      >
        {scenes.map((scene, i) => {
          const sensitive = scene.sensitive_contexts.length > 0;
          return (
            <div
              key={scene.scene_id}
              title={`${scene.dominant_activity} · ${formatTime(scene.start)}–${formatTime(scene.end)}`}
              className={`absolute inset-y-0 border-r border-line/60 ${
                sensitive ? 'hatch-rejected' : i % 2 === 0 ? 'bg-white/[0.03]' : 'bg-transparent'
              }`}
              style={{ left: `${pct(scene.start)}%`, width: `${pct(scene.end - scene.start) - pct(0)}%` }}
            />
          );
        })}

        {candidates.map((c) => {
          const isFinal = finalTimes.has(Math.round(c.timestamp));
          return (
            <div
              key={c.candidate_id}
              title={`${formatTime(c.timestamp)} · WHERE ${Math.round(c.where_score)} · ${c.status}`}
              className={`absolute top-1 bottom-1 w-0.5 rounded ${isFinal ? 'bg-accent' : 'bg-muted/50'}`}
              style={{ left: `${pct(c.timestamp)}%` }}
            />
          );
        })}

        <div
          className="absolute top-0 bottom-0 w-px bg-ink/80"
          style={{ left: `${pct(currentTime)}%` }}
        />
      </div>

      <div className="flex justify-between mt-1.5 text-[10px] font-mono text-muted">
        <span>00:00.0</span>
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration)}</span>
      </div>
    </div>
  );
};
