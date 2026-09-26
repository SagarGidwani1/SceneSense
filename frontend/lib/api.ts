import {
  HealthStatus,
  VideoSummary,
  UploadResult,
  AnalysisStatus,
  AnalysisResult,
  Brand,
  Rules,
} from './types';

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiError(`Backend not reachable at ${API_BASE}`);
  }
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new ApiError(`${res.status} ${res.statusText}${body ? `: ${body}` : ''}`);
  }
  return res.json() as Promise<T>;
}

function json(method: string, body: unknown): RequestInit {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
}

export const fetchHealth = () => request<HealthStatus>('/api/health');

export const fetchVideos = () => request<VideoSummary[]>('/api/videos');

export async function uploadVideo(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  return request<UploadResult>('/api/videos/upload', { method: 'POST', body: formData });
}

export const analyzeVideo = (videoId: string) =>
  request<{ video_id: string; status: string }>(`/api/videos/${videoId}/analyze`, { method: 'POST' });

export const fetchVideoStatus = (videoId: string) =>
  request<AnalysisStatus>(`/api/videos/${videoId}/status`);

export const fetchResult = (videoId: string) =>
  request<AnalysisResult>(`/api/videos/${videoId}/result`);

export const rematchVideo = (videoId: string) =>
  request<AnalysisResult>(`/api/videos/${videoId}/rematch`, { method: 'POST' });

export const vmapUrl = (videoId: string) => `${API_BASE}/api/videos/${videoId}/vmap`;
export const debugUrl = (videoId: string) => `${API_BASE}/api/videos/${videoId}/debug`;

export const fetchBrands = () => request<Brand[]>('/api/brands');

export const createBrand = (brand: Brand) => request<Brand>('/api/brands', json('POST', brand));

export const deleteBrand = (brandId: string) =>
  request<void>(`/api/brands/${brandId}`, { method: 'DELETE' });

export const fetchRules = () => request<Rules>('/api/rules');

export const updateRules = (rules: Rules) => request<Rules>('/api/rules', json('PUT', rules));
