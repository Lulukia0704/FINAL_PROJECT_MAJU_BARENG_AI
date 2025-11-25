ANALISIS PENULISAN ILMIAH
Final Project – Maju Bareng AI (Hacktiv8)

Platform AI yang dirancang untuk membantu akademisi dan mahasiswa dalam menulis karya ilmiah dengan lebih mudah, cepat, dan terstruktur.

#Deskripsi Project

Asisten Penulisan Ilmiah adalah aplikasi web yang memanfaatkan Google Gemini AI untuk mendukung proses penulisan akademis.
Tujuannya sederhana: membuat aktivitas membaca jurnal, menulis, dan memvalidasi kutipan menjadi jauh lebih efisien.

Dengan bantuan AI, aplikasi ini dapat merangkum jurnal, memparafrase teks, hingga mengecek format kutipan secara otomatis—cukup lewat browser, tanpa instalasi apa pun.

#Fitur Utama
1. Sintesis Jurnal Penelitian

Upload 2–5 jurnal PDF.

Sistem akan membaca isi jurnal secara menyeluruh.

Menyajikan ringkasan temuan utama.

Mengidentifikasi research gap antar jurnal.

Memberi rekomendasi untuk penelitian selanjutnya.

2. Parafrase & Gaya Penulisan

Parafrase teks dengan makna tetap terjaga.

Mengubah teks ke format akademis (APA, MLA, Chicago).

Menyediakan dua versi parafrase agar pengguna bisa memilih.

Hasil parafrase disesuaikan dengan bahasa ilmiah yang baik.

3. Cek Kutipan

Memeriksa apakah kutipan sudah sesuai format standar.

Mengecek kelengkapan elemen citasi.

Bisa dibandingkan langsung dengan PDF sumber.

Memberikan saran perbaikan yang jelas dan mudah diikuti.

#Cara Menggunakan Sistem
Prasyarat

Browser modern (Chrome, Firefox, Edge, Safari)

Koneksi internet stabil

Google Gemini API Key

Langkah 1: Menyiapkan API Key

Buka Google AI Studio.

Login dan buat API Key baru.

Copy API Key tersebut.

Buka file academic-assistant.html.

Masukkan API Key pada baris 15:

const GEMINI_API_KEY = "PASTE_API_KEY_ANDA_DISINI";

Langkah 2: Menjalankan Aplikasi

Download file academic-assistant.html

Buka langsung melalui browser
atau gunakan Live Server di VS Code.

Langkah 3: Menggunakan Fitur
A. Sintesis Jurnal

Unggah PDF

Klik “Mulai Sintesis”

Tunggu proses ±20–60 detik

Hasil sintesis muncul dan bisa diunduh

B. Parafrase

Pilih mode: parafrase/APA/MLA/Chicago

Masukkan teks

Klik “Proses Teks”

Unduh atau salin hasilnya

C. Cek Kutipan

Tempel kutipan

(Opsional) unggah PDF sumber

Klik “Cek Kutipan”

Perbaikan langsung ditampilkan

#Bagaimana Sistem Ini Bekerja?

Aplikasi ini sepenuhnya berjalan di sisi frontend. Saat pengguna mengunggah PDF atau memasukkan teks:

File dikonversi ke Base64.

Data dikirim ke Gemini melalui API.

Gemini membaca, menganalisis, dan memproses dokumen.

Hasilnya dikembalikan ke aplikasi untuk ditampilkan.

Model yang digunakan adalah Gemini 1.5 Flash, yang dikenal cepat, mampu membaca PDF secara langsung, dan memiliki context window besar sehingga dapat memproses banyak dokumen sekaligus.

#Optimasi & Rate Limiting

Untuk menghindari error “rate limit exceeded”, aplikasi:

Memberi jeda otomatis 5 detik antar request.

Membatasi maksimal 2 PDF per proses.

Melakukan retry otomatis jika error.

Menyediakan tombol reset request counter.

#Teknologi yang Digunakan
Frontend

React 18

Tailwind CSS

Babel Standalone

AI

Google Gemini 1.5 Flash

Arsitektur

Client-side only

Tidak memerlukan backend atau server tambahan

#Troubleshooting
Rate Limit

Biasanya terjadi jika terlalu banyak request dalam waktu singkat.
Solusi: reset counter, tunggu 2–3 menit, lalu refresh.

API Key Invalid

Periksa kembali apakah key ditulis tanpa spasi atau karakter tambahan.

PDF Tidak Terbaca

Gunakan PDF berukuran kecil (<5 MB), tidak terenkripsi, dan berbasis teks.

#Roadmap Pengembangan
Versi 2.0

Support .docx

Export hasil ke PDF

Integrasi dengan Zotero/Mendeley

Plagiarism checker

Dukungan multi-bahasa

Versi 2.5

Fitur kolaborasi

Cloud storage

Template penulisan otomatis

Citation generator lengkap

#Kontribusi

Kontribusi sangat terbuka.
Cukup fork, buat branch, commit perubahan, lalu kirim pull request.

#Tim Pengembang

Final Project Hacktiv8: Maju Bareng AI

Developer: Luluk Asti Qomariah

Mentor: Mukhlas Adib Rasyidy
