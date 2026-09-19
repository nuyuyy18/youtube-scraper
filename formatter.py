"""
formatter.py
Membaca semua CSV hasil scraping per-playlist dari folder output,
lalu menghasilkan satu file teks terstruktur:

  NAMA PLAYLIST
  https://youtube.com/watch?v=xxx
  https://youtube.com/watch?v=yyy

  NAMA PLAYLIST BERIKUTNYA
  https://youtube.com/watch?v=zzz
  ...
"""

import argparse
import csv
import os
import sys
from collections import OrderedDict


def read_all_csvs(folder: str) -> list[dict]:
    """Baca semua file CSV dari folder secara berurutan."""
    rows = []
    for fname in sorted(os.listdir(folder)):
        if not fname.endswith(".csv"):
            continue
        fpath = os.path.join(folder, fname)
        with open(fpath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    return rows


FIELDNAMES = ["niche", "sub_niche", "pembahasan", "title", "youtube_url", "playlist"]


def main():
    parser = argparse.ArgumentParser(
        description="Format hasil scraping menjadi file teks terstruktur per playlist"
    )
    parser.add_argument(
        "folder",
        type=str,
        nargs="?",
        default="result/output_terasdakwah",
        help="Folder berisi file CSV per-playlist (default: result/output_terasdakwah)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Nama file output (default: grouped_<folder>.txt)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f"[!] Folder tidak ditemukan: {args.folder}")
        sys.exit(1)

    # ── Baca semua CSV ───────────────────────────────────
    all_rows = read_all_csvs(args.folder)
    if not all_rows:
        print("[!] Tidak ada data CSV di folder tersebut.")
        sys.exit(1)

    print(f"[*] Dibaca {len(all_rows)} baris dari folder '{args.folder}'")

    # ── Kelompokkan per playlist ─────────────────────────
    # Gunakan OrderedDict agar urutan tetap sesuai file CSV
    groups: OrderedDict[str, list[dict]] = OrderedDict()

    for row in all_rows:
        playlist = (row.get("playlist") or "").strip()
        url      = (row.get("youtube_url") or "").strip()
        niche    = (row.get("niche") or "Uncategorized").strip()
        sub      = (row.get("sub_niche") or "General").strip()

        if not url:
            continue

        # Jika tidak ada nama playlist, gunakan niche/sub_niche sebagai grup
        if not playlist:
            playlist = f"{niche} — {sub}" if niche != "Uncategorized" else "Lain-lain"
            row["playlist"] = playlist

        if playlist not in groups:
            groups[playlist] = []

        # Hindari duplikat URL
        if not any(r.get("youtube_url") == url for r in groups[playlist]):
            groups[playlist].append(row)

    total_groups = len(groups)
    total_links  = sum(len(v) for v in groups.values())
    print(f"[*] Ditemukan {total_groups} playlist, {total_links} link total")

    # ── Tulis file output (semua kolom) ──────────────────
    folder_name = os.path.basename(args.folder.rstrip("/\\"))
    out_file    = args.output or os.path.join("result", f"grouped_{folder_name}.csv")

    # Tentukan fieldnames: pakai FIELDNAMES baku jika tersedia, fallback ke kolom data
    sample_keys = list(all_rows[0].keys()) if all_rows else []
    out_fields  = FIELDNAMES if all(f in sample_keys for f in FIELDNAMES) else sample_keys

    import csv as csv_module

    with open(out_file, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv_module.writer(f)
        # Header
        writer.writerow(out_fields)
        for i, (playlist, rows) in enumerate(groups.items()):
            for row in rows:
                writer.writerow([row.get(field, "") for field in out_fields])
            # Baris kosong pemisah antar playlist (kecuali terakhir)
            if i < total_groups - 1:
                writer.writerow([""] * len(out_fields))

    print(f"[✓] Selesai! Disimpan ke: {out_file}")
    print(f"    {total_groups} playlist  |  {total_links} link")

    # ── Preview ──────────────────────────────────────────
    print("\n--- Preview (20 baris pertama) ---")
    with open(out_file, encoding="utf-8") as f:
        for i, line in enumerate(f):
            print(line, end="")
            if i >= 19:
                break
    print("\n---")


if __name__ == "__main__":
    main()
