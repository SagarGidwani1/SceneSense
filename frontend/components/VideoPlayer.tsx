'use client';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Play, Pause, SkipForward, Volume2, VolumeX } from 'lucide-react';
import { FinalBreak } from '../lib/types';
import { formatTime, apiAsset } from '../lib/format';
import { API_BASE } from '../lib/api';

interface VideoPlayerProps {
  videoUrl: string;
  finalBreaks: FinalBreak[];
  onTimeUpdate: (t: number) => void;
  seekTo: number | null;
}

const SEEK_TOLERANCE = 1.5;

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoUrl, finalBreaks, onTimeUpdate, seekTo }) => {
  const mainRef = useRef<HTMLVideoElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const playedRef = useRef<Set<string>>(new Set());

  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [activeBreak, setActiveBreak] = useState<FinalBreak | null>(null);
  const [adRemaining, setAdRemaining] = useState(0);
  const [, forceRender] = useState(0);

  const sortedBreaks = useMemo(
    () => [...finalBreaks].sort((a, b) => a.timestamp - b.timestamp),
    [finalBreaks]
  );

  useEffect(() => {
    if (seekTo != null && mainRef.current) mainRef.current.currentTime = seekTo;
  }, [seekTo]);

  useEffect(() => () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
  }, []);

  const clearAdTimer = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const resumeMain = (b: FinalBreak) => {
    clearAdTimer();
    setActiveBreak((cur) => (cur && cur.break_id === b.break_id ? null : cur));
    const video = mainRef.current; // main video stays mounted during the ad
    if (video) {
      video.currentTime = b.timestamp;
      video.play().catch(() => {});
    }
  };

  const triggerBreak = (b: FinalBreak) => {
    playedRef.current.add(b.break_id);
    forceRender((n) => n + 1);
    mainRef.current?.pause();
    setActiveBreak(b);
    setAdRemaining(Math.max(1, Math.round(b.duration_seconds)));
    clearAdTimer();
    // Safety net if the creative fails to load or never fires `ended`.
    const deadline = Date.now() + (b.duration_seconds + 3) * 1000;
    intervalRef.current = setInterval(() => {
      if (Date.now() >= deadline) resumeMain(b);
    }, 500);
  };

  const handleTimeUpdate = () => {
    const video = mainRef.current;
    if (!video || activeBreak) return;
    const t = video.currentTime;
    setCurrentTime(t);
    onTimeUpdate(t);

    for (const b of sortedBreaks) {
      if (playedRef.current.has(b.break_id)) continue;
      if (t < b.timestamp) continue;
      if (t - b.timestamp <= SEEK_TOLERANCE) {
        triggerBreak(b);
      } else {
        playedRef.current.add(b.break_id); // seeked past — mark skipped
      }
    }
  };

  const togglePlay = () => {
    const video = mainRef.current;
    if (!video || activeBreak) return;
    if (playing) video.pause(); else video.play().catch(() => {});
  };

  const toggleMute = () => {
    const video = mainRef.current;
    if (!video) return;
    video.muted = !video.muted;
    setMuted(video.muted);
  };

  const jumpToNextBreak = () => {
    const video = mainRef.current;
    if (!video) return;
    const next = sortedBreaks.find((b) => !playedRef.current.has(b.break_id) && b.timestamp > currentTime);
    if (next) video.currentTime = Math.max(0, next.timestamp - 5);
  };

  const seekFromBar = (e: React.MouseEvent<HTMLDivElement>) => {
    const video = mainRef.current;
    if (!video || duration <= 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    video.currentTime = ratio * duration;
  };

  return (
    <div className="rounded-md border border-line bg-black overflow-hidden relative">
      <div className="relative aspect-video max-h-[58vh] mx-auto bg-black">
        <video
          ref={mainRef}
          src={videoUrl}
          preload="auto"
          className={`absolute inset-0 w-full h-full object-contain ${activeBreak ? 'invisible' : ''}`}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={() => setDuration(mainRef.current?.duration || 0)}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
        />
        {activeBreak && (
          <>
            <video
              key={activeBreak.break_id}
              src={apiAsset(API_BASE, activeBreak.brand.creative_url)}
              autoPlay
              muted={muted}
              className="absolute inset-0 w-full h-full object-contain"
              onTimeUpdate={(e) =>
                setAdRemaining(Math.max(0, Math.ceil(activeBreak.duration_seconds - e.currentTarget.currentTime)))
              }
              onEnded={() => resumeMain(activeBreak)}
            />
            <div className="absolute top-3 left-3 flex items-center gap-2 rounded bg-black/70 px-2.5 py-1 text-[11px] font-mono text-warn">
              Ad · {activeBreak.brand.brand_name} · 0:{adRemaining.toString().padStart(2, '0')}
            </div>
            <button
              onClick={() => resumeMain(activeBreak)}
              className="absolute bottom-3 right-3 rounded bg-surface/90 border border-line px-3 py-1.5 text-xs text-ink hover:border-accent"
            >
              Skip ad
            </button>
          </>
        )}
      </div>

      <div className="flex items-center gap-3 px-3 py-2 bg-surface border-t border-line">
        <button onClick={togglePlay} disabled={!!activeBreak} className="text-ink disabled:opacity-40">
          {playing ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <button onClick={toggleMute} className="text-muted hover:text-ink">
          {muted ? <VolumeX size={14} /> : <Volume2 size={14} />}
        </button>

        <div
          onClick={seekFromBar}
          className="relative flex-1 h-1.5 rounded-full bg-surface2 cursor-pointer"
        >
          <div
            className="h-full rounded-full bg-accent"
            style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
          />
          {sortedBreaks.map((b) => (
            <div
              key={b.break_id}
              className="absolute top-1/2 -translate-y-1/2 w-0.5 h-3 bg-accepted"
              style={{ left: `${duration > 0 ? (b.timestamp / duration) * 100 : 0}%` }}
              title={`${formatTime(b.timestamp)} · ${b.brand.brand_name}`}
            />
          ))}
        </div>

        <span className="text-[11px] font-mono text-muted shrink-0">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>

        <button
          onClick={jumpToNextBreak}
          className="flex items-center gap-1 text-[11px] text-muted hover:text-ink shrink-0"
          title="Jump to 5s before next break"
        >
          <SkipForward size={13} />
          Next break
        </button>
      </div>
    </div>
  );
};
