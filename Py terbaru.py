import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

st.set_page_config(page_title='Dashboard Pendidikan & Pengangguran NTB', page_icon='📊', layout='wide')
BASE=Path(__file__).parent
FILES={
'HLS':'data_hls.json','TPT':'data_tpt.json','RLS':'data_rls.json'}

@st.cache_data
def load_data():
    h=pd.read_json(BASE/FILES['HLS'])
    t=pd.read_json(BASE/FILES['TPT'])
    r=pd.read_json(BASE/FILES['RLS'])
    key=['Nama Kabupaten/Kota','Tahun']
    h=h[key+['Harapan Lama Sekolah (Tahun)']].rename(columns={'Harapan Lama Sekolah (Tahun)':'HLS'})
    r=r[key+['Rata-Rata Lama Sekolah (Tahun)']].rename(columns={'Rata-Rata Lama Sekolah (Tahun)':'RLS'})
    t=t[key+['TPT Kabupaten/Kota (Persen)']].rename(columns={'TPT Kabupaten/Kota (Persen)':'TPT'})
    # Pisahkan agregat provinsi, hilangkan duplikat persis per wilayah-tahun
    for d in (h,r,t):
        d.drop_duplicates(subset=key, keep='first', inplace=True)
    df=t.merge(r,on=key,how='outer').merge(h,on=key,how='outer')
    df=df[df['Nama Kabupaten/Kota'].str.contains('Kabupaten|Kota',case=False,na=False)].copy()
    df['Tahun']=pd.to_numeric(df['Tahun'],errors='coerce').astype('Int64')
    # Nol TPT serentak 2016 dan Lombok Utara 2018 diperlakukan sebagai kandidat missing/anomali.
    df.loc[(df['Tahun']==2016)&(df['TPT']==0),'TPT']=pd.NA
    df.loc[(df['Tahun']==2018)&(df['Nama Kabupaten/Kota'].str.contains('Lombok Utara',na=False))&(df['TPT']==0),'TPT']=pd.NA
    return df.sort_values(['Tahun','Nama Kabupaten/Kota'])

df=load_data()

st.markdown('''<style>
.block-container{
    padding-top:1.3rem;
    padding-bottom:2rem;
}
.hero{
    padding:1.3rem 1.5rem;
    border-radius:18px;
    background:linear-gradient(120deg,#0f172a,#1e3a5f);
    color:white;
    margin-bottom:1rem;
}
.hero h1{
    margin:0;
    font-size:2rem;
}
.hero p{
    margin:.4rem 0 0;
    color:#dbeafe;
}
.note{
    padding:.8rem 1rem;
    border-radius:12px;
    background:#f8fafc;
    border:1px solid #e2e8f0;
    color:#0f172a;
}

/* KPI CARD - tetap terbaca pada dark/light mode */
div[data-testid="stMetric"]{
    background:#ffffff !important;
    border:1px solid #e2e8f0 !important;
    padding:16px 14px !important;
    border-radius:16px !important;
    box-shadow:0 2px 8px rgba(0,0,0,.08) !important;
    min-height:126px;
}
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] *,
div[data-testid="stMetric"] label,
div[data-testid="stMetric"] label *{
    color:#475569 !important;
    opacity:1 !important;
    font-weight:600 !important;
}
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] *,
div[data-testid="stMetric"] [data-testid="stMetricValue"]{
    color:#0f172a !important;
    opacity:1 !important;
    font-weight:800 !important;
    font-size:1.65rem !important;
}
div[data-testid="stMetricDelta"],
div[data-testid="stMetricDelta"] *{
    opacity:1 !important;
    font-weight:700 !important;
}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>Dashboard Pendidikan & Pengangguran NTB</h1><p>TPT, Rata-Rata Lama Sekolah, dan Harapan Lama Sekolah Kabupaten/Kota</p></div>',unsafe_allow_html=True)

with st.sidebar:
    st.header('Filter Dashboard')
    years=sorted(df['Tahun'].dropna().astype(int).unique())
    year=st.selectbox('Tahun',years,index=len(years)-1)
    regions=sorted(df['Nama Kabupaten/Kota'].dropna().unique())
    selected=st.multiselect('Kabupaten/Kota',regions,default=regions)

f=df[(df['Tahun']==year)&(df['Nama Kabupaten/Kota'].isin(selected))].copy()
prev=df[(df['Tahun']==year-1)&(df['Nama Kabupaten/Kota'].isin(selected))]
avg_tpt=f.TPT.mean(); avg_rls=f.RLS.mean(); avg_hls=f.HLS.mean(); prev_tpt=prev.TPT.mean()
delta=avg_tpt-prev_tpt if pd.notna(avg_tpt) and pd.notna(prev_tpt) else None
maxrow=f.dropna(subset=['TPT']).sort_values('TPT',ascending=False).head(1)

c1,c2,c3,c4,c5=st.columns(5)
c1.metric('Rata-rata TPT',f'{avg_tpt:.2f}%' if pd.notna(avg_tpt) else 'N/A',f'{delta:+.2f} pp' if delta is not None else None)
c2.metric('Rata-rata RLS',f'{avg_rls:.2f} tahun' if pd.notna(avg_rls) else 'N/A')
c3.metric('Rata-rata HLS',f'{avg_hls:.2f} tahun' if pd.notna(avg_hls) else 'N/A')
c4.metric('TPT tertinggi',f"{maxrow.iloc[0].TPT:.2f}%" if len(maxrow) else 'N/A')
c5.metric('Wilayah TPT tertinggi',maxrow.iloc[0]['Nama Kabupaten/Kota'].replace('Kabupaten ','Kab. ') if len(maxrow) else 'N/A')

st.subheader('Perkembangan indikator')
trend=df[df['Nama Kabupaten/Kota'].isin(selected)].groupby('Tahun',as_index=False)[['TPT','RLS','HLS']].mean()
long=trend.melt('Tahun',var_name='Indikator',value_name='Nilai')
chart=alt.Chart(long).mark_line(point=True).encode(x=alt.X('Tahun:O',title='Tahun'),y=alt.Y('Nilai:Q',title='Nilai'),color='Indikator:N',tooltip=['Tahun','Indikator',alt.Tooltip('Nilai:Q',format='.2f')]).properties(height=350).interactive()
st.altair_chart(chart,use_container_width=True)

left,right=st.columns(2)
with left:
    st.subheader(f'Ranking TPT — {year}')
    rank=f.dropna(subset=['TPT']).sort_values('TPT')
    ch=alt.Chart(rank).mark_bar().encode(y=alt.Y('Nama Kabupaten/Kota:N',sort=None,title=None),x=alt.X('TPT:Q',title='TPT (%)'),tooltip=['Nama Kabupaten/Kota',alt.Tooltip('TPT:Q',format='.2f')]).properties(height=360)
    st.altair_chart(ch,use_container_width=True)
with right:
    st.subheader(f'RLS dan HLS — {year}')
    ed=f.melt(['Nama Kabupaten/Kota'],value_vars=['RLS','HLS'],var_name='Indikator',value_name='Tahun sekolah').dropna()
    ch=alt.Chart(ed).mark_bar().encode(y=alt.Y('Nama Kabupaten/Kota:N',title=None),x=alt.X('Tahun sekolah:Q'),color='Indikator:N',tooltip=['Nama Kabupaten/Kota','Indikator',alt.Tooltip('Tahun sekolah:Q',format='.2f')]).properties(height=360)
    st.altair_chart(ch,use_container_width=True)

st.subheader('Hubungan pendidikan dengan pengangguran')
a,b=st.columns(2)
for col,x in [(a,'RLS'),(b,'HLS')]:
    with col:
        dd=f.dropna(subset=[x,'TPT'])
        corr=dd[x].corr(dd.TPT) if len(dd)>1 else float('nan')
        st.caption(f'{x} vs TPT · korelasi r = {corr:.3f}' if pd.notna(corr) else f'{x} vs TPT')
        sc=alt.Chart(dd).mark_circle(size=100).encode(x=alt.X(f'{x}:Q',title=f'{x} (tahun)'),y=alt.Y('TPT:Q',title='TPT (%)'),tooltip=['Nama Kabupaten/Kota',alt.Tooltip(f'{x}:Q',format='.2f'),alt.Tooltip('TPT:Q',format='.2f')]).properties(height=320).interactive()
        st.altair_chart(sc,use_container_width=True)

st.subheader('Matriks korelasi')
corr_df=df[df['Nama Kabupaten/Kota'].isin(selected)][['TPT','RLS','HLS']].corr().round(3)
cm=corr_df.stack().reset_index(); cm.columns=['Variabel 1','Variabel 2','Korelasi']
heat=alt.Chart(cm).mark_rect().encode(x='Variabel 1:N',y='Variabel 2:N',color=alt.Color('Korelasi:Q',scale=alt.Scale(domain=[-1,1])),tooltip=['Variabel 1','Variabel 2','Korelasi'])
text=alt.Chart(cm).mark_text().encode(x='Variabel 1:N',y='Variabel 2:N',text=alt.Text('Korelasi:Q',format='.3f'))
st.altair_chart((heat+text).properties(height=300),use_container_width=True)

st.subheader('Insight otomatis')
if len(f):
    low=f.dropna(subset=['TPT']).sort_values('TPT').head(1)
    best_rls=f.dropna(subset=['RLS']).sort_values('RLS',ascending=False).head(1)
    best_hls=f.dropna(subset=['HLS']).sort_values('HLS',ascending=False).head(1)
    insights=[]
    if len(maxrow): insights.append(f"TPT tertinggi {year} terdapat di {maxrow.iloc[0]['Nama Kabupaten/Kota']} ({maxrow.iloc[0].TPT:.2f}%).")
    if len(low): insights.append(f"TPT terendah terdapat di {low.iloc[0]['Nama Kabupaten/Kota']} ({low.iloc[0].TPT:.2f}%).")
    if len(best_rls): insights.append(f"RLS tertinggi adalah {best_rls.iloc[0]['Nama Kabupaten/Kota']} ({best_rls.iloc[0].RLS:.2f} tahun).")
    if len(best_hls): insights.append(f"HLS tertinggi adalah {best_hls.iloc[0]['Nama Kabupaten/Kota']} ({best_hls.iloc[0].HLS:.2f} tahun).")
    if delta is not None: insights.append(f"Rata-rata TPT berubah {delta:+.2f} poin persentase dibanding {year-1}.")
    st.markdown('<div class="note">'+'<br>'.join('• '+x for x in insights)+'</div>',unsafe_allow_html=True)

st.subheader('Data detail')
st.dataframe(f[['Tahun','Nama Kabupaten/Kota','TPT','RLS','HLS']].sort_values('Nama Kabupaten/Kota'),use_container_width=True,hide_index=True)
st.download_button('Download data terfilter (CSV)',f[['Tahun','Nama Kabupaten/Kota','TPT','RLS','HLS']].to_csv(index=False).encode(),'data_dashboard_ntb.csv','text/csv')
