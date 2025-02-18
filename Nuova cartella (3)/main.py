#main
import script # ✅ Per garantire la creazione di nuove logiche prima del trading
import bridge_module  # ✅ Per garantire il corretto caricamento dei moduli prima dell'esecuzione
import pandas as pd
import json
import os
import trading_environment
from data_loader import load_config
from dashboard import app, server
from data_handler import get_client, get_pairs, get_historical_data
from indicators import TradingIndicators
from portfolio_optimization import PortfolioOptimization
from ai_model import AIModel

script.generate_new_logic()
bridge_module.load_custom_modules()

# 📌 Percorso di configurazione API
CONFIG_PATH = "config.json"

def execute_trading_strategy():
    # Caricamento della configurazione
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError("❌ Configurazione API non trovata. Verifica il file config.json.")
    
    with open(CONFIG_PATH, "r") as file:
        config = json.load(file)

    # Creazione dei client API per Danny e Giuseppe
    client_danny = get_client(config['danny']['api_key'], config['danny']['api_secret'])
    client_giuseppe = get_client(config['giuseppe']['api_key'], config['giuseppe']['api_secret'])

    # Verifica se i client sono stati creati correttamente
    if not client_danny or not client_giuseppe:
        print("❌ Errore nella creazione dei client. Verifica le credenziali API.")
        return

    # Recupero delle coppie di trading
    pairs_danny = get_pairs(client_danny)
    pairs_giuseppe = get_pairs(client_giuseppe)

    if not pairs_danny or not pairs_giuseppe:
        print("❌ Errore: Nessuna coppia di trading disponibile.")
        return

    # Recupero e elaborazione dei dati storici
    data_danny = process_historical_data(client_danny, pairs_danny[0], "Danny")
    data_giuseppe = process_historical_data(client_giuseppe, pairs_giuseppe[0], "Giuseppe")

    if data_danny is None or data_giuseppe is None:
        return  # Errore nei dati, esce dalla funzione

    # Creazione e addestramento dei modelli AI
    ai_model_danny = train_ai_model(data_danny, "Danny")
    ai_model_giuseppe = train_ai_model(data_giuseppe, "Giuseppe")

    # Predizioni con AI
    predictions_danny = ai_model_danny.predict(data_danny['close'].values[-10:].reshape(-1, 10, 1))
    predictions_giuseppe = ai_model_giuseppe.predict(data_giuseppe['close'].values[-10:].reshape(-1, 10, 1))

    # Esecuzione delle strategie di trading
    check_trading_signal(data_danny, predictions_danny, client_danny, pairs_danny[0], "Danny")
    check_trading_signal(data_giuseppe, predictions_giuseppe, client_giuseppe, pairs_giuseppe[0], "Giuseppe")

    # Ottimizzazione del portafoglio
    optimize_portfolio(data_danny, "Danny")
    optimize_portfolio(data_giuseppe, "Giuseppe")


def process_historical_data(client, pair, trader_name):
    """Recupera e elabora i dati storici per il trader specificato."""
    print(f"📥 Recupero dati storici per {trader_name}...")
    data = get_historical_data(client, pair)
    
    if data.empty:
        print(f"❌ Errore: i dati storici per {trader_name} sono vuoti.")
        return None

    print(f"📊 Calcolo indicatori tecnici per {trader_name}...")
    data = TradingIndicators.calculate_indicators(data)
    data = TradingIndicators.generate_signals(data)
    return data


def train_ai_model(data, trader_name):
    """Addestra un modello AI per il trader specificato."""
    print(f"🤖 Addestramento AI per {trader_name}...")
    ai_model = AIModel(input_shape=(10, 1))
    
    X_train = data['close'].values[:-10].reshape(-1, 10, 1)
    y_train = data['close'].values[10:]
    
    ai_model.train(X_train=X_train, y_train=y_train, epochs=10)
    return ai_model


def check_trading_signal(data, predictions, client, pair, trader_name):
    """Esegue operazioni di trading basate sui segnali AI."""
    if data['Buy_Signal'].iloc[-1] and predictions[0] > data['close'].iloc[-1]:
        print(f"✅ {trader_name} sta acquistando {pair} con supporto AI.")
        try:
            client.create_order(symbol=pair, side='BUY', type='MARKET', quantity=1)
        except Exception as e:
            print(f"❌ Errore nell'ordine di acquisto per {trader_name}: {e}")
    
    elif data['Sell_Signal'].iloc[-1] and predictions[0] < data['close'].iloc[-1]:
        print(f"🚀 {trader_name} sta vendendo {pair} con supporto AI.")
        try:
            client.create_order(symbol=pair, side='SELL', type='MARKET', quantity=1)
        except Exception as e:
            print(f"❌ Errore nell'ordine di vendita per {trader_name}: {e}")


def optimize_portfolio(data, trader_name):
    """Ottimizza il portafoglio di investimento per un trader specifico."""
    print(f"📊 Ottimizzazione del portafoglio per {trader_name}...")
    
    returns = data['close'].pct_change().dropna()
    cov_matrix = data[['RSI', 'SMA', 'EMA']].cov()

    portfolio = PortfolioOptimization(returns, cov_matrix)
    optimal_weights = portfolio.optimize_portfolio()

    print(f"📈 Pesi ottimali del portafoglio per {trader_name}: {optimal_weights}")


if __name__ == "__main__":
    execute_trading_strategy()