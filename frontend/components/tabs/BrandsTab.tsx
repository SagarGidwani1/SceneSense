'use client';
import React, { useEffect, useState } from 'react';
import { Trash2, Plus } from 'lucide-react';
import { Brand } from '../../lib/types';
import { fetchBrands, createBrand, deleteBrand, rematchVideo, ApiError } from '../../lib/api';

interface BrandsTabProps {
  videoId: string | null;
  onRematched: (result: Awaited<ReturnType<typeof rematchVideo>>) => void;
}

const EMPTY = { brand_id: '', brand_name: '', category: '', description: '', positive_contexts: '', negative_contexts: '' };

function splitCsv(value: string): string[] {
  return value.split(',').map((s) => s.trim()).filter(Boolean);
}

export const BrandsTab: React.FC<BrandsTabProps> = ({ videoId, onRematched }) => {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const reload = () => fetchBrands().then(setBrands).catch((e) => setError(e instanceof ApiError ? e.message : 'Failed to load brands'));

  useEffect(() => { reload(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const brand: Brand = {
        brand_id: form.brand_id,
        brand_name: form.brand_name,
        category: form.category,
        description: form.description,
        positive_contexts: splitCsv(form.positive_contexts),
        negative_contexts: splitCsv(form.negative_contexts),
        keywords: [],
      };
      await createBrand(brand);
      setForm(EMPTY);
      await reload();
      if (videoId) onRematched(await rematchVideo(videoId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to add brand');
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (brandId: string) => {
    setBusy(true);
    try {
      await deleteBrand(brandId);
      await reload();
      if (videoId) onRematched(await rematchVideo(videoId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to delete brand');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div>
        <p className="text-[11px] text-muted mb-2">Catalog — no code changes, this is data.</p>
        <ul className="flex flex-col gap-2">
          {brands.map((b) => (
            <li key={b.brand_id} className="rounded-md border border-line bg-surface p-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-sm text-ink font-medium">{b.brand_name}</div>
                  <div className="text-[11px] text-muted">{b.category}</div>
                </div>
                <button onClick={() => handleDelete(b.brand_id)} disabled={busy} className="text-muted hover:text-rejected">
                  <Trash2 size={14} />
                </button>
              </div>
              <p className="text-xs text-ink mt-1.5">{b.description}</p>
              {b.negative_contexts.length > 0 && (
                <p className="text-[11px] text-rejected mt-1.5">Blocks: {b.negative_contexts.join(', ')}</p>
              )}
            </li>
          ))}
          {brands.length === 0 && <p className="text-xs text-muted">No brands yet.</p>}
        </ul>
      </div>

      <form onSubmit={handleSubmit} className="rounded-md border border-line bg-surface p-4 flex flex-col gap-2.5 h-fit">
        <h3 className="text-xs font-medium text-ink mb-1">Add brand</h3>
        {(['brand_id', 'brand_name', 'category', 'description'] as const).map((field) => (
          <input
            key={field}
            required
            placeholder={field.replace('_', ' ')}
            value={form[field]}
            onChange={(e) => setForm({ ...form, [field]: e.target.value })}
            className="bg-surface2 border border-line rounded px-2.5 py-1.5 text-xs text-ink placeholder:text-muted focus:outline-none focus:border-accent"
          />
        ))}
        <input
          placeholder="positive contexts (comma-separated)"
          value={form.positive_contexts}
          onChange={(e) => setForm({ ...form, positive_contexts: e.target.value })}
          className="bg-surface2 border border-line rounded px-2.5 py-1.5 text-xs text-ink placeholder:text-muted focus:outline-none focus:border-accent"
        />
        <input
          placeholder="negative contexts (comma-separated)"
          value={form.negative_contexts}
          onChange={(e) => setForm({ ...form, negative_contexts: e.target.value })}
          className="bg-surface2 border border-line rounded px-2.5 py-1.5 text-xs text-ink placeholder:text-muted focus:outline-none focus:border-accent"
        />
        <button
          type="submit"
          disabled={busy}
          className="flex items-center justify-center gap-1.5 rounded bg-accent text-base font-medium text-sm py-1.5 mt-1 disabled:opacity-50"
        >
          <Plus size={14} /> Add & rematch
        </button>
        {error && <p className="text-[11px] text-rejected">{error}</p>}
      </form>
    </div>
  );
};
