"""
audit.py — Verifikasi kelengkapan dan keunikan data scraping
"""
import csv
import re
import sys
import yt_dlp
from collections import Counter

CSV_FILE    = "grouped_output_terasdakwah.csv"
CHANNEL_URL = "https://www.youtube.com/@terasdakwah"

def extract_vid_id(url: str) -> str | None:
    m = re.search(r"v=([\w\-]+)", url)
    return m.group(1) if m else None

# ── 1. Baca semua URL dari CSV ─────────────────────────────────
print("=" * 60)
print("  AUDIT: Duplikat & Kelengkapan Scraping")
print("=" * 60)

print(f"\n[1/3] Membaca {CSV_FILE}...")
all_urls  = []
all_ids   = []
playlists = {}  # playlist → set of vid_ids

with open(CSV_FILE, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        url      = (row.get("youtube_url") or "").strip()
        playlist = (row.get("playlist") or "").strip()
        if not url or not url.startswith("http"):
            continue
        vid_id = extract_vid_id(url)
        if vid_id:
            all_urls.append(url)
            all_ids.append(vid_id)
            playlists.setdefault(playlist, set()).add(vid_id)

# Deteksi duplikat
id_counter     = Counter(all_ids)
duplicate_ids  = {vid: count for vid, count in id_counter.items() if count > 1}

print(f"  Total baris URL di CSV  : {len(all_urls)}")
print(f"  Total video ID unik     : {len(set(all_ids))}")
print(f"  Video ID duplikat       : {len(duplicate_ids)}")

if duplicate_ids:
    print("\n  ⚠  Duplikat ditemukan:")
    for vid_id, count in list(duplicate_ids.items())[:20]:
        print(f"     https://youtube.com/watch?v={vid_id}  → muncul {count}x")
    if len(duplicate_ids) > 20:
        print(f"     ... dan {len(duplicate_ids)-20} lainnya")
else:
    print("  ✓  Tidak ada duplikat URL!")

# ── 2. Scrape ulang channel untuk cek total video ────────────
print(f"\n[2/3] Scraping total video dari channel...")
YDL_FLAT = {"extract_flat": "in_playlist", "quiet": True,
            "no_warnings": True, "ignoreerrors": True}

channel_ids = set()
with yt_dlp.YoutubeDL(YDL_FLAT) as ydl:
    info = ydl.extract_info(CHANNEL_URL + "/videos", download=False)
if info:
    for entry in (info.get("entries") or []):
        if entry and entry.get("id"):
            channel_ids.add(entry["id"])

print(f"  Total video di channel  : {len(channel_ids)}")

# ── 3. Bandingkan ─────────────────────────────────────────────
csv_ids    = set(all_ids)
missing    = channel_ids - csv_ids
extra      = csv_ids - channel_ids

print(f"\n[3/3] Perbandingan CSV vs Channel:")
print(f"  Video di CSV            : {len(csv_ids)}")
print(f"  Video di channel        : {len(channel_ids)}")
print(f"  Video BELUM terscrape   : {len(missing)}")
print(f"  Video di CSV tapi tdk di channel (private/dihapus): {len(extra)}")

# ── Ringkasan ──────────────────────────────────────────────────
print("\n" + "=" * 60)
if not duplicate_ids and not missing:
    print("  ✓  SEMPURNA! Semua video terscrape, tidak ada duplikat.")
elif not duplicate_ids and missing:
    print(f"  ⚠  Tidak ada duplikat, tapi {len(missing)} video BELUM terscrape.")
elif duplicate_ids and not missing:
    print(f"  ⚠  Semua video terscrape, tapi ada {len(duplicate_ids)} duplikat.")
else:
    print(f"  ✗  Ada {len(duplicate_ids)} duplikat dan {len(missing)} video belum terscrape.")
print("=" * 60)

if missing:
    print("\n  Video yang belum terscrape:")
    for vid_id in list(missing)[:10]:
        print(f"    https://www.youtube.com/watch?v={vid_id}")
    if len(missing) > 10:
        print(f"    ... dan {len(missing)-10} lainnya")
