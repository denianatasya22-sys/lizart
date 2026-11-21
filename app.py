import os
import uuid
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

# =========================================================
# KONFIGURASI
# =========================================================
NAMA_ARTIS = "Lizard"
KONTAK_ARTIS = "lizart.commisart"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Lizart2026!")  # ganti!

LOGO = "logo.jpeg"

FILE_PESANAN = "pesanan.csv"
FOLDER_REFERENSI = "referensi"
FOLDER_PORTOFOLIO = "portofolio"

os.makedirs(FOLDER_REFERENSI, exist_ok=True)
os.makedirs(FOLDER_PORTOFOLIO, exist_ok=True)

# Harga dasar (Rupiah) per gaya dan jenis badan
HARGA_DASAR = {
    "Sketsa": {"Headshot": 10000, "Half Body": 30000, "Full Body": 70000},
    "Lineart": {"Headshot": 35000, "Half Body": 45000, "Full Body": 90000},
    "Flat Color": {"Headshot": 80000, "Half Body": 13000, "Full Body": 19000},
    "Full Render": {"Headshot": 150000, "Half Body": 180000, "Full Body": 300000},
}
HARGA_BACKGROUND = {
    "Tanpa background": 0, 
    "Warna polos / gradasi": 20000,
    "Background simpel": 50000,
    "Background detail": 100000,
}
TAMBAHAN_KARAKTER = 0.8
BIAYA_KOMERSIAL = 0.5
BIAYA_PRIORITAS = 0.25 
BIAYA_REVISI_EXTRA = 15000

DAFTAR_STATUS = [
    "Menunggu Konfirmasi",
    "Diterima",
    "Sedang Dikerjakan",
    "Revisi",
    "Selesai",
    "Dibatalkan",
]

KOLOM = [
    "id", "waktu", "nama", "kontak", "gaya", "jenis", "jumlah_karakter",
    "background", "komersial", "prioritas", "revisi_extra", "deadline",
    "deskripsi", "file_referensi", "total_harga", "status",
]


# =========================================================
# FUNGSI BANTU
# =========================================================
def rupiah(angka):
    return "Rp {:,.0f}".format(angka).replace(",", ".")


def hitung_harga(gaya, jenis, jumlah, background, komersial, prioritas, revisi_extra):
    dasar = HARGA_DASAR[gaya][jenis]
    harga = dasar + (jumlah - 1) * dasar * TAMBAHAN_KARAKTER
    harga += HARGA_BACKGROUND[background]
    if komersial:
        harga += harga * BIAYA_KOMERSIAL
    if prioritas:
        harga += harga * BIAYA_PRIORITAS
    harga += revisi_extra * BIAYA_REVISI_EXTRA
    return int(round(harga, -2))  # dibulatkan ke ratusan


def muat_pesanan():
    if os.path.exists(FILE_PESANAN):
        return pd.read_csv(FILE_PESANAN, dtype=str).fillna("")
    return pd.DataFrame(columns=KOLOM)


def simpan_pesanan(df):
    df.to_csv(FILE_PESANAN, index=False)


def buat_id():
    return "CM-" + datetime.now().strftime("%y%m%d") + "-" + uuid.uuid4().hex[:4].upper()


def simpan_referensi(id_pesanan, files):
    nama_tersimpan = []
    for f in files:
        nama_aman = os.path.basename(f.name)
        path = os.path.join(FOLDER_REFERENSI, f"{id_pesanan}_{nama_aman}")
        with open(path, "wb") as out:
            out.write(f.getbuffer())
        nama_tersimpan.append(os.path.basename(path))
    return "; ".join(nama_tersimpan)


def tampilkan_logo_header():
    """Menampilkan logo di tengah halaman (jika file logo ada)."""
    if os.path.exists(LOGO):
        _, tengah, _ = st.columns([1, 1, 1])
        tengah.image(LOGO, use_container_width=True)


# =========================================================
# HALAMAN
# =========================================================
def halaman_beranda():
    tampilkan_logo_header()
    st.title(f"🎨 Commission Gambar by {NAMA_ARTIS}")
    st.write(
        "Selamat datang! Di sini kamu bisa memesan gambar custom: "
        "karakter OC, fanart, potret, dan lainnya."
    )

    st.subheader("Contoh Karya")
    gambar = [
        os.path.join(FOLDER_PORTOFOLIO, f)
        for f in sorted(os.listdir(FOLDER_PORTOFOLIO))
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]
    if gambar:
        kolom = st.columns(3)
        for i, path in enumerate(gambar):
            kolom[i % 3].image(path, use_container_width=True)
    else:
        st.info(
            f"Belum ada contoh karya. Taruh gambar (.png/.jpg) ke folder "
            f"'{FOLDER_PORTOFOLIO}' dan akan tampil di sini."
        )

    st.subheader("Alur Pemesanan")
    st.markdown(
        """
1. Isi form di halaman **Pesan Commission**
2. Simpan **ID Pesanan** yang muncul setelah mengirim
3. Artis mengonfirmasi pesanan lewat kontak yang kamu berikan
4. Pembayaran (DP / lunas) sesuai kesepakatan
5. Gambar dikerjakan, kamu bisa cek status di halaman **Cek Status**
6. Revisi (jika perlu) lalu file final dikirim
        """
    )
    st.caption(f"Kontak artis: {KONTAK_ARTIS}")


def halaman_harga():
    st.title("💰 Daftar Harga")
    baris = []
    for gaya, jenis_dict in HARGA_DASAR.items():
        row = {"Gaya": gaya}
        for jenis, harga in jenis_dict.items():
            row[jenis] = rupiah(harga)
        baris.append(row)
    st.table(pd.DataFrame(baris).set_index("Gaya"))

    st.subheader("Tambahan")
    st.markdown(
        f"""
- Karakter ke-2 dan seterusnya: **{int(TAMBAHAN_KARAKTER * 100)}%** dari harga dasar
- Background: {", ".join(f"{k} ({rupiah(v)})" for k, v in HARGA_BACKGROUND.items() if v)}
- Lisensi komersial: **+{int(BIAYA_KOMERSIAL * 100)}%**
- Pengerjaan prioritas: **+{int(BIAYA_PRIORITAS * 100)}%**
- Revisi tambahan: **{rupiah(BIAYA_REVISI_EXTRA)}** per revisi (gratis 2x revisi kecil)
        """
    )


def halaman_pesan():
    st.title("📝 Pesan Commission")

    st.subheader("1. Data Pemesan")
    nama = st.text_input("Nama")
    kontak = st.text_input("Kontak (Instagram / WhatsApp / Email)")

    st.subheader("2. Detail Gambar")
    c1, c2 = st.columns(2)
    gaya = c1.selectbox("Gaya gambar", list(HARGA_DASAR.keys()))
    jenis = c2.selectbox("Jenis", ["Headshot", "Half Body", "Full Body"])
    jumlah = c1.number_input("Jumlah karakter", min_value=1, max_value=5, value=1, step=1)
    background = c2.selectbox("Background", list(HARGA_BACKGROUND.keys()))
    deskripsi = st.text_area(
        "Deskripsi gambar",
        placeholder="Ceritakan karakter, pose, ekspresi, warna, suasana, dll.",
        height=150,
    )
    referensi = st.file_uploader(
        "Upload gambar referensi (opsional)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

    st.subheader("3. Opsi Tambahan")
    komersial = st.checkbox(f"Penggunaan komersial (+{int(BIAYA_KOMERSIAL * 100)}%)")
    prioritas = st.checkbox(f"Pengerjaan prioritas (+{int(BIAYA_PRIORITAS * 100)}%)")
    revisi_extra = st.number_input(
        f"Revisi tambahan ({rupiah(BIAYA_REVISI_EXTRA)}/revisi)",
        min_value=0, max_value=5, value=0, step=1,
    )
    deadline = st.date_input(
        "Deadline yang diinginkan",
        value=date.today() + timedelta(days=14),
        min_value=date.today() + timedelta(days=3),
    )

    total = hitung_harga(gaya, jenis, int(jumlah), background, komersial, prioritas, int(revisi_extra))
    st.divider()
    st.metric("Estimasi Total Harga", rupiah(total))

    setuju = st.checkbox(
        "Saya setuju dengan ketentuan: harga final dikonfirmasi artis, "
        "gambar tidak boleh diklaim sebagai buatan sendiri, dan hak cipta tetap pada artis."
    )

    if st.button("Kirim Pesanan", type="primary"):
        if not nama.strip() or not kontak.strip():
            st.error("Nama dan kontak wajib diisi.")
        elif not deskripsi.strip():
            st.error("Deskripsi gambar wajib diisi.")
        elif not setuju:
            st.error("Kamu harus menyetujui ketentuan terlebih dahulu.")
        else:
            id_pesanan = buat_id()
            nama_file = simpan_referensi(id_pesanan, referensi) if referensi else ""
            baru = {
                "id": id_pesanan,
                "waktu": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "nama": nama.strip(),
                "kontak": kontak.strip(),
                "gaya": gaya,
                "jenis": jenis,
                "jumlah_karakter": str(int(jumlah)),
                "background": background,
                "komersial": "Ya" if komersial else "Tidak",
                "prioritas": "Ya" if prioritas else "Tidak",
                "revisi_extra": str(int(revisi_extra)),
                "deadline": str(deadline),
                "deskripsi": deskripsi.strip(),
                "file_referensi": nama_file,
                "total_harga": str(total),
                "status": "Menunggu Konfirmasi",
            }
            df = muat_pesanan()
            df = pd.concat([df, pd.DataFrame([baru])], ignore_index=True)
            simpan_pesanan(df)

            st.success("Pesanan berhasil dikirim! 🎉")
            st.info(f"**ID Pesanan kamu: {id_pesanan}**  \nSimpan ID ini untuk cek status pesanan.")
            st.balloons()


def halaman_cek_status():
    st.title("🔎 Cek Status Pesanan")
    id_input = st.text_input("Masukkan ID Pesanan", placeholder="CM-241119-AB12")

    if st.button("Cek"):
        df = muat_pesanan()
        hasil = df[df["id"].str.upper() == id_input.strip().upper()]
        if hasil.empty:
            st.error("ID pesanan tidak ditemukan.")
        else:
            p = hasil.iloc[0]
            st.success(f"Status: **{p['status']}**")
            st.write(f"**Pemesan:** {p['nama']}")
            st.write(f"**Pesanan:** {p['gaya']} - {p['jenis']} ({p['jumlah_karakter']} karakter)")
            st.write(f"**Deadline:** {p['deadline']}")
            st.write(f"**Total harga:** {rupiah(int(p['total_harga']))}")


def halaman_admin():
    st.title("🔒 Dashboard Artis")
    password = st.text_input("Password admin", type="password")
    if password != ADMIN_PASSWORD:
        if password:
            st.error("Password salah.")
        return

    df = muat_pesanan()
    if df.empty:
        st.info("Belum ada pesanan masuk.")
        return

    total_pendapatan = df[df["status"] == "Selesai"]["total_harga"].astype(int).sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total pesanan", len(df))
    c2.metric("Perlu diproses", int((df["status"] == "Menunggu Konfirmasi").sum()))
    c3.metric("Pendapatan (selesai)", rupiah(total_pendapatan))

    filter_status = st.multiselect("Filter status", DAFTAR_STATUS, default=DAFTAR_STATUS)
    tampil = df[df["status"].isin(filter_status)]
    st.dataframe(tampil, use_container_width=True)

    st.subheader("Update Status Pesanan")
    id_pilih = st.selectbox("Pilih pesanan", df["id"].tolist())
    baris = df[df["id"] == id_pilih].iloc[0]
    st.write(f"**{baris['nama']}** | {baris['kontak']}")
    st.write(baris["deskripsi"])

    if baris["file_referensi"]:
        for nama_file in baris["file_referensi"].split("; "):
            path = os.path.join(FOLDER_REFERENSI, nama_file)
            if os.path.exists(path):
                st.image(path, caption=nama_file, width=250)

    status_baru = st.selectbox(
        "Status baru", DAFTAR_STATUS, index=DAFTAR_STATUS.index(baris["status"])
    )
    if st.button("Simpan Status"):
        df.loc[df["id"] == id_pilih, "status"] = status_baru
        simpan_pesanan(df)
        st.success("Status diperbarui.")
        st.rerun()

    st.download_button(
        "Download semua pesanan (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        file_name="pesanan.csv",
        mime="text/csv",
    )


# =========================================================
# APLIKASI UTAMA
# =========================================================
# page_icon = ikon di tab browser (pakai logo jika ada)
st.set_page_config(
    page_title="Commission Gambar",
    page_icon=LOGO if os.path.exists(LOGO) else "🎨",
    layout="centered",
)

# Logo di pojok atas sidebar
if os.path.exists(LOGO):
    st.logo(LOGO)

menu = st.sidebar.radio(
    "Menu",
    ["Beranda", "Daftar Harga", "Pesan Commission", "Cek Status", "Admin"],
)

if menu == "Beranda":
    halaman_beranda()
elif menu == "Daftar Harga":
    halaman_harga()
elif menu == "Pesan Commission":
    halaman_pesan()
elif menu == "Cek Status":
    halaman_cek_status()
else:
    halaman_admin()
