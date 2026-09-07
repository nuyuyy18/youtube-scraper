import argparse
import csv
import os
import re
import sys
import yt_dlp

# ─────────────────────────────────────────────
# NICHE TAXONOMY
# ─────────────────────────────────────────────
TAXONOMY = {
    "Beauty": {
        "Skincare":  ["skincare", "skin", "acne", "serum", "moisturizer", "sunscreen",
                      "glowing", "kulit", "jerawat", "wajah"],
        "Makeup":    ["makeup", "make up", "cosmetic", "lipstick", "foundation",
                      "eyeshadow", "tutorial makeup", "dandan", "rias"],
        "Haircare":  ["hair", "haircare", "shampoo", "rambut", "hairstyle", "salon",
                      "conditioner", "botak"],
        "Bodycare":  ["bodycare", "lotion", "body wash", "sabun mandi", "deodorant",
                      "parfum", "badan"],
    },
    "Self Improvement": {
        "Confidence":   ["confidence", "percaya diri", "insecure", "self esteem",
                         "brave", "berani"],
        "Productivity": ["productivity", "produktif", "time management", "focus",
                         "fokus", "habits", "kebiasaan", "procrastination", "malas"],
        "Mindset":      ["mindset", "pola pikir", "stoic", "stoicism", "mental",
                         "growth mindset", "berpikir"],
        "Discipline":   ["discipline", "disiplin", "konsisten", "consistency",
                         "motivation", "motivasi", "willpower"],
    },
    "Finance": {
        "Saving":      ["saving", "menabung", "frugal", "hemat", "uang", "nabung"],
        "Investing":   ["investing", "investasi", "saham", "crypto", "reksa dana",
                        "trading", "dividend"],
        "Budgeting":   ["budgeting", "anggaran", "pengeluaran", "cashflow",
                        "keuangan", "catatan keuangan"],
        "Side Hustle": ["side hustle", "passive income", "freelance",
                        "bisnis sampingan", "uang tambahan", "cuan"],
    },
    "Religion": {
        "Dakwah":          ["dakwah", "teras dakwah", "otw talk", "on the way talk",
                            "ustadz", "ustazah", "habib", "ceramah", "khutbah",
                            "kajian", "ngaji", "pengajian", "hijrah", "islam",
                            "muslim", "muslimah", "sunnah", "quran", "hadits",
                            "aqidah", "syariah", "fiqih", "tazkiyah"],
        "Motivasi Islami": ["motivasi islam", "motivasi islami", "semangat islam",
                            "inspirasi islami", "sabar", "ikhlas", "tawakkal",
                            "syukur", "rezeki"],
        "Akhlak":          ["akhlak", "adab", "sopan santun", "karakter muslim",
                            "budi pekerti", "etika islam"],
        "Keluarga Islami": ["keluarga islami", "parenting islami",
                            "pernikahan islami", "nikah", "pernikahan",
                            "keluarga muslim", "rumah tangga islami"],
    },
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def classify_niche(title: str, description: str) -> tuple[str, str]:
    text = ((title or "") + " " + (description or "")).lower()
    best_niche, best_sub, max_score = "Uncategorized", "General", 0
    for niche, sub_niches in TAXONOMY.items():
        for sub_niche, keywords in sub_niches.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score, best_niche, best_sub = score, niche, sub_niche
    return best_niche, best_sub


def normalize_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def safe_filename(text: str, max_len: int = 60) -> str:
    """Buat nama file yang aman dari judul playlist."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", text)
    cleaned = re.sub(r'\s+', "_", cleaned.strip())
    return cleaned[:max_len]


def sep(char="─", width=64):
    print(char * width)

# ─────────────────────────────────────────────
# SCRAPER
# ─────────────────────────────────────────────

YDL_FLAT = {
    "extract_flat": "in_playlist",
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": True,
}


def get_playlists(channel_url: str) -> list[dict]:
    """Ambil semua playlist dari channel."""
    playlists_url = channel_url.rstrip("/") + "/playlists"
    print(f"  Mengambil daftar playlist dari: {playlists_url}")

    with yt_dlp.YoutubeDL(YDL_FLAT) as ydl:
        info = ydl.extract_info(playlists_url, download=False)

    if not info:
        return []

    entries = info.get("entries", [])
    playlists = []
    for entry in entries:
        if not entry:
            continue
        pl_id = entry.get("id")
        pl_title = entry.get("title", "Untitled")
        if pl_id:
            playlists.append({
                "id": pl_id,
                "title": pl_title,
                "url": f"https://www.youtube.com/playlist?list={pl_id}",
            })
    return playlists


def get_videos_from_playlist(playlist: dict) -> list[dict]:
    """Ambil semua video dari satu playlist."""
    with yt_dlp.YoutubeDL(YDL_FLAT) as ydl:
        info = ydl.extract_info(playlist["url"], download=False)

    if not info:
        return []

    videos = []
    for entry in (info.get("entries") or []):
        if not entry:
            continue
        vid_id = entry.get("id")
        if vid_id:
            videos.append({
                "id":          vid_id,
                "title":       entry.get("title", ""),
                "description": entry.get("description") or "",
                "playlist_id": playlist["id"],
                "playlist":    playlist["title"],
            })
    return videos

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="YouTube Playlist Scraper — pisahkan link per playlist",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "channel_url",
        type=str,
        help="URL channel YouTube, contoh: https://www.youtube.com/@terasdakwah",
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        default=False,
        help="Simpan semua playlist ke SATU file CSV gabungan (default: satu file per playlist)",
    )
    args = parser.parse_args()

    sep("═")
    print("  YouTube Playlist Scraper")
    sep("═")
    print(f"  Channel : {args.channel_url}")
    print(f"  Mode    : {'Gabungan (1 CSV)' if args.combined else 'Per Playlist'}")
    sep()

    # ── 1. Ambil daftar playlist ────────────────
    print("\n[1/3] Mengambil daftar playlist...\n")
    playlists = get_playlists(args.channel_url)

    if not playlists:
        print("[!] Tidak ada playlist ditemukan di channel ini.")
        sys.exit(1)

    print(f"\n  Ditemukan {len(playlists)} playlist:")
    for i, pl in enumerate(playlists, 1):
        print(f"  [{i:>3}] {pl['title']}")

    # ── 2. Scrape video tiap playlist ───────────
    sep()
    print(f"\n[2/3] Mengambil video dari setiap playlist...\n")

    all_rows   = []       # untuk mode combined
    seen_ids   = set()    # global deduplikasi antar playlist
    pl_results = []       # hasil per playlist

    for i, pl in enumerate(playlists, 1):
        print(f"  [{i:>3}/{len(playlists)}] {pl['title']}", end=" → ", flush=True)
        videos = get_videos_from_playlist(pl)

        # Deduplikasi dalam playlist & global
        unique = []
        for v in videos:
            if v["id"] not in seen_ids:
                seen_ids.add(v["id"])
                unique.append(v)

        print(f"{len(unique)} video unik (dari {len(videos)} total)")

        if unique:
            pl_results.append({
                "playlist": pl,
                "videos":   unique,
            })

    total_videos = sum(len(r["videos"]) for r in pl_results)
    sep()
    print(f"\n  Total video unik dari semua playlist: {total_videos}")

    # ── 3. Klasifikasi & Export ─────────────────
    sep()
    print(f"\n[3/3] Klasifikasi niche & export CSV...\n")

    # Buat folder output di dalam result/
    handle    = re.search(r"@([\w\-]+)", args.channel_url)
    ch_handle = handle.group(1).lower() if handle else "channel"
    out_dir   = os.path.join("result", f"output_{ch_handle}")
    os.makedirs(out_dir, exist_ok=True)

    combined_rows = []

    for r in pl_results:
        pl        = r["playlist"]
        videos    = r["videos"]
        pl_rows   = []

        sep("─", 40)
        print(f"  Playlist: {pl['title']}  ({len(videos)} video)")

        for video in videos:
            title       = video.get("title") or ""
            description = video.get("description") or ""
            url         = normalize_url(video["id"])
            niche, sub  = classify_niche(title, description)

            title_disp = title[:55] + "…" if len(title) > 55 else title
            print(f"    [{niche:<17}] {title_disp}")

            row = {
                "youtube_url": url,
                "playlist":    pl["title"],
                "niche":       niche,
                "sub_niche":   sub,
            }
            pl_rows.append(row)
            combined_rows.append(row)

        # Simpan CSV per playlist
        if not args.combined:
            fname = safe_filename(pl["title"]) + ".csv"
            fpath = os.path.join(out_dir, fname)
            with open(fpath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["youtube_url", "playlist", "niche", "sub_niche"]
                )
                writer.writeheader()
                writer.writerows(pl_rows)
            print(f"    → Disimpan: {fpath}  ({len(pl_rows)} baris)")

    # Mode combined: satu CSV gabungan
    if args.combined:
        combined_path = os.path.join("result", f"youtube_links_{ch_handle}_all_playlists.csv")
        with open(combined_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["youtube_url", "playlist", "niche", "sub_niche"]
            )
            writer.writeheader()
            writer.writerows(combined_rows)

    # ── Ringkasan ───────────────────────────────
    sep("═")
    print("  RINGKASAN HASIL")
    sep("═")
    print(f"  Channel    : {args.channel_url}")
    print(f"  Playlist   : {len(pl_results)}")
    print(f"  Total video: {total_videos}")
    sep("─", 40)

    if args.combined:
        print(f"  File       : {combined_path}")
    else:
        print(f"  Folder CSV : {out_dir}/")
        for r in pl_results:
            fname = safe_filename(r["playlist"]["title"]) + ".csv"
            print(f"             ├── {fname}  ({len(r['videos'])} video)")

    sep("═")


if __name__ == "__main__":
    main()
