"""IAB VMAP 1.0 with inline VAST 3.0 linear ads. Built with ElementTree so output is always well-formed."""
import xml.etree.ElementTree as ET
from typing import List

from app.config import settings
from app.models.analysis import FinalBreak

VMAP_NS = "http://www.iab.net/videosuite/vmap"
ET.register_namespace("vmap", VMAP_NS)


def hms(seconds: float, millis: bool = True) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}" + (f".{ms:03d}" if millis else "")


def generate_vmap_xml(breaks: List[FinalBreak]) -> str:
    root = ET.Element(f"{{{VMAP_NS}}}VMAP", {"version": "1.0"})
    for b in breaks:
        ab = ET.SubElement(root, f"{{{VMAP_NS}}}AdBreak",
                           {"timeOffset": hms(b.timestamp), "breakType": "linear", "breakId": b.break_id})
        src = ET.SubElement(ab, f"{{{VMAP_NS}}}AdSource",
                            {"id": f"{b.break_id}_src", "allowMultipleAds": "false", "followRedirects": "true"})
        vast = ET.SubElement(ET.SubElement(src, f"{{{VMAP_NS}}}VASTAdData"), "VAST", {"version": "3.0"})
        inline = ET.SubElement(ET.SubElement(vast, "Ad", {"id": f"{b.break_id}_{b.brand.brand_id}"}), "InLine")
        ET.SubElement(inline, "AdSystem", {"version": "1.0"}).text = "SceneSense"
        ET.SubElement(inline, "AdTitle").text = f"{b.brand.brand_name} (synthetic)"
        ET.SubElement(inline, "Impression").text = f"{settings.public_base_url}/api/track/impression?break={b.break_id}"
        linear = ET.SubElement(ET.SubElement(ET.SubElement(inline, "Creatives"), "Creative",
                                             {"id": b.brand.brand_id, "sequence": "1"}), "Linear")
        ET.SubElement(linear, "Duration").text = hms(b.duration_seconds, millis=False)
        media = ET.SubElement(ET.SubElement(linear, "MediaFiles"), "MediaFile",
                              {"delivery": "progressive", "type": "video/mp4", "width": "1280", "height": "720"})
        url = b.brand.creative_url
        media.text = url if url.startswith("http") else settings.public_base_url + url
        ext = ET.SubElement(ET.SubElement(inline, "Extensions"), "Extension", {"type": "scenesense"})
        ET.SubElement(ext, "MatchScore").text = str(b.brand.match_score)
        ET.SubElement(ext, "WhereScore").text = str(b.where_score)
        ET.SubElement(ext, "SceneBefore").text = b.scene_before
    ET.indent(root)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")
