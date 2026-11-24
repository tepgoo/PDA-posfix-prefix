"""
Automata Pengenal Notasi Postfix dan Prefix
============================================
Menggunakan PDA (Pushdown Automaton), karena notasi ini BUKAN bahasa reguler
(butuh "memori" berupa stack untuk menghitung operan/operator).

Alfabet input (diklasifikasikan per karakter):
    'a' = operan    -> huruf atau angka tunggal (a-z, A-Z, 0-9)
    'o' = operator  -> + - * / ^

Cara pakai:
    python3 automata.py                 -> ketik ekspresi, keluar tabel transisi,
                                           cara kerja, dan gambar PNG-nya
    python3 automata.py "8 5 + 10 3 * -" -> langsung analisis satu ekspresi
    python3 automata.py desain          -> desain umum kedua PDA (PNG)
    python3 automata.py tes             -> jalankan pengujian
"""

import random
import re
import sys

OPERATOR = set("+-*/^")


def klasifikasi(ch):
    """Ubah satu karakter menjadi simbol input PDA ('a' atau 'o')."""
    if ch.isalnum():
        return "a"
    if ch in OPERATOR:
        return "o"
    return None  # karakter tidak dikenal -> ditolak


class PDA:
    """
    PDA nondeterministik dengan epsilon-move.

    delta: {(state, simbol_input, top_stack): [(state_baru, (isi_push...)), ...]}
      - simbol_input "" artinya epsilon-move (tidak membaca input)
      - isi_push ditulis top-first; top stack yang lama SELALU di-pop
        lalu diganti dengan isi_push (tuple kosong = hanya pop)
    Penerimaan: berhenti di state final setelah SEMUA input terbaca.
    """

    def __init__(self, nama, start, stack_awal, final, delta):
        self.nama = nama
        self.start = start
        self.stack_awal = stack_awal
        self.final = final
        self.delta = delta

    def jalankan(self, teks):
        """
        Jalankan PDA pada satu ekspresi. Mengembalikan dict:
          ok     : True jika diterima
          token  : daftar token hasil tokenisasi
          jalur  : daftar langkah (dict: state, pos, stack, baca, transisi);
                   sampai penerimaan, atau sampai titik macet jika ditolak
          alasan : penjelasan singkat bila ditolak
        """
        teks = teks.strip()
        hasil = {"ok": False, "token": [], "jalur": [], "alasan": ""}
        if not teks:
            hasil["alasan"] = "input kosong"
            return hasil

        # Tokenisasi: jika ada spasi, operan boleh multi-karakter (mis. "10");
        # jika tidak ada spasi, tiap karakter dianggap satu token (mis. "ab+").
        if any(c.isspace() for c in teks):
            token = re.findall(r"[A-Za-z0-9]+|[+\-*/^]|\S", teks)
        else:
            token = list(teks)
        hasil["token"] = token

        simbol = []
        for tk in token:
            if tk.isalnum():
                simbol.append("a")
            elif tk in OPERATOR:
                simbol.append("o")
            else:
                hasil["alasan"] = f"token '{tk}' tidak ada di alfabet"
                return hasil

        # konfigurasi: (state, posisi_input, stack_tuple_top_first)
        awal = (self.start, 0, (self.stack_awal,))
        induk = {awal: (None, None, None)}  # konfigurasi -> (induk, transisi, token dibaca)
        tumpukan = [awal]
        terjauh = awal
        diterima = None

        while tumpukan:
            konfig = tumpukan.pop()
            state, i, stack = konfig
            if i >= terjauh[1]:
                terjauh = konfig
            if state == self.final and i == len(simbol):
                diterima = konfig
                break
            if not stack:
                continue
            top, sisa = stack[0], stack[1:]

            pilihan = []
            if i < len(simbol):  # transisi yang membaca input
                for (q, push) in self.delta.get((state, simbol[i], top), []):
                    pilihan.append((q, i + 1, push, (state, simbol[i], top, q, push), token[i]))
            for (q, push) in self.delta.get((state, "", top), []):  # epsilon
                pilihan.append((q, i, push, (state, "", top, q, push), None))

            for (q, j, push, kunci, baca) in pilihan:
                baru = (q, j, tuple(push) + sisa)
                if baru not in induk:
                    induk[baru] = (konfig, kunci, baca)
                    tumpukan.append(baru)

        akhir = diterima or terjauh
        jalur, k = [], akhir
        while k is not None:
            prev, kunci, baca = induk[k]
            jalur.append({"state": k[0], "pos": k[1], "stack": k[2],
                          "transisi": kunci, "baca": baca})
            k = prev
        jalur.reverse()
        hasil["jalur"] = jalur
        hasil["ok"] = diterima is not None

        if not hasil["ok"]:
            state, i, stack = terjauh
            if i < len(simbol) and state == self.final:
                hasil["alasan"] = (f"ekspresi sudah lengkap di {state}, tetapi input masih "
                                   f"bersisa mulai '{token[i]}'")
            elif i < len(simbol):
                top = stack[0] if stack else "kosong"
                hasil["alasan"] = (f"macet di {state}: tidak ada transisi untuk "
                                   f"{NAMA_INPUT[simbol[i]]} '{token[i]}' dengan top stack {top}")
            else:
                hasil["alasan"] = (f"input habis, tetapi PDA berhenti di {state} dengan stack "
                                   f"{' '.join(stack)} (seharusnya di {self.final} "
                                   f"dengan stack {self.stack_awal})")
        return hasil

    def proses(self, teks):
        """Kembalikan (diterima: bool, jejak: list[str])."""
        h = self.jalankan(teks)
        if not h["ok"]:
            return False, [h["alasan"] + " -> ditolak"]
        baris = []
        for lg in h["jalur"]:
            sisa = " ".join(h["token"][lg["pos"]:])
            if lg["transisi"] is None:
                ket = "mulai"
            else:
                ket = (f"baca '{lg['baca']}'" if lg["baca"] is not None else "epsilon")
                ket += f", top={lg['transisi'][2]}"
            baris.append(f"({lg['state']}, sisa='{sisa}', stack={list(lg['stack'])})  <- {ket}")
        return True, baris


# ---------------------------------------------------------------------------
# PDA POSTFIX  (operan operan operator)   contoh: ab+  ,  abc*+
# Stack berisi X = "satu operan/hasil yang sudah ada". Z = penanda dasar stack.
# Operator butuh 2 operan: pop X (q0->q1), lalu cek X lagi dengan epsilon (q1->q0).
# Di akhir input, harus tersisa tepat 1 X: pop X (q2), lalu dasar Z terlihat -> qf.
# ---------------------------------------------------------------------------
pda_postfix = PDA(
    nama="Postfix",
    start="q0", stack_awal="Z", final="qf",
    delta={
        ("q0", "a", "Z"): [("q0", ("X", "Z"))],
        ("q0", "a", "X"): [("q0", ("X", "X"))],
        ("q0", "o", "X"): [("q1", ())],
        ("q1", "", "X"):  [("q0", ("X",))],
        ("q0", "", "X"):  [("q2", ())],
        ("q2", "", "Z"):  [("qf", ("Z",))],
    },
)

# ---------------------------------------------------------------------------
# PDA PREFIX  (operator operan operan)   contoh: +ab  ,  +a*bc
# Stack berisi E = "masih butuh satu ekspresi". Mulai dengan satu E.
# Operator : ganti E dengan E E (butuh dua ekspresi lagi)
# Operan   : pop E (satu kebutuhan terpenuhi)
# Diterima jika stack tinggal Z dan input habis.
# ---------------------------------------------------------------------------
pda_prefix = PDA(
    nama="Prefix",
    start="q0", stack_awal="Z", final="qf",
    delta={
        ("q0", "", "Z"):  [("q1", ("E", "Z"))],
        ("q1", "o", "E"): [("q1", ("E", "E"))],
        ("q1", "a", "E"): [("q1", ())],
        ("q1", "", "Z"):  [("qf", ("Z",))],
    },
)


# ---------------------------------------------------------------------------
# Pembanding independen (pakai penghitung) untuk menguji kebenaran PDA
# ---------------------------------------------------------------------------
def cek_postfix_counter(teks):
    c = 0
    for ch in teks:
        s = klasifikasi(ch)
        if s == "a":
            c += 1
        elif s == "o":
            if c < 2:
                return False
            c -= 1
        else:
            return False
    return c == 1


def cek_prefix_counter(teks):
    # prefix valid <=> dibaca dari kanan, aturannya sama dengan postfix
    return cek_postfix_counter(teks[::-1])


def tampilkan(teks, tampil_jejak=True):
    for pda in (pda_postfix, pda_prefix):
        ok, jejak = pda.proses(teks)
        print(f"\n[{pda.nama}] '{teks}' -> {'DITERIMA' if ok else 'DITOLAK'}")
        if tampil_jejak:
            for baris in jejak:
                print("   ", baris)


def jalankan_tes():
    kasus = [
        # (string, postfix?, prefix?)
        ("a", True, True),
        ("ab+", True, False),
        ("+ab", False, True),
        ("abc*+", True, False),
        ("+a*bc", False, True),
        ("ab+cd-*", True, False),
        ("*+ab-cd", False, True),
        ("a+", False, False),
        ("+a", False, False),
        ("ab", False, False),
        ("+ab+", False, False),
        ("a b +", True, False),
        ("8 5 + 10 3 * -", True, False),
        ("- + 8 5 * 10 3", False, True),
        ("8 + 5 - 10 * 3", False, False),
        ("a$b", False, False),
        ("", False, False),
    ]
    gagal = 0
    for s, pf, pr in kasus:
        r1 = pda_postfix.proses(s)[0]
        r2 = pda_prefix.proses(s)[0]
        ok = (r1 == pf) and (r2 == pr)
        gagal += 0 if ok else 1
        print(f"{'OK  ' if ok else 'GAGAL'} '{s}': postfix={r1} prefix={r2}")

    # uji acak: PDA harus selalu sama dengan pembanding counter
    random.seed(1)
    alfabet = "abc+*-"
    beda = 0
    for _ in range(3000):
        s = "".join(random.choice(alfabet) for _ in range(random.randint(1, 9)))
        if pda_postfix.proses(s)[0] != cek_postfix_counter(s):
            beda += 1
        if pda_prefix.proses(s)[0] != cek_prefix_counter(s):
            beda += 1
    print(f"\nUji acak 3000 string: {beda} perbedaan dengan pembanding")
    print("SEMUA TES LULUS" if gagal == 0 and beda == 0 else "ADA TES GAGAL")


# ---------------------------------------------------------------------------
# PEMBUAT DESAIN AUTOMATA
# Semua informasi dibaca langsung dari tabel delta di atas, jadi desain yang
# dicetak SELALU sama dengan automata yang benar-benar dijalankan program.
# ---------------------------------------------------------------------------
NAMA_INPUT = {"a": "operan", "o": "operator", "": "ε"}


def _push_teks(push):
    return " ".join(push) if push else "ε"


def daftar_transisi(pda):
    """Ubah delta menjadi baris: (dari, input, top, pengganti, ke)."""
    baris = []
    for (dari, inp, top), tujuan in pda.delta.items():
        for (ke, push) in tujuan:
            baris.append((dari, NAMA_INPUT[inp], top, _push_teks(push), ke))
    return baris


def daftar_state(pda):
    urut = [pda.start]
    for (dari, _, _, _, ke) in daftar_transisi(pda):
        for q in (dari, ke):
            if q not in urut:
                urut.append(q)
    return urut


def cetak_desain(pda):
    garis = "=" * 64
    transisi = daftar_transisi(pda)
    state = daftar_state(pda)
    simbol_stack = []
    for (_, _, top, peng, _) in transisi:
        for s in [top] + peng.split():
            if s != "ε" and s not in simbol_stack:
                simbol_stack.append(s)

    print(f"\n{garis}\nDESAIN PDA {pda.nama.upper()}\n{garis}")

    print("\n1. Definisi formal  M = (Q, Σ, Γ, δ, q0, Z, F)")
    print(f"   Q  = {{{', '.join(state)}}}")
    print("   Σ  = {operan, operator}")
    print(f"   Γ  = {{{', '.join(simbol_stack)}}}")
    print("   δ  = lihat tabel transisi di bawah")
    print(f"   q0 = {pda.start}")
    print(f"   Z  = {pda.stack_awal}   (simbol dasar stack)")
    print(f"   F  = {{{pda.final}}}")

    print("\n2. Tabel transisi δ")
    kepala = ("No", "Dari", "Input", "Top", "Pengganti", "Ke")
    isi = [(str(i),) + b for i, b in enumerate(transisi, 1)]
    lebar = [max(len(r[k]) for r in [kepala] + isi) for k in range(6)]
    cetak = lambda r: print("   " + " | ".join(r[k].ljust(lebar[k]) for k in range(6)))
    cetak(kepala)
    print("   " + "-+-".join("-" * w for w in lebar))
    for r in isi:
        cetak(r)

    print("\n3. Diagram state  (label: input, top / pengganti)")
    print(f"   --> ({pda.start})   <- state awal;  (({pda.final})) = state akhir\n")
    for q in state:
        keluar = [b for b in transisi if b[0] == q]
        if not keluar:
            continue
        for (_, inp, top, peng, ke) in keluar:
            tujuan = f"(({ke}))" if ke == pda.final else f"({ke})"
            print(f"   ({q}) --[{inp}, {top} / {peng}]--> {tujuan}")
    print()


def buat_dot(pda):
    """Teks Graphviz DOT dari PDA (transisi dengan asal-tujuan sama digabung)."""
    kelompok = {}
    for (dari, inp, top, peng, ke) in daftar_transisi(pda):
        kelompok.setdefault((dari, ke), []).append(f"{inp}, {top} / {peng}")
    baris = ["digraph PDA {", "  rankdir=LR;",
             '  node [shape=circle, fontname="Helvetica"];',
             '  edge [fontname="Helvetica"];',
             f"  {pda.final} [shape=doublecircle];",
             "  start [shape=point];", f"  start -> {pda.start};"]
    for (dari, ke), label in kelompok.items():
        baris.append(f'  {dari} -> {ke} [label="' + "\\n".join(label) + '"];')
    baris.append("}")
    return "\n".join(baris) + "\n"


def simpan_dot(pda):
    """Simpan teks Graphviz (.dot) sebagai bonus."""
    nama = f"desain_pda_{pda.nama.lower()}.dot"
    with open(nama, "w", encoding="utf-8") as f:
        f.write(buat_dot(pda))
    return nama


# ---------------------------------------------------------------------------
# CARA KERJA (teks penjelasan, dipakai di terminal dan di gambar PNG)
# ---------------------------------------------------------------------------
CARA_KERJA = {
    "Postfix": [
        "Ide: stack menyimpan X untuk setiap nilai yang sudah ada.",
        "1. Baca operan: push X (tetap di q0).",
        "2. Baca operator: pop X pertama (q0 ke q1), cek X kedua lalu "
        "gantikan dengan satu X hasil (q1 ke q0). Jika X tidak ada, "
        "PDA macet dan string ditolak.",
        "3. Input habis: pop X terakhir (q0 ke q2). Jika dasar stack Z "
        "terlihat, berarti tadinya tepat satu X, maka PDA pindah ke qf "
        "dan string diterima.",
        "Contoh abc*+: stack tumbuh X, XX, XXX; operator * jadi XX; "
        "operator + jadi X; diterima.",
    ],
    "Prefix": [
        "Ide: stack menyimpan E untuk setiap ekspresi yang masih dibutuhkan.",
        "1. Awal: push E (butuh satu ekspresi), pindah ke q1.",
        "2. Baca operator: ganti satu E dengan dua E, karena operator "
        "butuh dua ekspresi lagi.",
        "3. Baca operan: pop satu E, karena satu kebutuhan terpenuhi. "
        "Jika E sudah habis tapi input masih ada, PDA macet dan ditolak.",
        "4. Input habis dan dasar stack Z terlihat: pindah ke qf, diterima.",
        "Contoh +a*bc: E, EE, E, EE, E, lalu kosong; diterima.",
    ],
}

# posisi state di gambar (x, y)
POSISI = {
    "Postfix": {"q0": (0.0, 0.0), "q1": (3.6, 1.7), "q2": (3.6, -1.7), "qf": (7.2, -1.7)},
    "Prefix": {"q0": (0.0, 0.0), "q1": (3.6, 0.0), "qf": (7.2, 0.0)},
}


def cetak_cara_kerja(pda):
    import textwrap
    print("\n4. Cara kerja")
    for baris in CARA_KERJA[pda.nama]:
        for k, bagian in enumerate(textwrap.wrap(baris, 70)):
            print(("   " if k == 0 else "      ") + bagian)


def pastikan_matplotlib():
    """Ambil matplotlib; jika belum ada, coba pasang otomatis lewat pip."""
    import subprocess
    try:
        import matplotlib
    except ImportError:
        print("\nMatplotlib belum terpasang, mencoba memasang otomatis ...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
            import matplotlib
        except Exception:
            print("Gagal memasang. Pasang manual dengan:  python3 -m pip install matplotlib")
            return None
    matplotlib.use("Agg")
    return matplotlib


WARNA_PAKAI, WARNA_MATI = "#C0392B", "#9AA0A6"


def _gambar_diagram(ax, pda, sorot=None, ujung=None):
    """
    Gambar diagram state.
      sorot : {nomor_transisi: [langkah, ...]} -> transisi yang dipakai ekspresi
              ditandai merah; yang tidak dipakai diabu-abukan. None = tampilan biasa.
      ujung : (state, diterima) -> state tempat PDA berhenti diberi warna.
    """
    import math
    from matplotlib.patches import Circle, FancyArrowPatch

    pos = POSISI[pda.nama]
    r = 0.45
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 1.9, max(xs) + 1.2)
    ax.set_ylim(min(ys) - 1.5, max(ys) + 2.1)
    ax.set_aspect("equal")
    ax.axis("off")

    lingkaran = {}
    for q, (x, y) in pos.items():
        warna_isi = "none"
        if ujung and q == ujung[0]:
            warna_isi = "#D5F5E3" if ujung[1] else "#FADBD8"
        c = Circle((x, y), r, fc=warna_isi, lw=2.2, ec="#222222")
        ax.add_patch(c)
        lingkaran[q] = c
        if q == pda.final:
            ax.add_patch(Circle((x, y), r * 0.8, fill=False, lw=2.2, ec="#222222"))
        ax.text(x, y, q, ha="center", va="center", fontsize=16, color="#222222")

    x0, y0 = pos[pda.start]
    ax.add_patch(FancyArrowPatch((x0 - 1.4, y0), (x0 - r, y0), arrowstyle="-|>",
                                 mutation_scale=18, lw=2, color="#222222"))
    ax.text(x0 - 1.4, y0 + 0.2, "mulai", ha="left", va="bottom", fontsize=11, color="#555555")

    kelompok = {}
    for no, (dari, inp, top, peng, ke) in enumerate(daftar_transisi(pda), 1):
        kelompok.setdefault((dari, ke), []).append((f"{inp}, {top} / {peng}", no))

    def tulis(x, y, baris, mode, ha="center", kotak=False):
        """Tulis label, satu baris satu teks supaya warnanya bisa berbeda-beda."""
        n = len(baris)
        for i, (teks, no) in enumerate(baris):
            if sorot is None:
                warna, tebal = "#1B4F72", "normal"
            elif no in sorot:
                warna, tebal = WARNA_PAKAI, "bold"
                teks += f"   ×{len(sorot[no])}"
            else:
                warna, tebal = WARNA_MATI, "normal"
            if mode == "atas":
                dy, va = (n - 1 - i) * 17, "bottom"
            else:
                dy, va = ((n - 1) / 2 - i) * 17, "center"
            ax.annotate(teks, (x, y), xytext=(0, dy), textcoords="offset points",
                        ha=ha, va=va, fontsize=11.5, color=warna, fontweight=tebal,
                        bbox=(dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9)
                              if kotak else None))

    for (dari, ke), baris in kelompok.items():
        pakai = [no for _, no in baris if sorot and no in sorot]
        if sorot is None:
            warna_garis, tebal = "#222222", 2.0
        elif pakai:
            warna_garis, tebal = WARNA_PAKAI, 3.4
        else:
            warna_garis, tebal = WARNA_MATI, 2.0
        (xa, ya), (xb, yb) = pos[dari], pos[ke]

        if dari == ke:  # loop
            ax.add_patch(FancyArrowPatch((xa - 0.3, ya + r * 0.95), (xa + 0.3, ya + r * 0.95),
                                         connectionstyle="arc3,rad=-1.9", arrowstyle="-|>",
                                         mutation_scale=18, lw=tebal, color=warna_garis))
            # loop di state awal: label digeser ke kiri agar tidak menimpa panah keluar
            if dari == pda.start and any(d == dari and k != dari for (d, k) in kelompok):
                tulis(xa - 0.15, ya + r + 0.75, baris, "atas", ha="right")
            else:
                tulis(xa, ya + r + 0.75, baris, "atas")
            continue

        ada_balik = (ke, dari) in kelompok
        rad = -0.3 if ada_balik else 0.0
        ax.add_patch(FancyArrowPatch((xa, ya), (xb, yb), patchA=lingkaran[dari],
                                     patchB=lingkaran[ke], connectionstyle=f"arc3,rad={rad}",
                                     arrowstyle="-|>", mutation_scale=18, lw=tebal,
                                     color=warna_garis, shrinkA=1, shrinkB=1))
        dx, dy = xb - xa, yb - ya
        panjang = math.hypot(dx, dy)
        mx, my = (xa + xb) / 2 + 0.5 * rad * dy, (ya + yb) / 2 - 0.5 * rad * dx
        if rad:
            nx, ny = (math.copysign(1, rad) * dy / panjang, -math.copysign(1, rad) * dx / panjang)
        else:
            nx, ny = -dy / panjang, dx / panjang
            if ny < -0.01:
                nx, ny = -nx, -ny
        jarak = 0.3 + 0.12 * (len(baris) - 1)
        tulis(mx + nx * jarak, my + ny * jarak, baris, "tengah", kotak=True)


def buat_png(pda, nama_file=None):
    """Buat gambar desain lengkap: diagram state, tabel transisi, cara kerja."""
    import textwrap
    mpl = pastikan_matplotlib()
    if mpl is None:
        return None
    import matplotlib.pyplot as plt

    nama_file = nama_file or f"desain_pda_{pda.nama.lower()}.png"
    fig = plt.figure(figsize=(14, 11), facecolor="white")
    fig.text(0.5, 0.965, f"Desain PDA Notasi {pda.nama}", ha="center", va="center",
             fontsize=24, fontweight="bold", color="#1F2430")
    fig.text(0.5, 0.932, "label transisi: input, top stack / pengganti   "
             "(ε = tanpa input / tanpa isi)", ha="center", va="center",
             fontsize=12, color="#555555")

    ax_d = fig.add_axes([0.03, 0.47, 0.94, 0.44])
    _gambar_diagram(ax_d, pda)

    ax_t = fig.add_axes([0.03, 0.04, 0.54, 0.40])
    ax_t.axis("off")
    ax_t.set_title("Tabel transisi δ", loc="left", fontsize=15, fontweight="bold",
                   color="#1F2430")
    transisi = daftar_transisi(pda)
    isi = [[str(i), *b] for i, b in enumerate(transisi, 1)]
    tabel = ax_t.table(cellText=isi,
                       colLabels=["No", "Dari", "Input", "Top", "Pengganti", "Ke"],
                       colWidths=[0.08, 0.14, 0.26, 0.12, 0.2, 0.12],
                       loc="upper center", cellLoc="center")
    tabel.auto_set_font_size(False)
    tabel.set_fontsize(13)
    tabel.scale(1, 1.9)
    for (baris, kol), sel in tabel.get_celld().items():
        sel.set_edgecolor("#BBBBBB")
        if baris == 0:
            sel.set_facecolor("#1F2430")
            sel.get_text().set_color("white")
            sel.get_text().set_fontweight("bold")

    ax_c = fig.add_axes([0.60, 0.04, 0.37, 0.40])
    ax_c.axis("off")
    ax_c.set_title("Cara kerja", loc="left", fontsize=15, fontweight="bold", color="#1F2430")
    teks, y = [], 0.93
    for baris in CARA_KERJA[pda.nama]:
        bungkus = textwrap.wrap(baris, 46)
        ax_c.text(0.0, y, "\n".join(bungkus), va="top", ha="left", fontsize=11.5,
                  color="#2B2B2B", linespacing=1.4, transform=ax_c.transAxes)
        y -= 0.058 * len(bungkus) + 0.03

    fig.savefig(nama_file, dpi=150, facecolor="white")
    plt.close(fig)
    return nama_file


def buka_gambar(path):
    """Tampilkan gambar dengan aplikasi bawaan sistem."""
    import os
    import subprocess
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        elif sys.platform.startswith("win"):
            os.startfile(path)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception:
        pass


def tampilkan_desain():
    file_png = []
    for pda in (pda_postfix, pda_prefix):
        cetak_desain(pda)
        cetak_cara_kerja(pda)
        simpan_dot(pda)
        png = buat_png(pda)
        if png:
            file_png.append(png)
    if file_png:
        print("\nGambar desain dibuat:", ", ".join(file_png))
        for png in file_png:
            buka_gambar(png)
    else:
        print("\nGambar PNG tidak dibuat. File .dot tetap tersimpan di folder ini.")


# ---------------------------------------------------------------------------
# ANALISIS SATU EKSPRESI: tabel transisi, jejak langkah, cara kerja, dan gambar
# ---------------------------------------------------------------------------
def nomor_transisi(pda, kunci):
    """Nomor baris tabel δ untuk sebuah transisi (dari, input, top, ke, push)."""
    dari, inp, top, ke, push = kunci
    baris = (dari, NAMA_INPUT[inp], top, _push_teks(push), ke)
    return daftar_transisi(pda).index(baris) + 1


def pemakaian(pda, hasil):
    """{nomor transisi: [nomor langkah yang memakainya]}"""
    pakai = {}
    for n, lg in enumerate(hasil["jalur"]):
        if lg["transisi"] is not None:
            pakai.setdefault(nomor_transisi(pda, lg["transisi"]), []).append(n)
    return pakai


def tabel_transisi_ekspresi(pda, hasil):
    """Baris tabel δ ditambah kolom 'dipakai di langkah' untuk ekspresi ini."""
    pakai = pemakaian(pda, hasil)
    isi = []
    for no, b in enumerate(daftar_transisi(pda), 1):
        langkah = ", ".join(str(n) for n in pakai.get(no, [])) or "-"
        if len(langkah) > 16:
            langkah = langkah[:14] + " …"
        isi.append([str(no), *b, langkah])
    return isi


def tabel_langkah(pda, hasil):
    """Baris jejak eksekusi: No, Baca, Transisi, State, Sisa input, Stack."""
    baris = []
    for n, lg in enumerate(hasil["jalur"]):
        sisa = " ".join(hasil["token"][lg["pos"]:]) or "(habis)"
        stack = " ".join(lg["stack"]) or "(kosong)"
        if lg["transisi"] is None:
            baris.append([str(n), "(awal)", "-", lg["state"], sisa, stack])
        else:
            baca = lg["baca"] if lg["baca"] is not None else "ε"
            baris.append([str(n), baca, f"δ{nomor_transisi(pda, lg['transisi'])}",
                          lg["state"], sisa, stack])
    return baris


def penjelasan_langkah(pda, hasil):
    """Cara kerja untuk ekspresi ini, satu kalimat per langkah."""
    kalimat = []
    for n, lg in enumerate(hasil["jalur"]):
        if lg["transisi"] is None:
            continue
        dari, inp, top, ke, push = lg["transisi"]
        no = nomor_transisi(pda, lg["transisi"])
        if lg["baca"] is not None:
            baca = f"baca '{lg['baca']}' ({NAMA_INPUT[inp]})"
        else:
            baca = "tanpa membaca input (ε)"
        if not push:
            aksi = f"hapus {top} dari stack"
        elif tuple(push) == (top,):
            aksi = f"top stack {top} dicek lalu dikembalikan"
        else:
            aksi = f"ganti {top} dengan {' '.join(push)}"
        stack = " ".join(lg["stack"]) or "kosong"
        kalimat.append(f"Langkah {n} (δ{no}): {baca}; di {dari} top={top}, {aksi}, "
                       f"pindah ke {ke}. Stack: {stack}")
    return kalimat


def _cetak_tabel(kepala, isi, indent="   "):
    lebar = [max(len(r[k]) for r in [kepala] + isi) for k in range(len(kepala))]
    cetak = lambda r: print(indent + " | ".join(r[k].ljust(lebar[k]) for k in range(len(kepala))))
    cetak(kepala)
    print(indent + "-+-".join("-" * w for w in lebar))
    for r in isi:
        cetak(r)


def cetak_analisis(pda, hasil, teks):
    import textwrap
    garis = "=" * 70
    print(f"\n{garis}\nPDA {pda.nama.upper()}  |  ekspresi: {teks}\n{garis}")

    print("\nTabel transisi δ (kolom terakhir: dipakai di langkah ke-berapa)")
    _cetak_tabel(["No", "Dari", "Input", "Top", "Pengganti", "Ke", "Dipakai"],
                 tabel_transisi_ekspresi(pda, hasil))

    print("\nJejak eksekusi")
    _cetak_tabel(["No", "Baca", "Transisi", "State", "Sisa input", "Stack (top ke bawah)"],
                 tabel_langkah(pda, hasil))

    print("\nCara kerja untuk ekspresi ini")
    print("   " + CARA_KERJA[pda.nama][0])
    for k in penjelasan_langkah(pda, hasil):
        for i, bagian in enumerate(textwrap.wrap(k, 74)):
            print(("   - " if i == 0 else "     ") + bagian)

    if hasil["ok"]:
        print(f"\nHasil: DITERIMA. Input habis di {pda.final} dan stack tinggal {pda.stack_awal}.")
    else:
        print(f"\nHasil: DITOLAK. {hasil['alasan']}.")


def buat_png_ekspresi(pda, hasil, teks, nama_file):
    """Gambar lengkap untuk satu ekspresi: diagram (jalur ditandai), tabel, jejak."""
    import textwrap
    mpl = pastikan_matplotlib()
    if mpl is None:
        return None
    import matplotlib.pyplot as plt

    ok = hasil["ok"]
    warna_hasil = "#1E8449" if ok else "#C0392B"
    isi_tabel = tabel_transisi_ekspresi(pda, hasil)
    isi_jejak = tabel_langkah(pda, hasil)
    pakai = pemakaian(pda, hasil)

    T, D, M = 1.4, 5.0, 4.5
    B = 0.4 * (len(isi_jejak) + 1) + 0.8
    W, H = 15, T + D + M + B
    fy = lambda atas, tinggi: (H - atas - tinggi) / H
    fig = plt.figure(figsize=(W, H), facecolor="white")

    fig.text(0.5, 1 - 0.38 / H, f"PDA {pda.nama}   |   ekspresi: {teks}", ha="center",
             va="center", fontsize=22, fontweight="bold", color="#1F2430")
    status = "DITERIMA" if ok else "DITOLAK: " + hasil["alasan"]
    fig.text(0.5, 1 - 0.88 / H, "\n".join(textwrap.wrap(status, 120)), ha="center",
             va="center", fontsize=14, fontweight="bold", color=warna_hasil)

    # diagram dengan jalur ekspresi ditandai
    ax_d = fig.add_axes([0.03, fy(T, D), 0.94, D / H])
    _gambar_diagram(ax_d, pda, sorot=pakai, ujung=(hasil["jalur"][-1]["state"], ok))
    fig.text(0.97, fy(T, D) + (D - 0.1) / H,
             "merah = transisi yang dipakai ekspresi ini (×N = berapa kali dipakai)",
             ha="right", va="top", fontsize=11, color="#555555")

    # tabel transisi
    ax_t = fig.add_axes([0.03, fy(T + D, M - 0.3), 0.58, (M - 0.3) / H])
    ax_t.axis("off")
    ax_t.set_title("Tabel transisi δ", loc="left", fontsize=15, fontweight="bold", color="#1F2430")
    tabel = ax_t.table(cellText=isi_tabel,
                       colLabels=["No", "Dari", "Input", "Top", "Pengganti", "Ke", "Dipakai"],
                       colWidths=[0.07, 0.1, 0.18, 0.08, 0.16, 0.08, 0.2],
                       loc="upper center", cellLoc="center")
    tabel.auto_set_font_size(False)
    tabel.set_fontsize(12.5)
    tabel.scale(1, 1.8)
    for (baris, kol), sel in tabel.get_celld().items():
        sel.set_edgecolor("#BBBBBB")
        if baris == 0:
            sel.set_facecolor("#1F2430")
            sel.get_text().set_color("white")
            sel.get_text().set_fontweight("bold")
        elif isi_tabel[baris - 1][-1] != "-":
            sel.set_facecolor("#FDEDEC")

    # cara kerja umum
    ax_c = fig.add_axes([0.64, fy(T + D, M - 0.3), 0.34, (M - 0.3) / H])
    ax_c.axis("off")
    ax_c.set_title("Cara kerja", loc="left", fontsize=15, fontweight="bold", color="#1F2430")
    paragraf = ["\n".join(textwrap.wrap(b, 50)) for b in CARA_KERJA[pda.nama]]
    ax_c.text(0.0, 0.97, "\n\n".join(paragraf), va="top", ha="left", fontsize=10.5,
              color="#2B2B2B", linespacing=1.35, transform=ax_c.transAxes)

    # jejak eksekusi
    fig.text(0.03, 1 - (T + D + M + 0.15) / H, "Jejak eksekusi", ha="left", va="center",
             fontsize=15, fontweight="bold", color="#1F2430")
    tinggi_jejak = 0.4 * (len(isi_jejak) + 1)
    ax_b = fig.add_axes([0.03, fy(T + D + M + 0.4, tinggi_jejak), 0.94, tinggi_jejak / H])
    ax_b.axis("off")
    jejak = ax_b.table(cellText=isi_jejak,
                       colLabels=["No", "Baca", "Transisi", "State", "Sisa input",
                                  "Stack (top ke bawah)"],
                       colWidths=[0.06, 0.1, 0.1, 0.1, 0.32, 0.32],
                       cellLoc="center", bbox=[0, 0, 1, 1])
    jejak.auto_set_font_size(False)
    jejak.set_fontsize(12)
    for (baris, kol), sel in jejak.get_celld().items():
        sel.set_edgecolor("#BBBBBB")
        if baris == 0:
            sel.set_facecolor("#1F2430")
            sel.get_text().set_color("white")
            sel.get_text().set_fontweight("bold")
        elif baris == len(isi_jejak):
            sel.set_facecolor("#D5F5E3" if ok else "#FADBD8")

    fig.savefig(nama_file, dpi=130, facecolor="white")
    plt.close(fig)
    return nama_file


def analisis_ekspresi(teks, nomor=1):
    """Uji satu ekspresi ke kedua PDA, cetak penjelasan, dan buat gambar."""
    semua = [(pda, pda.jalankan(teks)) for pda in (pda_postfix, pda_prefix)]

    print(f"\nEkspresi: {teks}")
    print(f"Token   : {' '.join(semua[0][1]['token']) or '-'}")
    for pda, h in semua:
        print(f"  {pda.nama:<8}: " + ("DITERIMA" if h["ok"] else f"ditolak ({h['alasan']})"))

    if not semua[0][1]["token"] or not semua[0][1]["jalur"]:
        print("\nTidak ada yang bisa digambar untuk input ini.")
        return

    diterima = [(p, h) for p, h in semua if h["ok"]]
    if diterima:
        print(f"\n-> Ekspresi ini adalah notasi {' & '.join(p.nama for p, _ in diterima)}.")
    else:
        print("\n-> Ekspresi ini BUKAN Postfix dan BUKAN Prefix (mungkin Infix atau salah tulis).")
        print("   Berikut jejak PDA sampai titik macetnya.")

    gambar = []
    for pda, h in (diterima or semua):
        cetak_analisis(pda, h, teks)
        png = buat_png_ekspresi(pda, h, teks, f"hasil_{nomor}_{pda.nama.lower()}.png")
        if png:
            gambar.append(png)
    if gambar:
        print("\nGambar dibuat:", ", ".join(gambar))
        for g in gambar:
            buka_gambar(g)
    else:
        print("\nGambar PNG tidak dibuat (matplotlib tidak tersedia).")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "tes":
        jalankan_tes()
        return
    if len(sys.argv) > 1 and sys.argv[1] == "desain":
        tampilkan_desain()
        return
    if len(sys.argv) > 1:  # ekspresi langsung dari argumen (beri tanda kutip)
        analisis_ekspresi(" ".join(sys.argv[1:]))
        return

    print("Pengenal notasi Postfix & Prefix (PDA)")
    print("Ketik ekspresi, lalu program menampilkan tabel transisi, jejak langkah,")
    print("cara kerja, dan gambar desain PDA untuk ekspresi itu.")
    print("Operan: huruf/angka. Operator: + - * / ^")
    print("Pisahkan dengan spasi bila operan lebih dari satu karakter, contoh: 8 5 + 10 3 * -")
    print("Perintah lain: 'desain' = desain umum kedua PDA, 'keluar' = berhenti.")
    nomor = 0
    while True:
        teks = input("\nMasukkan ekspresi: ")
        if teks.strip().lower() == "keluar":
            break
        if teks.strip().lower() == "desain":
            tampilkan_desain()
            continue
        if not teks.strip():
            continue
        nomor += 1
        analisis_ekspresi(teks, nomor)


if __name__ == "__main__":
    main()