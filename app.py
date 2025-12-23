import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Servis Bengkel", layout="wide")

st.title("🛠️ Monitoring Servis Pelanggan")

# 1. Koneksi ke Google Sheets
# Pastikan URL sheet sudah di-share (view only)
url = "https://docs.google.com/spreadsheets/d/1wGEojxqModICUSxRIgCONuiLRIyrEhMGRDWsmxWXjng/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(spreadsheet=url)
    
    # Pastikan kolom tanggal dalam format datetime
    df['Tanggal Servis Terakhir'] = pd.to_datetime(df['Tanggal Servis Terakhir'])

    # 2. Filter Logika: 2 Bulan (60 Hari) yang lalu
    hari_ini = datetime.now()
    batas_servis = hari_ini - timedelta(days=60)

    # Pelanggan yang butuh servis (servis terakhir <= 60 hari yang lalu)
    perlu_servis = df[df['Tanggal Servis Terakhir'] <= batas_servis].copy()
    
    # Hitung selisih hari untuk informasi tambahan
    perlu_servis['Terlambat (Hari)'] = (hari_ini - perlu_servis['Tanggal Servis Terakhir']).dt.days

    # 3. Tampilan Dashboard
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pelanggan", len(df))
    col2.metric("Perlu Servis Segera", len(perlu_servis))
    col3.metric("Rata-rata Servis", f"{int(df['Tanggal Servis Terakhir'].count())} Unit")

    st.subheader("📋 Daftar Motor Yang Harus Diservis (Sudah 2 Bulan+)")
    
    if not perlu_servis.empty:
        # Menampilkan tabel data yang perlu diservis
        st.dataframe(perlu_servis.sort_values(by="Tanggal Servis Terakhir"), use_container_width=True)
        
        # Fitur Tambahan: Tombol Chat WhatsApp Otomatis
        st.subheader("📲 Hubungi Pelanggan")
        for index, row in perlu_servis.iterrows():
            pesan = f"Halo {row['Nama Pelanggan']}, motor {row['Tipe Motor']} ({row['No Polisi']}) sudah waktunya servis kembali di Bengkel kami. Yuk datang hari ini!"
            link_wa = f"https://wa.me/{row['No WhatsApp']}?text={pesan.replace(' ', '%20')}"
            
            with st.expander(f"Hubungi {row['Nama Pelanggan']} - {row['No Polisi']}"):
                st.write(f"Terakhir servis: {row['Tanggal Servis Terakhir'].strftime('%d %b %Y')}")
                st.write(f"Keterlambatan: {row['Terlambat (Hari)']} hari")
                st.markdown(f"[Kirim WhatsApp Klik Di Sini]({link_wa})")
                
    else:
        st.success("Semua motor pelanggan masih dalam kondisi prima (belum masuk masa servis).")

except Exception as e:
    st.error(f"Gagal memuat data. Pastikan URL Sheet benar dan bisa diakses. Error: {e}")