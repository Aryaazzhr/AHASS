import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Bengkel Pro", layout="wide")

st.title("🛠️ Monitoring & Insight Pelanggan Bengkel")

# 1. Koneksi ke Google Sheets
url = "https://docs.google.com/spreadsheets/d/1wGEojxqModICUSxRIgCONuiLRIyrEhMGRDWsmxWXjng/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Read data & hapus spasi di nama kolom
    df = conn.read(spreadsheet=url)
    df.columns = df.columns.str.strip()
    
    # Konversi Tanggal
    df['Tgl Service Terakhir'] = pd.to_datetime(df['Tgl Service Terakhir'])
    
    # --- LOGIKA FILTER SERVIS ---
    hari_ini = datetime.now()
    batas_servis = hari_ini - timedelta(days=60)
    perlu_servis = df[df['Tgl Service Terakhir'] <= batas_servis].copy()
    perlu_servis['Terlambat (Hari)'] = (hari_ini - perlu_servis['Tgl Service Terakhir']).dt.days

    # --- BAGIAN 1: METRIK UTAMA ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Pelanggan", len(df))
    col2.metric("Perlu Servis", len(perlu_servis))
    col3.metric("Rata-rata Terlambat", f"{int(perlu_servis['Terlambat (Hari)'].mean()) if not perlu_servis.empty else 0} Hari")
    col4.metric("Unit Masuk (Bulan Ini)", len(df[df['Tgl Service Terakhir'].dt.month == hari_ini.month]))

    st.divider()

    # --- BAGIAN 2: VISUALISASI INSIGHT ---
    st.subheader("📊 Insight Database Pelanggan")
    c1, c2 = st.columns(2)

    with c1:
        # Plot Jenis Motor
        if 'Market Name' in df.columns:
            fig_motor = px.bar(df['Market Name'].value_counts().head(10), 
                               title="Top 10 Jenis Motor", 
                               labels={'value':'Jumlah', 'index':'Model'},
                               color_discrete_sequence=['#FF4B4B'])
            st.plotly_chart(fig_motor, use_container_width=True)

        # Plot Tanggal Terakhir Service (Tren Bulanan)
        df_trend = df.resample('M', on='Tgl Service Terakhir').size().reset_index(name='Jumlah')
        fig_trend = px.line(df_trend, x='Tgl Service Terakhir', y='Jumlah', 
                            title="Tren Kedatangan Pelanggan (Bulanan)")
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        # Plot Daerah (Asumsi ada kolom 'Kecamatan' atau 'Alamat')
        kolom_daerah = 'Kecamatan' if 'Kecamatan' in df.columns else None
        if kolom_daerah:
            fig_daerah = px.pie(df[kolom_daerah].value_counts().head(5), 
                                names=df[kolom_daerah].value_counts().head(5).index,
                                values=df[kolom_daerah].value_counts().head(5).values,
                                title="Distribusi Wilayah Pelanggan")
            st.plotly_chart(fig_daerah, use_container_width=True)
        else:
            st.info("Kolom 'Kecamatan' tidak ditemukan untuk plot daerah.")

        # Plot Umur/Tahun Motor
        if 'Tahun' in df.columns:
            fig_tahun = px.histogram(df, x='Tahun', title="Distribusi Tahun Motor", nbins=10)
            st.plotly_chart(fig_tahun, use_container_width=True)
        elif 'Umur' in df.columns:
            fig_umur = px.histogram(df, x='Umur', title="Distribusi Umur Pelanggan")
            st.plotly_chart(fig_umur, use_container_width=True)

    st.divider()

    # --- BAGIAN 3: DAFTAR FOLLOW UP (WHATSAPP JADI SATU) ---
    st.subheader("📲 Daftar Hubungi Pelanggan (Waktunya Servis)")
    
    if not perlu_servis.empty:
        # Menyiapkan kolom Link WhatsApp
        def create_wa_link(row):
            pesan = f"Halo {row['Nama']}, motor {row['Market Name']} ({row['Nopol']}) sudah waktunya servis kembali. Terakhir servis {row['Tgl Service Terakhir'].strftime('%d %b %Y')}. Yuk ke Bengkel hari ini!"
            nomor = str(row['No HP1']).replace('.0', '')
            # Pastikan nomor diawali '62'
            if nomor.startswith('0'): nomor = '62' + nomor[1:]
            return f"https://wa.me/{nomor}?text={pesan.replace(' ', '%20')}"

        perlu_servis['WhatsApp'] = perlu_servis.apply(create_wa_link, axis=1)

        # Menampilkan tabel ringkas dengan link klik
        # Kita gunakan st.dataframe dengan kolom link yang bisa diklik
        st.write("Klik ikon link pada kolom WhatsApp untuk membuka chat:")
        
        display_df = perlu_servis[['Nama', 'Nopol', 'Market Name', 'Tgl Service Terakhir', 'Terlambat (Hari)', 'WhatsApp']]
        
        st.data_editor(
            display_df.sort_values(by="Terlambat (Hari)", ascending=False),
            column_config={
                "WhatsApp": st.column_config.LinkColumn("Hubungi Pelanggan", display_text="Kirim Pesan 🟢"),
                "Tgl Service Terakhir": st.column_config.DateColumn("Terakhir Servis"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("Luar biasa! Tidak ada pelanggan yang telat servis (di atas 2 bulan).")

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
    st.info("Saran: Pastikan nama kolom di Google Sheets sesuai (Nama, Nopol, Market Name, Tgl Service Terakhir, No HP1)")
