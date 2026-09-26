'use client';
import React from 'react';
import { VideoSummary } from '../lib/types';

interface VideoListProps {
  videos: VideoSummary[];
  activeId: string | null;
  onSelect: (video: VideoSummary) => void;
}

const STATUS_COLOR: Record<string, string> = {
  READY: 'bg-accepted',
  FAILED: 'bg-rejected',
};

export const VideoList: React.FC<VideoListProps> = ({ videos, activeId, onSelect }) => {
  if (videos.length === 0) {
    return <p className="text-[11px] text-muted px-1">No videos analysed yet.</p>;
  }
  return (
    <ul className="flex flex-col gap-1">
      {videos.map((v) => {
        const dotColor = STATUS_COLOR[v.status] ?? 'bg-warn';
        return (
          <li key={v.video_id}>
            <button
              onClick={() => onSelect(v)}
              className={`w-full text-left px-2 py-2 rounded transition-colors ${
                activeId === v.video_id ? 'bg-surface2 border border-line' : 'hover:bg-surface2 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} />
                <span className="text-xs text-ink truncate">{v.filename}</span>
              </div>
              <div className="text-[10px] text-muted font-mono mt-0.5 pl-3.5">{v.status}</div>
            </button>
          </li>
        );
      })}
    </ul>
  );
};
