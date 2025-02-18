#indicators
import talib
import pandas as pd
import numpy as np
import logging
import requests

# 📌 Configurazione logging avanzata
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SENTIMENT_API_URL = "https://your-sentiment-api.com/analyze"

class TradingIndicators:
    @staticmethod
    def calculate_indicators(df):
        """Calcola una serie di indicatori tecnici avanzati per scalping e trading su timeframe ultra-rapidi."""
        if len(df) < 30:
            logging.warning("⚠️ Non ci sono abbastanza dati per calcolare tutti gli indicatori.")
            return df

        # ✅ Indicatori di tendenza
        df['SMA'] = talib.SMA(df['close'], timeperiod=5)  # Scalping: SMA su 5 periodi
        df['EMA'] = talib.EMA(df['close'], timeperiod=5)
        df['TEMA'] = talib.TEMA(df['close'], timeperiod=5)

        # ✅ Indicatori di volatilità e breakout per scalping
        upper, middle, lower = talib.BBANDS(df['close'], timeperiod=5)
        df['BB_upper'], df['BB_middle'], df['BB_lower'] = upper, middle, lower

        df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=5)  # True Range ridotto per scalping
        df['Volatility_Index'] = df['ATR'] / df['close']  # Volatilità percentuale

        # ✅ Volume Velocity Analysis - Analisi della velocità dei volumi
        df['Volume_Change'] = df['volume'].pct_change()
        df['Volume_Momentum'] = df['Volume_Change'].rolling(window=3).sum()  # Somma variazioni degli ultimi 3 periodi

        # ✅ Identificazione dei Breakout
        df['Breakout'] = (df['close'] > df['BB_upper']) & (df['Volume_Momentum'] > 0)

        # ✅ Indicatori di forza della tendenza per scalping
        df['ADX'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=5)
        df['+DI'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=5)
        df['-DI'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=5)

        # ✅ RSI modificato per scalping (timeframe più veloce)
        df['RSI'] = talib.RSI(df['close'], timeperiod=7)  

        # ✅ Ichimoku Cloud modificato per scalping
        nine_high = df['high'].rolling(window=9).max()
        nine_low = df['low'].rolling(window=9).min()
        df['conversion_line'] = (nine_high + nine_low) / 2
        twenty_six_high = df['high'].rolling(window=26).max()
        twenty_six_low = df['low'].rolling(window=26).min()
        df['base_line'] = (twenty_six_high + twenty_six_low) / 2
        df['leading_span_a'] = ((df['conversion_line'] + df['base_line']) / 2).shift(26)
        fifty_two_high = df['high'].rolling(window=52).max()
        fifty_two_low = df['low'].rolling(window=52).min()
        df['leading_span_b'] = ((fifty_two_high + fifty_two_low) / 2).shift(26)

        # ✅ Order Flow Analysis (previsione movimenti dei market maker)
        df['Order_Flow_Score'] = TradingIndicators.get_order_flow_score(df['close'], df['volume'])

        # ✅ Sentiment Analysis
        df['Sentiment_Score'] = TradingIndicators.get_sentiment_score(df['close'])

        # ✅ Pulizia dei dati
        df.fillna(0, inplace=True)

        return df

    @staticmethod
    def get_sentiment_score(price_series):
        """Ottiene il sentiment del mercato basato su news e social media."""
        try:
            response = requests.post(SENTIMENT_API_URL, json={"prices": price_series.tolist()})
            if response.status_code == 200:
                return response.json().get("sentiment_score", 0)
        except Exception as e:
            logging.error(f"⚠️ Errore nel recupero del sentiment di mercato: {e}")
        return 0  

    @staticmethod
    def get_order_flow_score(price_series, volume_series):
        """Analizza il flusso degli ordini per prevedere i movimenti di mercato."""
        try:
            return (price_series.pct_change() * volume_series.pct_change()).rolling(window=3).sum()
        except Exception as e:
            logging.error(f"⚠️ Errore nel calcolo dell'Order Flow Score: {e}")
        return 0  

    @staticmethod
    def generate_signals(df):
        """Genera segnali di acquisto e vendita basati sugli indicatori di scalping."""
        df['Buy_Signal'] = (df['close'] < df['BB_lower']) & (df['RSI'] < 30) & (df['ADX'] > 20) & (df['Sentiment_Score'] > 0) & (df['Order_Flow_Score'] > 0)
        df['Sell_Signal'] = (df['close'] > df['BB_upper']) & (df['RSI'] > 70) & (df['ADX'] > 20) & (df['Sentiment_Score'] < 0) & (df['Order_Flow_Score'] < 0)

        return df