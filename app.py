import streamlit as st
import pandas as pd
import os
from datetime import datetime
from fpdf import FPDF

# --- KONFIGURASI FILE PENYIMPANAN ---
FILE_STOK = 'stok_bengkel.csv'
FILE_TRANSAKSI = 'transaksi_bengkel.csv'

# --- FUNGSI LOAD & SAVE DATA ---
def load_data(filename, columns):
    if not os.path.exists(filename):
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(filename)
    except:
        return pd.DataFrame(columns=columns)

def save_data(df, filename):
    df.to_csv(filename, index=False)

# --- FUNGSI GENERATE PDF ---
def export_to_pdf(nama, plat, jasa, barang, qty, harga_brg, total):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="NOTA PEMBAYARAN SS GARAGE", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
    pdf.ln(10)
    
    # Informasi Pelanggan
    pdf.set_font("Arial", size=12)
    pdf.cell(100, 10, txt=f"Pelanggan: {nama}")
    pdf.cell(100, 10, txt=f"Plat Nomor: {plat}", ln=True)
    pdf.cell(190, 0, txt="", border="T", ln=True)
    pdf.ln(5)
    
    # Tabel Rincian
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(90, 10, txt="Deskripsi")
    pdf.cell(30, 10, txt="Qty")
    pdf.cell(70, 10, txt="Subtotal", ln=True)
    
    pdf.set_font("Arial", size=12)
    # Baris Jasa
    pdf.cell(90, 10, txt="Jasa Servis Mekanik")
    pdf.cell(30, 10, txt="-")
    pdf.cell(70, 10, txt=f"Rp {jasa:,}", ln=True)
    
    # Baris Barang (Jika ada)
    if barang != "-" and barang != "- Tidak Ada -":
        pdf.cell(90, 10, txt=f"Sparepart: {barang}")
        pdf.cell(30, 10, txt=f"{qty}")
        pdf.cell(70, 10, txt=f"Rp {harga_brg:,}", ln=True)
    
    pdf.ln(5)
    pdf.cell(190, 0, txt="", border="T", ln=True)
    
    # Total
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(120, 10, txt="TOTAL PEMBAYARAN", align='R')
    pdf.cell(70, 10, txt=f"Rp {total:,}", ln=True, align='R')
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Terima kasih telah mempercayakan kendaraan Anda di SS Garage.", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- SETUP HALAMAN ---
st.set_page_config(page_title="SS Garage - Sistem Manajemen", layout="wide", page_icon="🔧")
st.title("🔧 Sistem Kasir & Stok SS Garage")

# Load Data Awal
df_stok = load_data(FILE_STOK, ['Nama Barang', 'Harga Jual', 'Stok'])
df_transaksi = load_data(FILE_TRANSAKSI, ['Tanggal', 'Pelanggan', 'Plat Nomor', 'Jasa Servis', 'Barang', 'Qty', 'Total Harga'])

# --- SIDEBAR MENU ---
menu = st.sidebar.selectbox("Menu Utama", ["Kasir (Transaksi)", "Kelola Stok (Gudang)", "Laporan Keuangan"])

# ================= MENU: KASIR =================
if menu == "Kasir (Transaksi)":
    st.header("💰 Kasir Pembayaran")
    col1, col2 = st.columns(2)
    
    with col1:
        pelanggan = st.text_input("Nama Pelanggan")
        plat_nomor = st.text_input("Plat Nomor")
        biaya_jasa = st.number_input("Biaya Jasa Mekanik (Rp)", min_value=0, step=5000)

    with col2:
        if not df_stok.empty:
            list_barang = df_stok['Nama Barang'].tolist()
            pilih_barang = st.selectbox("Pilih Sparepart (Opsional)", ["- Tidak Ada -"] + list_barang)
            
            qty, harga_barang = 0, 0
            if pilih_barang != "- Tidak Ada -":
                data_barang = df_stok[df_stok['Nama Barang'] == pilih_barang].iloc[0]
                stok_tersedia = int(data_barang['Stok'])
                harga_satuan = data_barang['Harga Jual']
                
                if stok_tersedia > 0:
                    st.info(f"Stok: {stok_tersedia} | Harga: Rp {harga_satuan:,}")
                    qty = st.number_input("Jumlah Beli", min_value=1, max_value=stok_tersedia, step=1)
                    harga_barang = harga_satuan * qty
                else:
                    st.error("⚠️ Stok Habis!")
        else:
            st.warning("Stok kosong. Isi di menu Gudang.")
            pilih_barang, harga_barang, qty = "- Tidak Ada -", 0, 0

    total_bayar = biaya_jasa + harga_barang
    st.markdown(f"### Total Tagihan: Rp {total_bayar:,}")

    if st.button("Proses Pembayaran & Cetak"):
        if pelanggan and plat_nomor:
            if pilih_barang != "- Tidak Ada -" and qty == 0:
                st.error("Stok tidak mencukupi.")
            else:
                # 1. Update Stok
                if pilih_barang != "- Tidak Ada -" and qty > 0:
                    idx = df_stok.index[df_stok['Nama Barang'] == pilih_barang].tolist()[0]
                    df_stok.at[idx, 'Stok'] -= qty
                    save_data(df_stok, FILE_STOK)

                # 2. Simpan Transaksi
                waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_row = pd.DataFrame({'Tanggal': [waktu], 'Pelanggan': [pelanggan], 'Plat Nomor': [plat_nomor], 
                                        'Jasa Servis': [biaya_jasa], 'Barang': [pilih_barang], 'Qty': [qty], 'Total Harga': [total_bayar]})
                df_transaksi = pd.concat([df_transaksi, new_row], ignore_index=True)
                save_data(df_transaksi, FILE_TRANSAKSI)

                # 3. Nota PDF
                pdf_bytes = export_to_pdf(pelanggan, plat_nomor, biaya_jasa, pilih_barang, qty, harga_barang, total_bayar)
                st.success("Transaksi Berhasil!")
                st.download_button(label="📄 Download Nota PDF", data=pdf_bytes, file_name=f"Nota_{plat_nomor}.pdf", mime="application/pdf")
        else:
            st.error("Lengkapi data pelanggan!")

# ================= MENU: GUDANG =================
elif menu == "Kelola Stok (Gudang)":
    st.header("📦 Gudang & Stok Barang")
    with st.expander("Tambah Barang Baru"):
        with st.form("tambah_barang"):
            n_baru = st.text_input("Nama Sparepart")
            h_baru = st.number_input("Harga Jual (Rp)", min_value=0, step=1000)
            s_baru = st.number_input("Stok Awal", min_value=1, step=1)
            if st.form_submit_button("Simpan") and n_baru:
                df_stok = pd.concat([df_stok, pd.DataFrame({'Nama Barang':[n_baru], 'Harga Jual':[h_baru], 'Stok':[s_baru]})], ignore_index=True)
                save_data(df_stok, FILE_STOK)
                st.rerun()

    edited_df = st.data_editor(df_stok, num_rows="dynamic")
    if st.button("Update Tabel"):
        save_data(edited_df, FILE_STOK)
        st.success("Data diperbarui!")

# ================= MENU: LAPORAN =================
elif menu == "Laporan Keuangan":
    st.header("📊 Laporan & Riwayat")
    if not df_transaksi.empty:
        t_omset = df_transaksi['Total Harga'].sum()
        t_jasa = df_transaksi['Jasa Servis'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Omset", f"Rp {t_omset:,}")
        c2.metric("Jasa", f"Rp {t_jasa:,}")
        c3.metric("Barang", f"Rp {t_omset - t_jasa:,}")

        st.subheader("Riwayat Transaksi")
        for i, row in df_transaksi.iterrows():
            with st.expander(f"{row['Tanggal']} - {row['Pelanggan']} ({row['Plat Nomor']})"):
                col_t, col_b = st.columns([4, 1])
                col_t.write(f"Detail: {row['Barang']} ({row['Qty']}) | Total: Rp {row['Total Harga']:,}")
                if col_b.button("🗑️ Hapus", key=f"del_{i}"):
                    if row['Barang'] != "- Tidak Ada -":
                        if row['Barang'] in df_stok['Nama Barang'].values:
                            idx_s = df_stok.index[df_stok['Nama Barang'] == row['Barang']].tolist()[0]
                            df_stok.at[idx_s, 'Stok'] += row['Qty']
                            save_data(df_stok, FILE_STOK)
                    df_transaksi = df_transaksi.drop(i).reset_index(drop=True)
                    save_data(df_transaksi, FILE_TRANSAKSI)
                    st.rerun()
        
        st.download_button("Download CSV", df_transaksi.to_csv(index=False), "laporan.csv", "text/csv")
    else:
        st.info("Belum ada data.")