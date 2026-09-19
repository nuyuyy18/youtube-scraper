"""
generate_pembahasan.py
Membaca CSV hasil scraping, lalu mengisi kolom 'pembahasan' dengan
ringkasan naratif menggunakan Google Gemini API.

Contoh hasil yang diinginkan (dari otw.csv):
  title      : "BUKTI TANDA CINTA - Ust. Heru Kusumahadi, Habib Ja'far..."
  pembahasan : "Bukti & Komitmen Cinta Sejati"

Usage:
  python generate_pembahasan.py result/jafaraljufrihayfala.csv
  python generate_pembahasan.py result/jafaraljufrihayfala.csv --api-key YOUR_KEY
"""

import argparse
import csv
import os
import sys
import time

FIELDNAMES = ["niche", "sub_niche", "pembahasan", "title", "youtube_url", "playlist"]


def build_prompt(titles):
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    return f"""Kamu adalah asisten yang meringkas judul video YouTube menjadi deskripsi topik yang singkat, informatif, dan dalam bahasa Indonesia yang natural.

Untuk setiap judul di bawah, tulis SATU baris ringkasan topik yang:
- Menjelaskan inti pembahasan video (bukan sekadar terjemahan judul)
- Singkat: 4-8 kata
- Tanpa nama pembicara, tanpa nomor episode
- Natural dan deskriptif, seperti: "Kesabaran Menghadapi Ujian Pasangan", "Menghindari Dosa & Menjaga Hati"

Judul:
{numbered}

Jawab HANYA dengan daftar bernomor yang sama persis, satu baris per judul. Jangan tambahkan penjelasan lain."""


def generate_pembahasan_batch(titles, model):
    if not titles:
        return []
    prompt = build_prompt(titles)
    response = model.generate_content(prompt)
    text = response.text.strip()
    results = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0].isdigit():
            dot_idx = line.find(".")
            if dot_idx != -1:
                line = line[dot_idx + 1:].strip()
        results.append(line)
    if len(results) != len(titles):
        print(f"  [!] Hasil AI ({len(results)}) tidak cocok dengan jumlah judul ({len(titles)}), pakai fallback")
        return titles
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate kolom 'pembahasan' dengan Gemini AI")
    parser.add_argument("csv_file", help="Path ke file CSV")
    parser.add_argument("--api-key", default=os.environ.get("GEMINI_API_KEY", ""), help="Gemini API key")
    parser.add_argument("--batch-size", type=int, default=10, help="Jumlah judul per request (default: 10)")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Model Gemini (default: gemini-2.0-flash)")
    args = parser.parse_args()

    if not args.api_key:
        print("[!] API key tidak ditemukan. Gunakan --api-key atau set env GEMINI_API_KEY")
        sys.exit(1)

    if not os.path.isfile(args.csv_file):
        print(f"[!] File tidak ditemukan: {args.csv_file}")
        sys.exit(1)

    try:
        import google.generativeai as genai
    except ImportError:
        print("[!] Jalankan: pip install google-generativeai")
        sys.exit(1)

    genai.configure(api_key=args.api_key)
    model = genai.GenerativeModel(args.model)
    print(f"[*] Model: {args.model}")

    rows = []
    with open(args.csv_file, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        file_fields = reader.fieldnames or []
        for row in reader:
            rows.append(row)
    print(f"[*] Dibaca {len(rows)} baris dari '{args.csv_file}'")

    out_fields = FIELDNAMES if all(f in file_fields for f in FIELDNAMES) else file_fields
    to_process_idx = [i for i, r in enumerate(rows) if r.get("title", "").strip()]
    print(f"[*] {len(to_process_idx)} baris dengan judul akan diproses")

    total = len(to_process_idx)
    done = 0

    for start in range(0, total, args.batch_size):
        batch_idx = to_process_idx[start:start + args.batch_size]
        batch_titles = [rows[i]["title"] for i in batch_idx]
        print(f"  Batch {start//args.batch_size + 1}: {len(batch_titles)} judul...", end=" ", flush=True)
        try:
            summaries = generate_pembahasan_batch(batch_titles, model)
            for i, summary in zip(batch_idx, summaries):
                rows[i]["pembahasan"] = summary
            done += len(batch_idx)
            print("OK")
        except Exception as e:
            print(f"Error: {e}")
            for i, title in zip(batch_idx, batch_titles):
                rows[i]["pembahasan"] = title
        if start + args.batch_size < total:
            time.sleep(1)

    print(f"\n[OK] Selesai: {done}/{total} judul diproses")

    out_file = args.csv_file
    with open(out_file, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(out_fields)
        current_playlist = None
        first = True
        for row in rows:
            title = row.get("title", "").strip()
            playlist = row.get("playlist", "").strip()
            if not title:
                continue
            if playlist != current_playlist:
                if not first:
                    writer.writerow([""] * len(out_fields))
                current_playlist = playlist
                first = False
            writer.writerow([row.get(field, "") for field in out_fields])

    print(f"[OK] Disimpan ke: {out_file}")


if __name__ == "__main__":
    main()
