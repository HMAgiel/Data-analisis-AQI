import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st


#Function yang dipakai
#function plot pola

def plot_klim(polutan, cuaca=['TEMP', 'WSPM', 'RAIN']):
    bulan_label = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                   'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    satuan = {'TEMP': '°C', 'WSPM': 'm/s', 'RAIN': 'mm/bulan'}
    warna_cuaca = {'TEMP': 'tab:red', 'DEWP': 'tab:green', 'PRES': 'tab:purple',
                   'WSPM': 'tab:orange', 'RAIN': 'tab:blue'}


    klim = gabung.groupby(['month', 'station'])[polutan].mean().unstack('station')


    agg = {v: ('sum' if v == 'RAIN' else 'mean') for v in cuaca}
    cb = gabung.groupby(['station', 'year', 'month'])[cuaca].agg(agg)
    klim_cuaca = cb.groupby('month').mean()

    cmap = plt.get_cmap('tab20')
    n = 1 + len(cuaca)
    fig, axes = plt.subplots(n, 1, figsize=(13, 3 + 2.2 * n), sharex=True,
                             gridspec_kw={'height_ratios': [2.5] + [1] * len(cuaca)})


    ax = axes[0]
    for i, nama in enumerate(header_loaksi):
        ax.plot(klim.index, klim[nama], color=cmap(i), linewidth=1.2, alpha=0.8, label=nama)
    ax.plot(klim.index, klim.mean(axis=1), color='black', linewidth=3, label='Rata-rata stasiun')
    ax.set_ylabel(f'{polutan}\n(µg/m³)')
    ax.set_title(f'Klimatologi bulanan {polutan} dan variabel cuaca')
    ax.grid(alpha=0.3)
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5), frameon=False)

    # panel cuaca
    for ax, v in zip(axes[1:], cuaca):
        if v == 'RAIN':
            ax.bar(klim_cuaca.index, klim_cuaca[v], color=warna_cuaca[v], alpha=0.7)
        else:
            ax.plot(klim_cuaca.index, klim_cuaca[v], color=warna_cuaca[v], linewidth=2.5, marker='o')
        ax.set_ylabel(f'{v}\n({satuan.get(v, "")})')
        ax.grid(alpha=0.3)

    axes[-1].set_xticks(range(1, 13))
    axes[-1].set_xticklabels(bulan_label)
    st.pyplot(fig=fig)
    plt.close()
    
#Fungsi plot rose
def plot_rose(polutan: str):
  data = {}
  for nama, bln in musim.items():
      d = gabung[gabung['month'].isin(bln)]
      frek = d['wd'].value_counts(normalize=True).reindex(arah).fillna(0) * 100
      pm = d.groupby('wd')[polutan].mean().reindex(arah)
      data[nama] = (frek, pm)

  # batas radial sama untuk kedua musim supaya bisa dibandingkan
  fmax = max(f.max() for f, _ in data.values()) * 1.1
  pmax = max(p.max() for _, p in data.values()) * 1.1

  baris = [('Frekuensi arah angin (%)', fmax, plt.cm.Blues, 0),
          (f'Rata-rata {polutan} (µg/m³)',  pmax, plt.cm.Reds,  1)]

  fig, axes = plt.subplots(2, 2, subplot_kw={'projection': 'polar'}, figsize=(12, 12))
  for j, (nama, nilai_musim) in enumerate(data.items()):
      for judul, rmax, cmap, i in baris:
          nilai = nilai_musim[i]
          ax = axes[i, j]
          ax.set_theta_zero_location('N')
          ax.set_theta_direction(-1)
          ax.bar(theta, nilai.values, width=np.deg2rad(22.5),
                color=cmap(nilai.values / rmax), edgecolor='white')
          ax.set_ylim(0, rmax)
          ax.set_xticks(theta)
          ax.set_xticklabels(arah)
          ax.set_title(f'{nama}\n{judul}', pad=20)

  st.pyplot(fig=fig)
  plt.close()

def plot_klasifikasi(polutan: str):
    harian = (gabung.set_index('datetime')
                    .groupby('station')[polutan]
                    .resample('D').mean()
                    .reset_index())
    harian['month'] = harian['datetime'].dt.month

    # 2. kategori US EPA AQI untuk PM2.5 (revisi 2024)
    batas = [0, 9.0, 35.4, 55.4, 125.4, 225.4, np.inf]
    label = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups',
            'Unhealthy', 'Very Unhealthy', 'Hazardous']
    harian['AQI'] = pd.cut(harian[polutan], bins=batas, labels=label, include_lowest=True)

    # 3. % hari per kategori per bulan (semua stasiun & tahun)
    pct = pd.crosstab(harian['month'], harian['AQI'], normalize='index') * 100

    # 4. plot dengan warna resmi EPA
    warna_epa = ['#00e400', '#ffff00', '#ff7e00', '#ff0000', '#8f3f97', '#7e0023']
    fig, ax = plt.subplots(figsize=(12, 5))
    pct.plot(kind='bar', stacked=True, color=warna_epa, width=0.85,
                figsize=(12, 5), edgecolor='white', linewidth=0.5, ax=ax)
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'],
                    rotation=0)
    ax.set_ylabel('Persentase hari (%)')
    ax.set_xlabel('Bulan')
    ax.set_title(f'Distribusi kategori US AQI ({polutan} harian) per bulan, semua stasiun 2013–2017')
    buruk = pct[['Unhealthy', 'Very Unhealthy', 'Hazardous']].sum(axis=1)
    ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5), frameon=False)
    
    st.pyplot(fig=fig)
    plt.close()

#Read data
df = []
header_loaksi = ["Aotizhongxin", "Changping", "Dingling", "Dongsi", "Guanyuan", "Gucheng", "Huairou", "Nongzhanguan",
                 "Shunyi", "Tiantan", "Wanliu", "Wanshouxigong"]

for i in header_loaksi:
    try:
        df.append(pd.read_excel("/home/hasyim/dicoding/data_analysis/submission/dashboard/data_kualitas_udara_beijing.xlsx", sheet_name= i, engine="calamine"))
        print("Berhasil input data")
    
    except FileExistsError:
        print("File error")

# Data process
gabung = pd.concat(df, keys=header_loaksi, names=['station']).reset_index()

bulanan = gabung.groupby(['station', 'month']).agg({
    'PM2.5': 'mean',
    'PM10': 'mean'
})

arah = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']
theta = np.deg2rad(np.arange(16) * 22.5)
musim = {'Musim dingin (Des–Feb)': [12, 1, 2],
         'Musim panas (Jun–Agu)':  [6, 7, 8]}


#Streamlit logic        
st.header('Hasyim Pollution Dashboard :sparkles:')

st.markdown("""
           ## Latar Belakang
Pada project ini, saya mencoba memposisikan diri sebagai pebisnis masker yang ingin melihat kapan waktu polusi tinggi dan faktor apa yang memengaruhinya pada semua wilayah. Tujuan melihat kapan waktu tertinggi ini adalah untuk mencoba meningkatkan penjualan dengan melakukan pemasaran di saat polusi tertinggi, serta untuk persiapan penambahan stok dan pemasaran sebelum puncak polusi itu terjadi.


## Pertanyaan
Dari latar belakang di atas, maka saya membuat pertanyaan:

**Pertanyaan 1**: Pengaruh variabel temperatur, hujan, dan angin terhadap konsentrasi PM 2.5 dan PM 10, serta bagaimana perubahan variabel cuaca terhadap pola konsentrasi dalam rentang klimatologi bulanan di 12 wilayah pengamatan.

Keterangan pertanyaan 1:

- **Specific**: Fokus pada polutan PM 2.5 dan PM 10, serta pada variabel cuaca hujan, temperatur, dan kecepatan angin.
- **Measurable**: Besar pengaruh dalam korelasi dan perubahan pola.
- **Action-Oriented**: Dengan mengetahui hubungan polutan dengan cuaca serta perubahan pola, maka dapat dilakukan edukasi ke masyarakat saat pola polutan tinggi dan rendah, serta dapat juga melakukan promosi, terutama saat polutan tinggi.
- **Relevant**: Kenaikan dan penurunan polutan berpengaruh terhadap banyaknya penggunaan masker untuk kesehatan.
- **Time-bound**: Klimatologi bulanan.

**Pertanyaan 2**: Berdasarkan arah dan kecepatan angin dari seluruh wilayah, bagaimana pergerakan dari dan ke particulate matter saat musim panas dan musim dingin?

- **Specific**: Fokus pada arah angin dan polutan PM 2.5 dan PM 10.
- **Measurable**: Dihitung berdasarkan kategori arah angin saja.
- **Action-Oriented**: Dengan mengetahui arah angin, dapat diketahui ke mana arah gerak polutan dan dari mana asalnya, sehingga pada wilayah yang dilalui dapat dilakukan promosi dengan lebih detail kepada orang-orang di wilayah tersebut.
- **Relevant**: Arah pergerakan polutan memengaruhi wilayah mana yang terdampak dan dapat dijadikan target market.
- **Time-bound**: Musim panas dan musim dingin. """)

st.subheader("Pertanyaan 1: Pengaruh variabel temperatur, hujan, dan angin terhadap konsentrasi PM 2.5 dan PM 10, serta bagaimana perubahan variabel cuaca terhadap pola konsentrasi dalam rentang klimatologi bulanan di 12 wilayah pengamatan.")
st.subheader("Korelasi polutan")

cuaca = ['TEMP', 'RAIN', 'WSPM']

korelasi_pm_2_5 = {}
for nama, d in zip(header_loaksi, df):
    matrix = d.corr(numeric_only=True)
    korelasi_pm_2_5[nama] = matrix.loc['PM2.5', cuaca]

korelasi_pm25 = pd.DataFrame(korelasi_pm_2_5).T

korelasi_pm_10 = {}
for nama, d in zip(header_loaksi, df):
    matrix = d.corr(numeric_only=True)
    korelasi_pm_10[nama] = matrix.loc['PM10', cuaca]

korelasi_pm10 = pd.DataFrame(korelasi_pm_10).T

fig1, ax1 = plt.subplots(figsize=(8, 6))
sns.heatmap(korelasi_pm25, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, center=0)
ax1.set_title('Korelasi PM2.5 dengan variabel cuaca per stasiun')

fig2, ax2 = plt.subplots(figsize=(8, 6))
sns.heatmap(korelasi_pm10, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, center=0)
ax2.set_title('Korelasi PM2.5 dengan variabel cuaca per stasiun')

kor1, kor2 = st.columns(2)

with kor1:
    st.pyplot(fig=fig1)
    plt.close()
    st.caption("Korelasi PM 2.5 dan variabel cuaca", text_alignment='center')

with kor2:
    st.pyplot(fig=fig2)
    plt.close()
    st.caption("Korelasi PM 10 dan variabel cuaca", text_alignment='center')

st.markdown("""
Hasil korelasi variabel cuaca menunjukkan hasil yang lemah untuk semua variabel, dengan nilai korelasi terhadap PM 2.5 dan PM 10 di bawah 0,3. Dari hasil ini juga dapat terlihat bahwa variabel cuaca berkorelasi negatif dengan partikulat.

Maka dari hasil ini dapat dikatakan bahwa partikulat memiliki hubungan berkebalikan yang lemah dengan temperatur, hujan, dan angin.

Dari hasil hubungan ini, dapat dikatakan bahwa partikulat akan bernilai tinggi saat suhu, hujan, dan angin rendah, di mana hal ini biasanya terjadi di musim dingin.
\n""")


st.subheader("Pola polutan dan variabel cuaca")

plot_klim('PM2.5', cuaca=['TEMP', 'WSPM', 'RAIN'])
st.caption("Pola Polutan PM 2.5 dan data cuaca", text_alignment="center")

st.markdown("""
            Pada pola polutan PM2.5 terlihat adanya kenaikan dimulai dari bulan September dan mencapai puncak di bulan Desember atau Januari, lalu mulai mengalami penurunan dari bulan Maret sampai titik terendah di bulan Agustus.

Jika dilihat dari pola temperatur, nilai polutan mencapai titik terendah saat temperatur tinggi dan mencapai puncak saat temperatur rendah. Hal ini sejalan dengan nilai korelasi yang berkebalikan.

Sedangkan untuk pola angin, nilainya tidak terlalu mengikuti polutan dan terdapat lag, atau tidak serupa pada puncak dan titik terendah polutan.

Pada hujan, tidak ada kesesuaian antara pola polutan dengan hujan. Hal ini sesuai dengan korelasi hujan dan polutan.
            """)

plot_klim('PM10', cuaca=['TEMP', 'WSPM', 'RAIN'])
st.caption("Pola Polutan PM 10 dan data cuaca", text_alignment="center")

st.markdown("""
Dari hasil plot line polutan PM10, temperatur, angin, dan plot bar hujan, dapat diketahui bahwa polutan memiliki pola yang serupa untuk semua wilayah, di mana terdapat pola kenaikan yang signifikan dari bulan September dan mencapai puncak di bulan Maret, lalu turun dan mencapai titik terendah di bulan Juli atau Agustus.
            \n""")

st.subheader("Berdasarkan arah dan kecepatan angin dari seluruh wilayah, bagaimana pergerakan dari dan ke particulate matter saat musim panas dan musim dingin?")

plot_rose("PM2.5")
st.caption("Plot rose PM 2.5", text_alignment="center")

plot_rose("PM10")
st.caption("Plot rose PM 10", text_alignment="center")

st.markdown("""
            Pada hasil peta windrose dan juga pollution rose, terlihat bahwa pergerakannya sama untuk PM 10 dan PM 2.5, di mana saat musim dingin kebanyakan angin bergerak dari barat laut ke utara dan timur laut, sedangkan pada musim panas dari utara ke timur laut.

Pada kedua musim itu juga polutan terlihat tinggi di musim dingin dengan hampir dominasi di seluruh arah angin, kecuali dari barat ke utara, sedangkan di musim panas pergerakan polutan cenderung lemah.

Hal ini sejalan dengan analisis bulanan, di mana polutan tinggi di akhir tahun sampai awal tahun, yaitu pada musim dingin, dan rendah pada musim panas di pertengahan tahun.
            """)

st.subheader("Analisis lanjutan kategorikal")
st.markdown("""
            Pada analisis lanjutan di sini saya akan mencoba mengelompokan polutan berdasarkan kriteria dari US Air Quality Index, polutan akan dirata-rata dulu di setiap stasiun dan dilihat perbukan bagaiaman dan yang termasuk katrgori berbahaya yang mana

Berikut adalah index yang dipakai

| Nilai AQI | Kategori (Level of Concern) | Warna  | Keterangan |
|-----------|-----------------------------|--------|------------|
| 0 – 50    | Good                        | Hijau  | Kualitas udara memuaskan, polusi udara sedikit atau tidak berisiko. |
| 51 – 100  | Moderate                    | Kuning | Kualitas udara dapat diterima, tetapi bisa berisiko bagi sebagian kecil orang yang sangat sensitif terhadap polusi. |
| 101 – 150 | Unhealthy for Sensitive Groups | Oranye | Kelompok sensitif (anak-anak, lansia, penderita penyakit jantung/paru) dapat mengalami gangguan kesehatan. Masyarakat umum kemungkinan kecil terdampak. |
| 151 – 200 | Unhealthy                   | Merah  | Sebagian masyarakat umum dapat mengalami gangguan kesehatan; kelompok sensitif dapat mengalami dampak yang lebih serius. |
| 201 – 300 | Very Unhealthy              | Ungu   | Peringatan kesehatan: risiko dampak kesehatan meningkat bagi semua orang. |
| 301+      | Hazardous                   | Merah marun | Peringatan darurat kesehatan: semua orang lebih mungkin terdampak. |
            """)

plot_klasifikasi("PM2.5")
st.caption("Kategori PM 2.5 rata=rata stasiun di semua bulan", text_alignment='center')

plot_klasifikasi("PM10")
st.caption("Kategori PM 10 rata=rata stasiun di semua bulan", text_alignment='center')

st.markdown("""
            Berdasarkan hasil pengelompokan polutan dari Air Quality Index, terlihat bahwa pada bulan Oktober sampai Maret terdapat persentase yang tinggi untuk kategori hazardous yang mana ini amat sangat melebihi batas atas.

Dari hasil ini, maka dapat dikatakan bahwa pada bulan-bulan dengan kategori tinggi dapat menjadi peluang potensi pada edukasi masyarakat tentang bahaya pencemaran polutan PM 10 dan PM 2.5, serta untuk pemasaran penjualan masker dari perusahaan.
            """)


st.subheader("Conclusion")
st.markdown("""
            - **Conclusion pertanyaan 1:** Kesimpulan yang didapatkan dari pertanyaan 1 adalah, polutan PM 2.5 dan PM 10 tidak memiliki korelasi atau hubungan yang kuat dengan temperatur, hujan, dan angin, akan tetapi pola pergerakan variabel cuaca menunjukkan adanya keterkaitan dengan sistem yang lebih luas, di mana pada musim gugur dan dingin nilai polutan naik dan mencapai titik tertinggi, lalu turun kembali dan mencapai titik terendah di musim panas.



- **Conclusion pertanyaan 2:** Pada pertanyaan kedua, pergerakan polutan di musim dingin cenderung tersebar dari semua wilayah, sedangkan pada musim panas lemah di semua arah angin.

Dari hasil kedua ini juga dapat disimpulkan untuk bisnis masker yang menjadi dasar analisis adalah penjualan dapat diboost di waktu polutan tinggi, yaitu saat musim gugur dan musim dingin. Hal ini dapat dilakukan dengan mengedukasi masyarakat di saat polutan rendah di musim panas sehingga saat musim dingin masyarakat aware dan mulai adanya peningkatan pembelian.
            """)

st.markdown("""
            **Rekomendasi Action Item:**
- Perlunya dilakukan penelitian lebih lanjut dengan acuan yang lebih detail dan data yang lebih panjang.
- Pada edukasi ke masyarakat, perlu ditekankan bahwa polutan PM 10 dan PM 2.5 berbahaya, lalu perlu ditekankan pada bulan-bulan yang benar-benar terlihat berbahaya.
- Perlunya memakai data cuaca lain agar lebih terlihat faktor cuaca apa yang benar-benar memengaruhi polutan.
- Jika memungkinkan, perlunya penggunaan machine learning, terutama untuk mengisi data kosong, karena dengan metode sekarang terlalu robust.
            """)

with st.bottom:
    st.text("Hasil Analisis Air Quality Data | Hasim Muhammad Agiel")