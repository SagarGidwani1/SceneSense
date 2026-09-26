'use client';
import React from 'react';
import { HealthStatus } from '../lib/types';

interface HealthPillsProps {
  health: HealthStatus | null;
}

const PROVIDERS: Array<{ key: keyof HealthStatus; label: string }> = [
  { key: 'groq', label: 'Groq ASR' },
  { key: 'gemini', label: 'Gemini vision' },
  { key: 'ffmpeg', label: 'FFmpeg' },
];

export const HealthPills: React.FC<HealthPillsProps> = ({ health }) => (
  <div className="flex items-center gap-3">
    {PROVIDERS.map(({ key, label }) => {
      const ok = !!health?.[key];
      return (
        <div
          key={key}
          className="flex items-center gap-1.5"
          title={ok ? undefined : 'add key in .env'}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-accepted' : 'bg-muted/40'}`} />
          <span className="text-[11px] text-muted">{label}</span>
        </div>
      );
    })}
  </div>
);
