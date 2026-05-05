from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import pandas as pd
from prophet import Prophet
import os
import json

class tool_prediksi_input(BaseModel):
    file_path: str = Field(..., description="Path to the Excel file for sales prediction")

class tool_prediksi(BaseTool):
    name: str = "Tool prediksi penjualan"
    description: str = (
        "Memprediksi penjualan berdasarkan data historis di file Excel menggunakan algoritma Prophet. "
        "Menerima path file Excel sebagai input. Kolom yang dibutuhkan: PRODUCT, TANGGAL, TARGET."
    )
    args_schema: Type[BaseModel] = tool_prediksi_input

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File tidak ditemukan di path '{file_path}'"})

        try:
            df = pd.read_excel(file_path, sheet_name=0)
            required_cols = {'PRODUCT', 'TANGGAL', 'TARGET'}
            if not required_cols.issubset(set(df.columns)):
                return json.dumps({"error": f"Kolom tidak lengkap. Dibutuhkan: {required_cols}. Ditemukan: {list(df.columns)}"})

            df_prophet = df[['TANGGAL', 'TARGET']].copy()
            df_prophet.rename(columns={'TANGGAL': 'ds', 'TARGET': 'y'}, inplace=True)
            df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])
            
            # If there are duplicate dates (e.g., multiple products), aggregate them by sum
            df_prophet = df_prophet.groupby('ds')['y'].sum().reset_index()

            # Initialize and fit model
            # Turn off seasonality if data is too small (e.g., < 14 days)
            if len(df_prophet) < 14:
                model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
            else:
                model = Prophet(yearly_seasonality=False, daily_seasonality=False)
                
            model.fit(df_prophet)

            # Predict next 5 days
            future = model.make_future_dataframe(periods=5)
            forecast = model.predict(future)

            # Extract the future predictions (tail 5)
            predictions = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(5)
            
            # Convert 'ds' to string for JSON serialization
            predictions['ds'] = predictions['ds'].dt.strftime('%Y-%m-%d')
            
            result = {
                "status": "success",
                "message": "Prediksi berhasil dijalankan",
                "data": predictions.to_dict(orient='records')
            }
            return json.dumps(result)

        except Exception as e:
            return json.dumps({"error": f"Terjadi kesalahan saat memproses data: {str(e)}"})
