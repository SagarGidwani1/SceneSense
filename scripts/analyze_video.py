"""CLI: python scripts/analyze_video.py path/to/episode.mp4  -> prints breaks, writes VMAP + debug JSON."""
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.config import STORAGE_PATH  # noqa: E402
from app.services import scheduler, video_service  # noqa: E402

src = Path(sys.argv[1]).resolve()
vid = uuid.uuid4().hex[:8]
dest = STORAGE_PATH / "uploads" / f"{vid}_{src.name}"
shutil.copy(src, dest)
video_service.register_video(vid, src.name, str(dest))
scheduler.run_pipeline(vid)
st = scheduler.get_status(vid)
if st.status != "READY":
    sys.exit(f"FAILED: {st.error}")
res = scheduler.get_result(vid)
print(f"{vid}: {len(res.scenes)} scenes, providers={res.providers}")
for b in res.final_breaks:
    print(f"  {b.timestamp:8.2f}s  {b.brand.brand_name:<12} match={b.brand.match_score}  where={b.where_score}")
Path(f"{vid}_vmap.xml").write_text(res.vmap_xml, encoding="utf-8")
Path(f"{vid}_debug.json").write_text(res.model_dump_json(indent=2), encoding="utf-8")
print(f"wrote {vid}_vmap.xml and {vid}_debug.json")
