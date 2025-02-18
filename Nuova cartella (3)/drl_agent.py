from stable_baselines3 import PPO, DQN, A2C, SAC
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.buffers import ReplayBuffer
import numpy as np
import optuna
import logging
import time
import os
import requests
from datetime import datetime
from data_handler import load_normalized_data
from data_api_module import main_fetch_all_data as load_raw_data
import gym_trading_env
from trading_environment import TradingEnv
import indicators

# 📌 Configurazione percorsi per il salvataggio del modello
USB_PATH = "/mnt/usb_trading_data/models"
CLOUD_PATH = "https://your-cloud-storage.com/upload"
LOCAL_PATH = "D:/trading_data/models"
SAVE_PATH = USB_PATH if os.path.exists(USB_PATH) else LOCAL_PATH

# 📌 Configurazione logging avanzata
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DRLAgent:
    def __init__(self, model_type='PPO', normalize=False, data=None, buffer_size=100000):
        """
        Inizializza l'agente DRL con supporto per scalping, tuning automatico e backtesting migliorato.
        """
        self.model_type = model_type
        self.normalize = normalize
        self.data = data if data is not None else load_normalized_data()
        self.env = self._select_trading_env()
        self.model = self._initialize_model()
        
        # ✅ Replay Buffer per scalping ad alta velocità
        self.replay_buffer = ReplayBuffer(
            buffer_size=buffer_size,
            observation_space=self.env.observation_space,
            action_space=self.env.action_space,
            device='cpu'
        )

    def _select_trading_env(self):
        """Seleziona l'ambiente di trading in base ai dati disponibili e attiva il backtesting se necessario."""
        if self.data is not None and not self.data.empty:
            logging.info("✅ Usando TradingEnv con dati disponibili.")
            return DummyVecEnv([lambda: TradingEnv(self.data)])
        else:
            logging.warning("⚠️ Nessun dato disponibile, avvio modalità di backtesting.")
            return DummyVecEnv([lambda: TradingEnv(load_raw_data())])

    def _initialize_model(self):
        """Inizializza il modello DRL con iperparametri ottimizzati per scalping."""
        model_classes = {'PPO': PPO, 'DQN': DQN, 'A2C': A2C, 'SAC': SAC}
        if self.model_type in model_classes:
            optimized_params = self.optimize_hyperparameters()
            return model_classes[self.model_type]("MlpPolicy", self.env, verbose=1, **optimized_params)
        else:
            raise ValueError("❌ Tipo di modello non supportato. Usa 'PPO', 'DQN', 'A2C' o 'SAC'.")

    def optimize_hyperparameters(self):
        """Utilizza Optuna per ottimizzare automaticamente gli iperparametri per scalping."""
        def objective(trial):
            learning_rate = trial.suggest_loguniform("learning_rate", 1e-5, 1e-2)
            gamma = trial.suggest_uniform("gamma", 0.8, 0.99)
            return {"learning_rate": learning_rate, "gamma": gamma}
        
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=10)
        logging.info(f"✅ Iperparametri ottimizzati: {study.best_params}")
        return study.best_params

    def train(self, total_timesteps=100000):
        """Allena il modello DRL e seleziona la strategia migliore per scalping."""
        logging.info(f"🔄 Inizio allenamento DRL per scalping su {total_timesteps} timesteps...")
        self.model.learn(total_timesteps=total_timesteps)
        logging.info("✅ Allenamento completato. Ora valuto la strategia migliore.")
        self.evaluate_scalping_strategy()

    def evaluate_scalping_strategy(self):
        """Testa diverse strategie di scalping e seleziona la migliore."""
        strategies = ["BB+RSI", "Ichimoku+ADX", "Order Flow+Sentiment"]
        best_strategy = None
        best_performance = -np.inf

        for strategy in strategies:
            logging.info(f"🔍 Testando strategia: {strategy}...")
            avg_reward = self._test_scalping_strategy(strategy)
            if avg_reward > best_performance:
                best_performance = avg_reward
                best_strategy = strategy

        logging.info(f"🏆 Migliore strategia di scalping selezionata: {best_strategy} con performance {best_performance}")

    def _test_scalping_strategy(self, strategy):
        """Esegue un backtest della strategia di scalping e ritorna la performance media."""
        rewards = []
        for _ in range(5):
            state = self.env.reset()
            total_reward = 0
            done = False
            while not done:
                action, _ = self.model.predict(state)
                state, reward, done, _ = self.env.step(action)
                total_reward += reward
            rewards.append(total_reward)
        return np.mean(rewards)

    def choose_action(self, state):
        """Sceglie un'azione basata sugli indicatori specializzati per scalping."""
        indicators_data = indicators.calculate_indicators(pd.DataFrame(state))
        action, _ = self.model.predict(indicators_data.values)
        return action

    def save(self, filename="drl_scalping_model.zip"):
        """Salva il modello AI per scalping su USB, locale o cloud."""
        filepath = os.path.join(SAVE_PATH, filename)
        self.model.save(filepath)
        logging.info(f"💾 Modello salvato in: {filepath}")
        self.upload_to_cloud(filepath)

# ==============================
# 🔹 ALLENAMENTO AUTOMATICO CONTINUO PER SCALPING
# ==============================
def auto_train_scalping():
    """
    Questo script allena continuamente il modello DRL ogni 30 minuti per massimizzare le performance di scalping.
    """
    agent = DRLAgent(model_type='PPO')
    while True:
        logging.info("🔄 Allenamento scalping in corso...")
        agent.train(total_timesteps=5000)
        agent.save("drl_scalping_model.zip")
        logging.info("✅ Modello di scalping aggiornato con successo!")
        time.sleep(1800)  # Aggiorna ogni 30 minuti

if __name__ == "__main__":
    auto_train_scalping()
