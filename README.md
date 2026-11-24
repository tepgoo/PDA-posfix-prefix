# PDA Pengenal Notasi Postfix dan Prefix

Program Python yang mengenali notasi matematika **Postfix** dan **Prefix** menggunakan *Pushdown Automaton* (PDA). Untuk setiap ekspresi yang dimasukkan, program menampilkan tabel transisi, jejak langkah, cara kerja, dan menghasilkan gambar desain PDA dalam bentuk PNG.

## Mengapa PDA?

Postfix dan prefix membutuhkan penghitungan operan dan operator yang jumlahnya tidak terbatas, misalnya `ab+`, `abc*+`, dan `abcd**+`. DFA/NFA tidak punya memori untuk itu, sedangkan PDA punya stack sehingga bisa menghitungnya.

## Contoh notasi

| Notasi | Posisi operator | Contoh untuk (a + b) × c |
|---|---|---|
| Infix | di antara operan | `(a + b) * c` |
| Postfix | setelah operan | `a b + c *` |
| Prefix | sebelum operan | `* + a b c` |

## Cara kerja PDA

Setiap token diubah menjadi salah satu dari dua simbol: **operan** (huruf atau angka) dan **operator** (`+ - * / ^`).

**PDA Postfix** (4 state: q0, q1, q2, qf). Stack menyimpan `X` untuk setiap nilai yang sudah ada.
- Operan: push `X`.
- Operator: dua `X` digabung menjadi satu `X`. Jika kurang dari dua, string ditolak.
- Input habis dan tersisa tepat satu `X`: diterima.

**PDA Prefix** (3 state: q0, q1, qf). Stack menyimpan `E` untuk setiap ekspresi yang masih dibutuhkan.
- Awal: stack berisi satu `E`.
- Operator: satu `E` diganti dua `E`.
- Operan: hapus satu `E`.
- Input habis dan stack kosong: diterima.

### Tabel transisi Postfix

| Dari | Input | Top | Pengganti | Ke |
|---|---|---|---|---|
| q0 | operan | Z | X Z | q0 |
| q0 | operan | X | X X | q0 |
| q0 | operator | X | ε | q1 |
| q1 | ε | X | X | q0 |
| q0 | ε | X | ε | q2 |
| q2 | ε | Z | Z | qf |

### Tabel transisi Prefix

| Dari | Input | Top | Pengganti | Ke |
|---|---|---|---|---|
| q0 | ε | Z | E Z | q1 |
| q1 | operator | E | E E | q1 |
| q1 | operan | E | ε | q1 |
| q1 | ε | Z | Z | qf |

`Z` adalah simbol dasar stack dan `ε` berarti tanpa input atau tanpa isi.

## Persyaratan

- Python 3
- matplotlib untuk membuat gambar PNG. Jika belum terpasang, program mencoba memasangnya otomatis. Jika gagal, pasang manual:

```
python3 -m pip install matplotlib
```

## Cara menjalankan

Buka terminal di folder program, lalu pilih salah satu:

| Tujuan | Perintah |
|---|---|
| Mode interaktif: ketik ekspresi, lalu lihat hasilnya | `python3 automata.py` |
| Analisis satu ekspresi langsung (beri tanda kutip) | `python3 automata.py "8 5 + 10 3 * -"` |
| Desain umum kedua PDA (PNG) | `python3 automata.py desain` |
| Menjalankan semua pengujian | `python3 automata.py tes` |

Di mode interaktif, ketik `desain` untuk desain umum dan `keluar` untuk berhenti.

### Aturan penulisan ekspresi

- Operan: huruf atau angka. Operator: `+ - * / ^`.
- Tanpa spasi, tiap karakter dianggap satu token, contoh `ab+`.
- Untuk operan lebih dari satu karakter, pisahkan dengan spasi, contoh `8 5 + 10 3 * -`.

### Contoh ekspresi

| Ekspresi | Hasil |
|---|---|
| `ab+` | Postfix |
| `abc*+` | Postfix |
| `8 5 + 10 3 * -` | Postfix |
| `+ab` | Prefix |
| `+a*bc` | Prefix |
| `- + 8 5 * 10 3` | Prefix |
| `8 + 5 - 10 * 3` | Bukan keduanya (infix) |

## Keluaran program

Untuk setiap ekspresi, program menampilkan:
1. Notasi yang cocok (Postfix, Prefix, atau bukan keduanya).
2. Tabel transisi dengan kolom "Dipakai" yang menunjukkan transisi mana yang dipakai ekspresi.
3. Jejak eksekusi: state, sisa input, dan isi stack di setiap langkah.
4. Cara kerja per langkah, beserta alasan jika ditolak.
5. Gambar PNG (`hasil_<nomor>_<notasi>.png`) berisi diagram state dengan jalur ekspresi berwarna merah, tabel transisi, dan jejak eksekusi.

## Pengujian

`python3 automata.py tes` menjalankan kasus uji manual dan 3.000 string acak yang dibandingkan dengan pembanding penghitung independen. Hasil yang diharapkan:

```
SEMUA TES LULUS
```

## Struktur kode

- `PDA`: kelas PDA nondeterministik dengan transisi ε. Transisi disimpan di tabel `delta`, dan tabel yang sama dipakai untuk menjalankan, mencetak, dan menggambar desain, sehingga desain selalu sama dengan automata yang dijalankan.
- `pda_postfix` dan `pda_prefix`: definisi kedua automata.
- `analisis_ekspresi`: analisis satu ekspresi (tabel, jejak, cara kerja, gambar).
- `tampilkan_desain`: desain umum kedua PDA.

# PDA-posfix-prefix
