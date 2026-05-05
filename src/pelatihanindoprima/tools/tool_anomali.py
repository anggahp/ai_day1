from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import pandas as pd
from sklearn.ensemble import IsolationForest
import os

class tool_anomali_input(BaseModel):
    file_path: str = Field(..., description="Path to the Excel file for anomaly detection")

class tool_anomali(BaseTool):
    name: str = "Tool deteksi anomali"
    description: str = (
        "Mendeteksi anomali pada data Excel menggunakan algoritma Isolation Forest. "
        "Menerima path file Excel sebagai input."
    )
    args_schema: Type[BaseModel] = tool_anomali_input

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"Error: File tidak ditemukan di path '{file_path}'"

        try:
            # Baca excel
            df = pd.read_excel(file_path, sheet_name=0)
            
            # Asumsi kolom pertama adalah index/waktu yang perlu diolah
            # Berdasarkan kode user sebelumnya:
            df_original = df.copy()
            
            # Preprocessing sederhana berdasarkan snippet user
            # df = df.iloc[:,1:] # Hapus kolom pertama jika itu ID/Time
            
            # Jika ada kolom 'time', konversi ke numeric
            if 'time' in df.columns:
                df['day_number'] = (pd.to_datetime(df['time']) - pd.Timestamp('2000-01-01')).dt.days
                df = df.drop(columns=['time'])

            # Konversi kolom object ke numeric jika memungkinkan
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df_clean = df.dropna()
            
            if df_clean.empty:
                return "Error: Tidak ada data valid (numeric) yang bisa dianalisis setelah pembersihan."

            # Deteksi Anomali
            iso_forest = IsolationForest(
                contamination=0.05,
                random_state=40,
                n_estimators=100
            )
            
            # Fit dan Predict
            df_clean = df_clean.copy()
            df_clean['anomali'] = iso_forest.fit_predict(df_clean)
            
            anomali_count = (df_clean['anomali'] == -1).sum()
            total_data = len(df_clean)
            
            # Ambil contoh data anomali
            anomali_samples = df_clean[df_clean['anomali'] == -1].head(10)
            
            result = f"--- Hasil Deteksi Anomali ---\n"
            result += f"Total Data dianalisis: {total_data}\n"
            result += f"Jumlah Anomali ditemukan: {anomali_count}\n"
            result += f"Persentase Anomali: {(anomali_count/total_data)*100:.2f}%\n\n"
            
            if anomali_count > 0:
                result += "Contoh Data Anomali (10 data pertama):\n"
                result += anomali_samples.to_string()
            else:
                result += "Tidak ditemukan anomali pada data."
                
            return result

        except Exception as e:
            return f"Error saat mendeteksi anomali: {str(e)}"
