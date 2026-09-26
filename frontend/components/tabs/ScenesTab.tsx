'use client';
import React, { useState } from 'react';
import { ChevronDown, ChevronRight, ImageOff } from 'lucide-react';
import { Scene } from '../../lib/types';
import { formatTime, apiAsset } from '../../lib/format';
import { API_BASE } from '../../lib/api';

interface ScenesTabProps {
  scenes: Scene[];
  onSeek: (t: number) => void;
}

const Bar: React.FC<{ label: string; value: number; color: string }> = ({ label, value, color }) => (
  <div className="flex items-center gap-2">
    <span className="text-[10px] text-muted w-20 shrink-0">{label}</span>
    <div className="flex-1 h-1.5 rounded-full bg-surface2 overflow-hidden">
      <div className={color} style={{ width: `${Math.round(value * 100)}%`, height: '100%' }} />
    </div>
    <span className="text-[10px] font-mono text-muted w-8 text-right">{Math.round(value * 100)}</span>
  </div>
);

export const ScenesTab: React.FC<ScenesTabProps> = ({ scenes, onSeek }) => {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-3">
      {scenes.map((scene) => {
        const thumb = apiAsset(API_BASE, scene.thumbnail_url);
        const isOpen = openId === scene.scene_id;
        return (
          <div key={scene.scene_id} className="rounded-md border border-line bg-surface p-3 flex gap-3">
            <div className="w-28 h-16 rounded bg-surface2 shrink-0 overflow-hidden flex items-center justify-center">
              {thumb ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={thumb} alt="" className="w-full h-full object-cover" />
              ) : (
                <ImageOff size={16} className="text-muted" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <button onClick={() => onSeek(scene.start)} className="font-mono text-xs text-accent hover:underline">
                  {formatTime(scene.start)} – {formatTime(scene.end)}
                </button>
                <span className="text-[11px] text-muted shrink-0">{scene.dominant_activity} · {scene.emotion}</span>
              </div>

              <p className="text-xs text-ink mt-1">{scene.summary}</p>

              {scene.context_tags.length > 0 && (
                <ul className="flex flex-wrap gap-1 mt-1.5">
                  {scene.context_tags.map((t, i) => (
                    <li key={i} className="text-[10px] rounded bg-surface2 border border-line px-1.5 py-0.5 text-muted">{t}</li>
                  ))}
                </ul>
              )}

              {scene.sensitive_contexts.length > 0 && (
                <p className="text-[11px] text-rejected mt-1.5">
                  Sensitive: {scene.sensitive_contexts.join(', ')}
                </p>
              )}

              <div className="grid grid-cols-2 gap-2 mt-2 max-w-sm">
                <Bar label="Tension" value={scene.tension_score} color="bg-warn" />
                <Bar label="Cliffhanger" value={scene.cliffhanger_score} color="bg-accent" />
              </div>

              {scene.transcript && (
                <div className="mt-2">
                  <button
                    onClick={() => setOpenId(isOpen ? null : scene.scene_id)}
                    className="flex items-center gap-1 text-[11px] text-muted hover:text-ink"
                  >
                    {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    Transcript
                  </button>
                  {isOpen && (
                    <p className="text-[11px] text-muted mt-1 whitespace-pre-wrap font-mono leading-relaxed">
                      {scene.transcript}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
