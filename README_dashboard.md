# Dashboard Pendidikan & Pengangguran NTB

## File yang harus ada di repository GitHub
- `app.py`
- `requirements.txt`
- `data_hls.json`
- `data_tpt.json`
- `data_rls.json`

## Deploy ke Streamlit Community Cloud
1. Buat repository GitHub baru/public.
2. Upload kelima file di atas ke root repository.
3. Buka Streamlit Community Cloud dan pilih **Create app**.
4. Pilih repository, branch `main`, dan main file `app.py`.
5. Klik **Deploy**.

Dashboard menggunakan Streamlit + Pandas + Altair sehingga tidak membutuhkan matplotlib atau plotly.
