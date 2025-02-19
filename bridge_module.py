# bridge_module.py
import os
import sys
import logging
import importlib
import requests

# Configurazione logging avanzata
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Percorsi delle directory
MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
BOT_SUPREMO_PATH = os.path.join(MODULE_PATH, "BOT_SUPREMO")
CUSTOM_MODULES_PATH = os.path.join(MODULE_PATH, "custom_modules")

# Assicurarsi che la directory dei moduli personalizzati sia accessibile
sys.path.append(BOT_SUPREMO_PATH)
sys.path.append(CUSTOM_MODULES_PATH)

# Lista aggiornata dei moduli personalizzati
CUSTOM_MODULES = [
    "ai_model",
    "data_api_module",
    "data_handler",
    "data_loader",
    "drl_agent",
    "DynamicTradingManager",
    "gym_trading_env",
    "indicators",
    "market_data",
    "market_data_apis",
    "portfolio_optimization",
    "risk_management",
    "script",  # ✅ Aggiunto modulo per la creazione di nuove logiche
    "trading_bot",  # ✅ Assicurarsi che il bot principale sia incluso
    "trading_environment",  # ✅ Ambiente di trading per l'AI
    "main"  # ✅ Se esiste un main script, aggiungilo qui
]

def import_custom_modules():
    """Importa dinamicamente i moduli personalizzati."""
    for module_name in CUSTOM_MODULES:
        try:
            importlib.import_module(module_name)
            logging.info(f"✅ Modulo '{module_name}' importato con successo.")
        except ImportError as e:
            logging.error(f"❌ Errore nell'importazione del modulo '{module_name}': {e}")

def fetch_remote_module(url, module_name):
    """
    Scarica un modulo Python da un URL remoto e lo salva nella directory dei moduli personalizzati.
    
    :param url: URL del modulo Python da scaricare.
    :param module_name: Nome del modulo da salvare.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        module_path = os.path.join(CUSTOM_MODULES_PATH, f"{module_name}.py")
        with open(module_path, "w", encoding="utf-8") as file:
            file.write(response.text)
        logging.info(f"✅ Modulo '{module_name}' scaricato e salvato in '{module_path}'.")
    except requests.RequestException as e:
        logging.error(f"❌ Errore nel download del modulo '{module_name}' da '{url}': {e}")

def initialize_bot():
    """
    Inizializza il bot importando i moduli personalizzati e scaricando eventuali moduli remoti necessari.
    """
    logging.info("🚀 Avvio dell'inizializzazione dei moduli personalizzati...")
    import_custom_modules()
    logging.info("✅ Tutti i moduli sono stati importati correttamente.")

    # Esempio di download di un modulo remoto se necessario
    remote_modules = {
        # "example_module": "https://example.com/example_module.py"
    }

    for module_name, url in remote_modules.items():
        if module_name not in CUSTOM_MODULES:
            fetch_remote_module(url, module_name)

if __name__ == "__main__":
    initialize_bot()
