"""
find_orphans.py
Cari video di channel yang TIDAK masuk playlist manapun,
kelompokkan berdasarkan judul, lalu append ke CSV yang ada.
"""

import argparse
import csv
import os
import re
import sys
import yt_dlp
from collections import OrderedDict

# ─────────────────────────────────────────────────────────────
# NICHE INFERENCE — dari judul video, singkat & padat
# ─────────────────────────────────────────────────────────────
NICHE_RULES: list[tuple[str, list[str]]] = [
    ("On The Way Talk",        ["otw", "on the way", "on the way talk"]),
    ("Q & A",                  ["q & a", "q&a", "qna", "tanya jawab", "ask", "ama"]),
    ("Kajian Islam",           ["kajian", "ngaji", "ceramah", "khutbah", "pengajian",
                                "tafsir", "hadits", "siroh", "sekolah", "bersanad"]),
    ("Dakwah & Motivasi",      ["dakwah", "motivasi", "hijrah", "semangat", "inspirasi",
                                "tausiyah", "nasihat", "reminder", "hidayah"]),
    ("Podcast & Talkshow",     ["podcast", "talkshow", "bincang", "obrolan",
                                "diskusi", "ruang tamu", "storynite", "ruang cerita"]),
    ("Kajian 1 Menit",         ["1 menit", "one minute", "short kajian"]),
    ("Ramadhan",               ["ramadhan", "ramadan", "puasa", "iftar", "sahur",
                                "tarawih", "lailatul"]),
    ("Web Series & Film",      ["series", "web series", "film", "short movie",
                                "episode", "vlog", "part "]),
    ("Keluarga & Pernikahan",  ["nikah", "pernikahan", "keluarga", "pranikah",
                                "parenting", "suami", "istri", "jomblo"]),
    ("Sosial & Kemanusiaan",   ["bergerak", "sedekah", "bantuan", "donasi", "qurban",
                                "lombok", "palu", "gempa", "bencana"]),
    ("Tokoh Ustadz",           ["ustadz", "ustadzah", "habib", "gus ", "syekh",
                                "ust.", " dr.", "kang "]),
    ("Video Kreatif & Poster", ["poster", "video kreatif", "video clip", "clip religi",
                                "murrotal", "sholawat"]),
    ("Bisnis & Wirausaha",     ["bisnis", "usaha", "wirausaha", "entrepreneur",
                                "modal", "riba", "ekonomi"]),
    ("Kesehatan",              ["kesehatan", "sehat", "halal", "makanan", "tips sehat"]),
]


def infer_niche(title: str) -> str:
    t = title.lower()
    for niche, keywords in NICHE_RULES:
        if any(kw in t for kw in keywords):
            return niche
    # Fallback: ambil 3 kata pertama dari judul sebagai label
    words = title.strip().split()
    short = " ".join(words[:3]) if len(words) >= 3 else title.strip()
    return short or "Lain-lain"


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

YDL_FLAT = {
    "extract_flat": "in_playlist",
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": True,
}


def get_all_channel_videos(channel_url: str) -> list[dict]:
    """Scrape semua video dari tab /videos channel."""
    videos_url = channel_url.rstrip("/") + "/videos"
    print(f"  Scraping: {videos_url}")
    with yt_dlp.YoutubeDL(YDL_FLAT) as ydl:
        info = ydl.extract_info(videos_url, download=False)
    if not info:
        return []
    videos = []
    for entry in (info.get("entries") or []):
        if entry and entry.get("id"):
            videos.append({
                "id":    entry["id"],
                "title": entry.get("title") or "",
            })
    return videos


def get_playlist_video_ids(csv_folder: str) -> set[str]:
    """Kumpulkan semua video_id yang sudah ada di playlist CSV."""
    ids = set()
    for fname in os.listdir(csv_folder):
        if not fname.endswith(".csv"):
            continue
        fpath = os.path.join(csv_folder, fname)
        with open(fpath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("youtube_url", "")
                # Ekstrak video ID dari URL
                m = re.search(r"v=([\w\-]+)", url)
                if m:
                    ids.add(m.group(1))
    return ids


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Cari video channel yang belum masuk playlist, append ke CSV"
    )
    parser.add_argument(
        "channel_url",
        type=str,
        help="URL channel YouTube, contoh: https://www.youtube.com/@terasdakwah",
    )
    parser.add_argument(
        "--folder",
        type=str,
        default="output_terasdakwah",
        help="Folder CSV playlist yang sudah ada (default: output_terasdakwah)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="grouped_output_terasdakwah.csv",
        help="File CSV output gabungan (default: grouped_output_terasdakwah.csv)",
    )
    args = parser.parse_args()

    print("=" * 64)
    print("  Find Orphan Videos — Channel vs Playlist")
    print("=" * 64)
    print(f"  Channel : {args.channel_url}")
    print(f"  Folder  : {args.folder}")
    print(f"  Output  : {args.output}")
    print("-" * 64)

    # ── 1. Ambil semua video dari channel ───────────────────
    print("\n[1/3] Scraping semua video dari channel...")
    all_videos = get_all_channel_videos(args.channel_url)
    print(f"  → Ditemukan {len(all_videos)} video di channel\n")

    if not all_videos:
        print("[!] Tidak ada video ditemukan.")
        sys.exit(1)

    # ── 2. Cari video yang belum masuk playlist ──────────────
    print("[2/3] Membandingkan dengan video yang sudah di playlist...")
    playlist_ids = get_playlist_video_ids(args.folder)
    print(f"  → Video di playlist : {len(playlist_ids)}")

    orphans = [v for v in all_videos if v["id"] not in playlist_ids]
    print(f"  → Video ORPHAN (belum di playlist) : {len(orphans)}\n")

    if not orphans:
        print("[✓] Semua video sudah masuk playlist. Tidak ada yang perlu ditambahkan.")
        sys.exit(0)

    # ── 3. Klasifikasi & grouping orphan ────────────────────
    print("[3/3] Mengklasifikasikan video orphan berdasarkan judul...\n")

    niche_groups: OrderedDict[str, list[str]] = OrderedDict()

    for v in orphans:
        title = v["title"]
        url   = f"https://www.youtube.com/watch?v={v['id']}"
        niche = infer_niche(title)

        title_disp = title[:55] + "…" if len(title) > 55 else title
        print(f"  [{niche:<25}] {title_disp}")

        if niche not in niche_groups:
            niche_groups[niche] = []
        if url not in niche_groups[niche]:
            niche_groups[niche].append(url)

    total_orphans = sum(len(v) for v in niche_groups.values())

    # ── 4. Append ke CSV gabungan ────────────────────────────
    print(f"\n  → {total_orphans} video orphan dikelompokkan ke {len(niche_groups)} niche baru")
    print(f"\n  Menambahkan ke: {args.output}")

    # Cek apakah file sudah ada (untuk tambah baris kosong pemisah)
    file_exists = os.path.isfile(args.output)

    with open(args.output, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        # Jika file sudah ada, tambah 1 baris kosong pemisah
        if file_exists:
            writer.writerow(["", ""])

        for i, (niche, urls) in enumerate(niche_groups.items()):
            for url in urls:
                writer.writerow([niche, url])
            # Baris kosong antar grup
            if i < len(niche_groups) - 1:
                writer.writerow(["", ""])

    # ── Ringkasan ────────────────────────────────────────────
    print("=" * 64)
    print("  RINGKASAN")
    print("=" * 64)
    print(f"  Total video channel    : {len(all_videos)}")
    print(f"  Sudah di playlist      : {len(playlist_ids)}")
    print(f"  Video orphan ditambah  : {total_orphans}")
    print(f"  Niche baru dibuat      : {len(niche_groups)}")
    print("-" * 40)
    for niche, urls in niche_groups.items():
        print(f"  {niche:<28} : {len(urls)} video")
    print("=" * 64)
    print(f"  [DONE] Tersimpan di: {args.output}")
    print("=" * 64)


if __name__ == "__main__":
    main()
