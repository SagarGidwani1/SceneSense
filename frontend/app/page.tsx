'use client';
import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { UploadPanel } from '../components/UploadPanel';
import { VideoList } from '../components/VideoList';
import { HealthPills } from '../components/HealthPills';
import { ProcessingProgress } from '../components/ProcessingProgress';
import { VideoPlayer } from '../components/VideoPlayer';
import { Timeline } from '../components/Timeline';
import { BreaksTab } from '../components/tabs/BreaksTab';
import { ScenesTab } from '../components/tabs/ScenesTab';
import { CandidatesTab } from '../components/tabs/CandidatesTab';
import { BrandsTab } from '../components/tabs/BrandsTab';
import { RulesTab } from '../components/tabs/RulesTab';
import { OutputsTab } from '../components/tabs/OutputsTab';
import {
  fetchHealth, fetchVideos, fetchVideoStatus, fetchResult, ApiError, API_BASE,
} from '../lib/api';
import { HealthStatus, VideoSummary, AnalysisStatus, AnalysisResult, UploadResult } from '../lib/types';

type TabId = 'breaks' | 'scenes' | 'candidates' | 'brands' | 'rules' | 'outputs';
const TABS: Array<{ id: TabId; label: string }> = [
  { id: 'breaks', label: 'Breaks' },
  { id: 'scenes', label: 'Scenes' },
  { id: 'candidates', label: 'Candidates' },
  { id: 'brands', label: 'Brands' },
  { id: 'rules', label: 'Rules' },
  { id: 'outputs', label: 'Outputs' },
];

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [videos, setVideos] = useState<VideoSummary[]>([]);
  const [activeVideoId, setActiveVideoId] = useState<string | null>(null);
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<TabId>('breaks');
  const [currentTime, setCurrentTime] = useState(0);
  const [seekTo, setSeekTo] = useState<number | null>(null);

  const reloadVideos = useCallback(() => {
    fetchVideos().then(setVideos).catch((e) => setError(e instanceof ApiError ? e.message : 'Backend unreachable'));
  }, []);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth(null));
    reloadVideos();
  }, [reloadVideos]);

  const selectVideo = (id: string) => {
    setActiveVideoId(id);
    setStatus(null);
    setResult(null);
    setError('');
    setTab('breaks');
  };

  const handleUploaded = (v: UploadResult) => {
    reloadVideos();
    selectVideo(v.video_id);
  };

  // Poll status until READY/FAILED, then load the full result.
  useEffect(() => {
    if (!activeVideoId || result) return;
    let cancelled = false;
    let interval: ReturnType<typeof setInterval> | null = null;

    const tick = async () => {
      try {
        const st = await fetchVideoStatus(activeVideoId);
        if (cancelled) return;
        setStatus(st);
        if (st.status === 'READY') {
          if (interval) clearInterval(interval);
          const res = await fetchResult(activeVideoId);
          if (!cancelled) { setResult(res); reloadVideos(); }
        } else if (st.status === 'FAILED') {
          if (interval) clearInterval(interval);
          reloadVideos();
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? e.message : 'Backend unreachable');
      }
    };

    tick();
    interval = setInterval(tick, 1500);
    return () => { cancelled = true; if (interval) clearInterval(interval); };
  }, [activeVideoId, result, reloadVideos]);

  const videoDuration = result ? result.duration_seconds : 0;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="h-12 border-b border-line flex items-center justify-between px-4 shrink-0">
        <span className="text-sm font-semibold tracking-tight text-ink">SceneSense</span>
        <HealthPills health={health} />
      </header>

      <div className="flex flex-1 min-h-0">
        <aside className="w-64 border-r border-line p-4 flex flex-col gap-4 shrink-0 overflow-y-auto">
          <UploadPanel onUploaded={handleUploaded} />
          <div>
            <span className="text-[10px] uppercase tracking-wide text-muted">Videos</span>
            <div className="mt-2">
              <VideoList videos={videos} activeId={activeVideoId} onSelect={(v) => selectVideo(v.video_id)} />
            </div>
          </div>
        </aside>

        <main className="flex-1 p-5 overflow-y-auto">
          {error && (
            <div className="flex items-center gap-2 rounded border border-rejected/40 bg-rejected/10 px-3 py-2 mb-4 text-xs text-rejected">
              <AlertTriangle size={14} />
              {error} at {API_BASE}
            </div>
          )}

          {!activeVideoId && (
            <p className="text-sm text-muted">Upload a video or select one from the left to begin.</p>
          )}

          {activeVideoId && !result && status && (
            <ProcessingProgress status={status} />
          )}

          {result && (
            <div className="flex flex-col gap-4">
              <VideoPlayer
                videoUrl={`${API_BASE}${result.video_url}`}
                finalBreaks={result.final_breaks}
                onTimeUpdate={setCurrentTime}
                seekTo={seekTo}
              />
              <Timeline
                duration={videoDuration}
                currentTime={currentTime}
                scenes={result.scenes}
                candidates={result.candidates}
                finalBreaks={result.final_breaks}
                onSeek={setSeekTo}
              />

              {result.warnings.length > 0 && (
                <div className="rounded border border-warn/40 bg-warn/10 px-3 py-2 text-xs text-warn">
                  {result.warnings.join(' · ')}
                </div>
              )}

              <div className="rounded-md border border-line bg-surface">
                <div className="flex items-center gap-1 px-3 pt-2 border-b border-line overflow-x-auto">
                  {TABS.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setTab(t.id)}
                      className={`px-3 py-1.5 text-xs rounded-t whitespace-nowrap ${
                        tab === t.id ? 'text-ink border-b-2 border-accent' : 'text-muted hover:text-ink'
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
                <div className="p-4">
                  {tab === 'breaks' && <BreaksTab finalBreaks={result.final_breaks} candidates={result.candidates} onSeek={setSeekTo} />}
                  {tab === 'scenes' && <ScenesTab scenes={result.scenes} onSeek={setSeekTo} />}
                  {tab === 'candidates' && <CandidatesTab candidates={result.candidates} onSeek={setSeekTo} />}
                  {tab === 'brands' && <BrandsTab videoId={activeVideoId} onRematched={setResult} />}
                  {tab === 'rules' && <RulesTab videoId={activeVideoId} currentRules={result.rules} onRematched={setResult} />}
                  {tab === 'outputs' && <OutputsTab videoId={result.video_id} vmapXml={result.vmap_xml} auditLogs={result.audit_logs} />}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
