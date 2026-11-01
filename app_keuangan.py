import flet as ft
import requests
import os
from datetime import datetime

# URL rahasia penghubung ke Google Sheets Anda
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbzx9ZBYqf7iY4TPXj_r4f42Rf-rzVdXZrnwHBES1lAgwavoxdVT948-GIcysQ2mZhd8Cg/exec"

def main(page: ft.Page):
    page.title = "Keuangan Keluarga Cloud"
    page.window.width = 400
    page.window.height = 750
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # 1. Komponen Input
    hari_ini = datetime.now().strftime("%Y-%m-%d")
    input_tanggal = ft.TextField(label="Tanggal (YYYY-MM-DD)", value=hari_ini, width=300)
    input_keterangan = ft.TextField(label="Keterangan (misal: Gaji, Beras)", width=300)
    input_nominal = ft.TextField(label="Nominal (Angka Saja)", width=300, keyboard_type=ft.KeyboardType.NUMBER)
    dropdown_tipe = ft.Dropdown(
        label="Tipe Transaksi", width=300,
        options=[ft.dropdown.Option("Pemasukan"), ft.dropdown.Option("Pengeluaran")]
    )
    pesan_notifikasi = ft.Text(value="", size=14)

    # 2. Komponen Laporan
    dropdown_bulan = ft.Dropdown(label="Pilih Bulan Laporan", width=300)
    teks_laporan = ft.Text(value="Klik tombol di bawah untuk menarik data dari Google Sheets.", size=14, weight=ft.FontWeight.W_500)

    # 3. Fungsi Menyimpan Data (Kirim POST ke Cloud)
    def simpan_data(e):
        if not input_tanggal.value or not input_keterangan.value or not input_nominal.value or not dropdown_tipe.value:
            pesan_notifikasi.value = "Mohon isi semua kolom!"
            pesan_notifikasi.color = ft.colors.RED
            page.update()
            return
        
        pesan_notifikasi.value = "Mengirim data ke Google Sheets..."
        pesan_notifikasi.color = ft.colors.ORANGE_700
        page.update()

        data_kirim = {
            "tanggal": input_tanggal.value,
            "tipe": dropdown_tipe.value,
            "keterangan": input_keterangan.value,
            "nominal": input_nominal.value
        }

        try:
            response = requests.post(URL_APPS_SCRIPT, json=data_kirim)
            if response.status_code == 200:
                pesan_notifikasi.value = f"Berhasil disimpan: {input_keterangan.value}"
                pesan_notifikasi.color = ft.colors.GREEN
                input_keterangan.value = ""
                input_nominal.value = ""
                dropdown_tipe.value = None
            else:
                pesan_notifikasi.value = "Gagal terhubung ke server."
                pesan_notifikasi.color = ft.colors.RED
        except Exception as ex:
            pesan_notifikasi.value = "Error koneksi internet!"
            pesan_notifikasi.color = ft.colors.RED
        
        page.update()

    # 4. Fungsi Mengambil Data & Menghitung (Ambil GET dari Cloud)
    def tarik_dan_hitung(e):
        pesan_notifikasi.value = "Membaca data dari Google Sheets..."
        pesan_notifikasi.color = ft.colors.ORANGE_700
        page.update()

        try:
            response = requests.get(URL_APPS_SCRIPT)
            if response.status_code == 200:
                data_sheets = response.json()
                
                bulan_unik = set()
                for i, row in enumerate(data_sheets):
                    if i == 0: continue
                    if len(row) > 0:
                        tgl_str = str(row[0])[:7] 
                        if len(tgl_str) == 7:
                            bulan_unik.add(tgl_str)
                
                daftar_bulan = sorted(list(bulan_unik), reverse=True)
                if not daftar_bulan:
                    daftar_bulan = [datetime.now().strftime("%Y-%m")]
                
                dropdown_bulan.options = [ft.dropdown.Option(b) for b in daftar_bulan]
                
                bulan_terpilih = dropdown_bulan.value
                if not bulan_terpilih:
                    bulan_terpilih = datetime.now().strftime("%Y-%m")
                    if bulan_terpilih in daftar_bulan:
                        dropdown_bulan.value = bulan_terpilih
                    elif daftar_bulan:
                        dropdown_bulan.value = daftar_bulan[0]
                        bulan_terpilih = daftar_bulan[0]

                pemasukan = 0
                pengeluaran = 0
                
                for i, row in enumerate(data_sheets):
                    if i == 0: continue
                    if len(row) >= 4:
                        tgl = str(row[0])
                        if tgl.startswith(bulan_terpilih):
                            try:
                                nom = int(row[3])
                                if row[1] == "Pemasukan":
                                    pemasukan += nom
                                elif row[1] == "Pengeluaran":
                                    pengeluaran += nom
                            except ValueError:
                                continue
                
                selisih = pemasukan - pengeluaran
                teks_laporan.value = (
                    f"📊 Rekap Periode: {bulan_terpilih}\n\n"
                    f"🟢 Total Pemasukan : Rp {pemasukan:,}\n\n"
                    f"🔴 Total Pengeluaran : Rp {pengeluaran:,}\n\n"
                    f"💰 Sisa / Selisih : Rp {selisih:,}"
                )
                pesan_notifikasi.value = "Data berhasil disinkronisasi."
                pesan_notifikasi.color = ft.colors.GREEN
            else:
                pesan_notifikasi.value = "Gagal memuat data dari server."
                pesan_notifikasi.color = ft.colors.RED

        except Exception as ex:
            pesan_notifikasi.value = "Error koneksi internet!"
            pesan_notifikasi.color = ft.colors.RED
        
        page.update()

    # 5. Susunan Tombol
    tombol_simpan = ft.ElevatedButton(text="Simpan Data (Cloud)", on_click=simpan_data, width=300, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)
    tombol_laporan = ft.ElevatedButton(text="Sinkronisasi & Hitung", on_click=tarik_dan_hitung, width=300, bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)

    page.add(
        ft.Column(
            controls=[
                ft.Text("Pencatat Keuangan", size=24, weight=ft.FontWeight.BOLD),
                input_tanggal,
                input_keterangan, 
                input_nominal, 
                dropdown_tipe, 
                tombol_simpan, 
                pesan_notifikasi,
                ft.Divider(height=40, color=ft.colors.GREY_300),
                ft.Text("Ringkasan Kas", size=20, weight=ft.FontWeight.BOLD),
                dropdown_bulan, 
                teks_laporan, 
                tombol_laporan
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

port = int(os.environ.get("PORT", 8550))
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")