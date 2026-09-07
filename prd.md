
# PRD — YouTube Link Scraper & Niche Classifier

## 1. Tujuan

Membangun sistem untuk:

**Search YouTube → Scrape link video → Klasifikasi niche → Kelompokkan → Export CSV**

Sistem hanya menangani proses **pengumpulan link YouTube dan klasifikasi niche**.

Hasil akhirnya berupa kumpulan link YouTube yang sudah dikelompokkan berdasarkan niche dan sub-niche.

---

## 2. Scope

### Termasuk

* Pencarian video YouTube
* Scraping link video YouTube
* Normalisasi URL
* Deduplication
* Klasifikasi niche
* Klasifikasi sub-niche
* Pengelompokan link berdasarkan niche
* Review/edit klasifikasi secara manual
* Export CSV

### Tidak termasuk

* Scraping transcript
* Mengambil isi/video content
* Summarization
* Analisis isi video
* Relevance filtering
* Pembuatan ebook
* Rewriting konten
* Analisis channel
* Analytics performa video
* Export Excel
* Export TXT
* Export JSON
* Export PDF

---

## 3. YouTube Scraping

Sistem melakukan pencarian YouTube dan mengumpulkan video yang ditemukan.

Data yang diambil secara internal:

```text
video_id
youtube_url
title
description
channel_name
```

Data seperti title dan description digunakan untuk membantu proses klasifikasi niche.

Output yang ditampilkan kepada user cukup:

```text
YouTube URL
Niche
Sub-Niche
```

---

## 4. URL Normalization

Semua format URL YouTube diubah menjadi format standar.

Contoh:

```text
https://www.youtube.com/watch?v=ABC123
https://youtu.be/ABC123
https://www.youtube.com/watch?v=ABC123&utm_source=xxx
```

menjadi:

```text
https://www.youtube.com/watch?v=ABC123
```

---

## 5. Deduplication

Video yang sama tidak boleh disimpan lebih dari satu kali.

Deduplication dilakukan berdasarkan:

```text
YouTube Video ID
```

Contoh:

```text
ABC123
ABC123
ABC123
```

menjadi:

```text
ABC123
```

---

## 6. Niche Classification

Setiap video diklasifikasikan berdasarkan informasi yang tersedia, terutama:

* Title
* Description
* Keyword
* Metadata yang tersedia

AI menentukan:

### Main Niche

Contoh:

```text
Beauty
Self Improvement
Finance
Career
Relationship
Fashion
Productivity
```

### Sub-Niche

Contoh:

```text
Beauty
└── Skincare

Self Improvement
└── Confidence

Finance
└── Saving
```

---

## 7. Custom Niche Taxonomy

User dapat menentukan kategori niche yang ingin digunakan.

Contoh:

```text
Beauty
├── Skincare
├── Makeup
├── Haircare
└── Bodycare

Self Improvement
├── Confidence
├── Productivity
├── Mindset
└── Discipline

Finance
├── Saving
├── Investing
├── Budgeting
└── Side Hustle
```

AI mengklasifikasikan setiap video berdasarkan kategori tersebut.

Jika tidak menggunakan custom taxonomy, sistem dapat menggunakan kategori default.

---

## 8. Manual Classification

User dapat mengubah hasil klasifikasi AI secara manual.

Contoh:

```text
YouTube URL
https://youtube.com/watch?v=ABC123

Niche:
Self Improvement

Sub-Niche:
Confidence
```

User dapat mengubahnya menjadi:

```text
Niche:
Beauty

Sub-Niche:
Appearance
```

Perubahan disimpan ke database.

---

## 9. Dashboard

Dashboard menampilkan seluruh hasil scraping dalam bentuk tabel.

| YouTube URL                | Niche            | Sub-Niche  |
| -------------------------- | ---------------- | ---------- |
| youtube.com/watch?v=ABC123 | Beauty           | Skincare   |
| youtube.com/watch?v=DEF456 | Self Improvement | Confidence |
| youtube.com/watch?v=GHI789 | Finance          | Saving     |

Fitur:

* Filter berdasarkan niche
* Filter berdasarkan sub-niche
* Search
* Edit niche
* Edit sub-niche
* Hapus data
* Export CSV

---

## 10. Grouping

Link otomatis dikelompokkan berdasarkan niche.

Contoh:

```text
BEAUTY

https://youtube.com/watch?v=ABC123
https://youtube.com/watch?v=ABC456
https://youtube.com/watch?v=ABC789


SELF IMPROVEMENT

https://youtube.com/watch?v=DEF123
https://youtube.com/watch?v=DEF456
https://youtube.com/watch?v=DEF789


FINANCE

https://youtube.com/watch?v=GHI123
https://youtube.com/watch?v=GHI456
```

---

## 11. Export CSV

Sistem hanya menyediakan export dalam format CSV.

Format:

```csv
youtube_url,niche,sub_niche
https://youtube.com/watch?v=ABC123,Beauty,Skincare
https://youtube.com/watch?v=DEF456,Self Improvement,Confidence
https://youtube.com/watch?v=GHI789,Finance,Saving
```

Kolom:

| Column      | Keterangan        |
| ----------- | ----------------- |
| youtube_url | URL video YouTube |
| niche       | Main niche        |
| sub_niche   | Sub-niche         |

---

## 12. Database

### projects

```text
id
name
created_at
```

### youtube_links

```text
id
project_id
video_id
youtube_url
title
description
channel_name
niche
sub_niche
created_at
updated_at
```

### scraping_jobs

```text
id
project_id
status
collected_count
started_at
completed_at
error_message
```

---

## 13. Workflow

```text
YouTube Search
      ↓
Collect Video URLs
      ↓
Normalize URL
      ↓
Deduplicate
      ↓
Niche Classification
      ↓
Niche + Sub-Niche
      ↓
Save Database
      ↓
Dashboard
      ↓
Manual Review
      ↓
Export CSV
```

---

## 14. MVP

Versi pertama cukup memiliki:

### Scraping

* Search YouTube
* Collect video URLs
* Normalize URL
* Deduplicate

### Classification

* Niche classification
* Sub-niche classification
* Custom niche taxonomy

### Management

* Dashboard
* Filter niche
* Manual edit
* Delete data

### Output

* Grouped YouTube links
* Export CSV

---

## 15. Prinsip Utama

Sistem ini **hanya bertugas mencari dan mengelompokkan link YouTube**.

```text
YouTube
   ↓
Scraping
   ↓
YouTube Links
   ↓
Niche Classification
   ↓
Grouped Links
   ↓
CSV
```

Tidak ada proses membaca isi video, transcript, summarization, filtering konten, atau pembuatan ebook di dalam sistem ini.
