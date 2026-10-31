import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Hasyim Pollution Dashboard", page_icon="☁️", layout="wide")

#Variabel yang dipakai
header_loaksi = ["Aotizhongxin", "Changping", "Dingling", "Dongsi", "Guanyuan", "Gucheng", "Huairou", "Nongzhanguan",
                 "Shunyi", "Tiantan", "Wanliu", "Wanshouxigong"]
bulan_label = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
               'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
arah = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']
cuaca = ['TEMP', 'WSPM', 'RAIN']
nama_cuaca = {'TEMP': 'Temperatur (°C)', 'WSPM': 'Kecepatan angin (m/s)', 'RAIN': 'Hujan (mm/bulan)'}
musim = {'Musim dingin (Des–Feb)': [12, 1, 2],
         'Musim panas (Jun–Agu)':  [6, 7, 8]}

# warna stasiun yang di-highlight (maksimal 4 stasiun)
warna_highlight = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
warna_cuaca = '#0E7C86'

# kategori US EPA AQI (revisi 2024), batas PM2.5 dan PM10 berbeda
batas_aqi = {'PM2.5': [0, 9.0, 35.4, 55.4, 125.4, 225.4, np.inf],
             'PM10':  [0, 54, 154, 254, 354, 424, np.inf]}
label_aqi = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups',
             'Unhealthy', 'Very Unhealthy', 'Hazardous']
warna_epa = ['#00e400', '#ffff00', '#ff7e00', '#ff0000', '#8f3f97', '#7e0023']


#Read data
@st.cache_data
def load_data():
    df = []
    for i in header_loaksi:
        df.append(pd.read_excel("submission/dashboard/data_kualitas_udara_beijing.xlsx", sheet_name=i, engine="calamine"))

    gabung = pd.concat(df, keys=header_loaksi, names=['station']).reset_index()
    return gabung


#Function yang dipakai
#function data harian + kategori AQI
def hitung_harian(data, polutan):
    harian = (data.set_index('datetime')
                  .groupby('station')[polutan]
                  .resample('D').mean()
                  .reset_index())
    harian['month'] = harian['datetime'].dt.month
    harian['AQI'] = pd.cut(harian[polutan], bins=batas_aqi[polutan], labels=label_aqi, include_lowest=True)
    return harian

#function plot pola
def plot_klim(data, polutan, stasiun_pilih):
    klim = data.groupby(['month', 'station'])[polutan].mean().reset_index()
    rata = klim.groupby('month')[polutan].mean()

    # stasiun yang dipilih diberi warna, sisanya abu-abu
    warna = {}
    for nama in header_loaksi:
        if nama in stasiun_pilih:
            warna[nama] = warna_highlight[stasiun_pilih.index(nama)]
        else:
            warna[nama] = 'lightgray'

    # stasiun yang dipilih digambar paling akhir supaya ada di atas garis abu-abu
    urutan = [nama for nama in header_loaksi if nama not in stasiun_pilih] + stasiun_pilih

    fig = px.line(klim, x='month', y=polutan, color='station',
                  color_discrete_map=warna, category_orders={'station': urutan},
                  title=f'Pola bulanan {polutan} per stasiun')

    for garis in fig.data:
        if garis.name in stasiun_pilih:
            garis.line.width = 4
            garis.mode = 'lines+markers'
        else:
            garis.line.width = 1
            garis.showlegend = False

    fig.add_scatter(x=rata.index, y=rata.values, name='Rata-rata stasiun', mode='lines',
                    line=dict(color='#1B2A35', width=3, dash='dash'))
    fig.update_xaxes(tickvals=list(range(1, 13)), ticktext=bulan_label, title='Bulan')
    fig.update_yaxes(title=f'{polutan} (µg/m³)')
    fig.update_layout(height=450, legend_title_text='')
    st.plotly_chart(fig)

    with st.expander("Lihat tabel data"):
        tabel = klim.pivot(index='month', columns='station', values=polutan).round(1)
        tabel.index = [bulan_label[b - 1] for b in tabel.index]
        st.dataframe(tabel)

#function plot cuaca
def plot_cuaca(data):
    agg = {v: ('sum' if v == 'RAIN' else 'mean') for v in cuaca}
    cb = data.groupby(['station', 'year', 'month'])[cuaca].agg(agg)
    klim_cuaca = cb.groupby('month').mean().reset_index()

    kolom = st.columns(3)
    for kol, v in zip(kolom, cuaca):
        if v == 'RAIN':
            fig = px.bar(klim_cuaca, x='month', y=v, title=nama_cuaca[v],
                         color_discrete_sequence=[warna_cuaca])
        else:
            fig = px.line(klim_cuaca, x='month', y=v, title=nama_cuaca[v], markers=True,
                          color_discrete_sequence=[warna_cuaca])
        fig.update_xaxes(tickvals=list(range(1, 13)), ticktext=bulan_label, title='')
        fig.update_yaxes(title='')
        fig.update_layout(height=300)
        with kol:
            st.plotly_chart(fig)

#function plot korelasi
def plot_korelasi(data, polutan):
    korelasi = {}
    for nama in data['station'].unique():
        d = data[data['station'] == nama]
        korelasi[nama] = d[[polutan] + cuaca].corr().loc[polutan, cuaca]

    korelasi_df = pd.DataFrame(korelasi).T
    korelasi_df.columns = [nama_cuaca[v] for v in cuaca]

    fig = px.imshow(korelasi_df, text_auto='.2f', color_continuous_scale='RdBu_r',
                    zmin=-1, zmax=1, aspect='auto',
                    title=f'Korelasi {polutan} dengan variabel cuaca per stasiun')
    fig.update_layout(height=500)
    st.plotly_chart(fig)

#Fungsi plot rose
def plot_rose(data, polutan, musim_pilih):
    # batas radial dari semua musim supaya bisa dibandingkan saat ganti musim
    fmax = 0
    pmax = 0
    for bln in musim.values():
        d = data[data['month'].isin(bln)]
        if len(d) > 0:
            fmax = max(fmax, (d['wd'].value_counts(normalize=True) * 100).max())
            pmax = max(pmax, d.groupby('wd')[polutan].mean().max())

    d = data[data['month'].isin(musim[musim_pilih])]
    if len(d) == 0:
        st.info("Tidak ada data untuk musim ini di rentang waktu yang dipilih")
        return

    rose = pd.DataFrame({
        'arah': arah,
        'frekuensi': d['wd'].value_counts(normalize=True).reindex(arah).fillna(0).values * 100,
        polutan: d.groupby('wd')[polutan].mean().reindex(arah).values
    })

    kol1, kol2 = st.columns(2)
    with kol1:
        fig = px.bar_polar(rose, r='frekuensi', theta='arah', color='frekuensi',
                           color_continuous_scale='Blues', range_r=[0, fmax * 1.1],
                           range_color=[0, fmax * 1.1], title='Frekuensi arah angin (%)')
        fig.update_layout(height=450)
        st.plotly_chart(fig)
    with kol2:
        fig = px.bar_polar(rose, r=polutan, theta='arah', color=polutan,
                           color_continuous_scale='Oranges', range_r=[0, pmax * 1.1],
                           range_color=[0, pmax * 1.1], title=f'Rata-rata {polutan} (µg/m³)')
        fig.update_layout(height=450)
        st.plotly_chart(fig)

#function plot kategori AQI
def plot_klasifikasi(harian, polutan):
    # % hari per kategori per bulan
    pct = pd.crosstab(harian['month'], harian['AQI'], normalize='index') * 100
    pct.columns = pct.columns.astype(str)
    pct = pct.reindex(columns=label_aqi, fill_value=0).reset_index()

    fig = px.bar(pct, x='month', y=label_aqi, color_discrete_sequence=warna_epa,
                 title=f'Distribusi kategori US AQI ({polutan} harian) per bulan',
                 labels={'value': 'Persentase hari (%)', 'variable': 'Kategori AQI'})
    fig.update_traces(marker_line_color='white', marker_line_width=1)
    fig.update_xaxes(tickvals=list(range(1, 13)), ticktext=bulan_label, title='Bulan')
    fig.update_layout(height=450, bargap=0.15)
    st.plotly_chart(fig)


# Data process
gabung = load_data()

min_date = gabung['datetime'].min().date()
max_date = gabung['datetime'].max().date()


#Sidebar
with st.sidebar:
    st.title("Filter Data")

    polutan = st.selectbox("Pilih polutan", ["PM2.5", "PM10"])

    tanggal = st.date_input("Rentang waktu", value=[min_date, max_date],
                            min_value=min_date, max_value=max_date)

    stasiun_pilih = st.multiselect("Pilih stasiun", header_loaksi, max_selections=4,
                                   placeholder="Semua stasiun",
                                   help="Stasiun yang dipilih di-highlight di grafik pola bulanan "
                                        "dan dipakai untuk grafik lain. Kosongkan untuk semua stasiun.")

if len(tanggal) != 2:
    st.warning("Pilih tanggal akhir dulu di sidebar")
    st.stop()

start_date, end_date = tanggal

main_df = gabung[(gabung['datetime'] >= pd.to_datetime(start_date)) &
                 (gabung['datetime'] < pd.to_datetime(end_date) + pd.Timedelta(days=1))]

if len(stasiun_pilih) > 0:
    stasiun_df = main_df[main_df['station'].isin(stasiun_pilih)]
else:
    stasiun_df = main_df

harian = hitung_harian(stasiun_df, polutan)


#Streamlit logic
st.header('Hasyim Pollution Dashboard :sparkles:')

if len(stasiun_pilih) > 0:
    teks_stasiun = ", ".join(stasiun_pilih)
else:
    teks_stasiun = "Semua stasiun"
st.caption(f"{start_date} s/d {end_date} | {teks_stasiun}")

rata_polutan = stasiun_df[polutan].mean()
bulan_tinggi = stasiun_df.groupby('month')[polutan].mean().idxmax()
stasiun_tinggi = stasiun_df.groupby('station')[polutan].mean().idxmax()
persen_buruk = harian['AQI'].isin(['Unhealthy', 'Very Unhealthy', 'Hazardous']).mean() * 100

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(f"Rata-rata {polutan}", value=f"{rata_polutan:.1f} µg/m³", border=True)
with col2:
    st.metric("Bulan tertinggi", value=bulan_label[bulan_tinggi - 1], border=True)
with col3:
    st.metric("Stasiun tertinggi", value=stasiun_tinggi, border=True)
with col4:
    st.metric("Hari Unhealthy ke atas", value=f"{persen_buruk:.1f}%", border=True)

tab1, tab2, tab3, tab4 = st.tabs(["Pola Bulanan", "Korelasi", "Arah Angin", "Kategori AQI"])

with tab1:
    plot_klim(main_df, polutan, stasiun_pilih)
    st.subheader("Variabel cuaca")
    plot_cuaca(stasiun_df)

with tab2:
    plot_korelasi(stasiun_df, polutan)

with tab3:
    musim_pilih = st.radio("Pilih musim", list(musim.keys()), horizontal=True)
    plot_rose(stasiun_df, polutan, musim_pilih)

with tab4:
    plot_klasifikasi(harian, polutan)

with st.bottom:
    st.text("Hasil Analisis Air Quality Data | Hasim Muhammad Agiel")
