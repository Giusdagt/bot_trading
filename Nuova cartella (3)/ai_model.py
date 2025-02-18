#ai_model
import os
import time
import numpy as np
import pandas as pd
from datetime import datetime
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
import indicators
import data_handler
import drl_agent
import gym_trading_env
import risk_management
import logging

# 📌 Configurazione logging per monitorare AI in tempo reale
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📌 Configurazione percorsi per archiviazione USB e locale
MODEL_DIR = "/mnt/usb_trading_data/models" if os.path.exists("/mnt/usb_trading_data") else "D:/trading_data/models"
MODEL_FILE = "best_model.h5"
REALTIME_MODEL_FILE = "realtime_model.h5"

class AIModel:
    def __init__(self, input_shape, output_size):
        self.input_shape = (input_shape, 1)
        self.output_size = output_size
        self.model = self._build_model()
        self.xgb_model = xgb.XGBRegressor(objective='reg:squarederror')
        self.scaler = MinMaxScaler(feature_range=(0, 1))
    
    def _build_model(self):
        """Crea il modello AI combinato LSTM + XGBoost"""
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=self.input_shape),
            Dropout(0.2),
            LSTM(128, return_sequences=False),
            Dropout(0.2),
            Dense(self.output_size)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def preprocess_data(self, df):
        """Prepara e normalizza i dati per il training AI"""
        df = indicators.TradingIndicators.calculate_indicators(df)
        df = df.select_dtypes(include=[np.number]).fillna(df.median())
        df_scaled = self.scaler.fit_transform(df)
        return np.expand_dims(df_scaled, axis=-1) if df_scaled.ndim == 2 else df_scaled

    def train(self, X_train, y_train, epochs=10, batch_size=32):
        """Allena il modello AI"""
        logging.info("🔄 Avvio training AI...")
        X_train_scaled = self.preprocess_data(X_train)
        self.model.fit(X_train_scaled, y_train, epochs=epochs, batch_size=batch_size,
                       callbacks=[EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)])
        self.xgb_model.fit(X_train_scaled[:, :, 0], y_train)

    def predict(self, X_input):
        """Prevede i prezzi futuri basandosi su AI combinata"""
        lstm_pred = self.model.predict(self.preprocess_data(X_input))
        xgb_pred = self.xgb_model.predict(self.preprocess_data(X_input)[:, :, 0])
        return (lstm_pred + xgb_pred) / 2

    def save(self, filename):
        """Salva il modello AI"""
        filepath = os.path.join(MODEL_DIR, filename)
        self.model.save(filepath)
        logging.info(f"✅ Modello AI salvato in: {filepath}")

    def load(self, filename):
        """Carica il modello AI"""
        filepath = os.path.join(MODEL_DIR, filename)
        if os.path.exists(filepath):
            self.model = load_model(filepath)
            logging.info(f"✅ Modello AI caricato da: {filepath}")
        else:
            logging.warning(f"⚠️ Modello AI non trovato: {filepath}, eseguo nuovo training.")

def train_ai_in_realtime():
    """Allenamento AI automatico ogni 30 minuti"""
    while True:
        logging.info("🔄 Aggiornamento AI con nuovi dati...")
        data = data_handler.load_normalized_data()

        if data.empty:
            logging.warning("⚠ Nessun dato disponibile, provo a scaricare nuovi dati...")
            data = data_handler.fetch_and_prepare_data()

        if not data.empty:
            X_train = data.drop(columns=['close']).values
            y_train = data['close'].values

            ai = AIModel(input_shape=X_train.shape[1], output_size=1)
            model_path = os.path.join(MODEL_DIR, REALTIME_MODEL_FILE)
            
            if os.path.exists(model_path):
                ai.load(model_path)

            ai.train(X_train, y_train, epochs=10)
            ai.save(model_path)
            logging.info("✅ AI aggiornata con successo!")
        
        time.sleep(1800)  # Aggiorna ogni 30 minuti

if __name__ == "__main__":
    train_ai_in_realtime()
